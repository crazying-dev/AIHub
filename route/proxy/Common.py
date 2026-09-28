"""入站中继的公共部分：鉴权、错误形状、以及「canonical request -> 上游 -> 渲染」这条流水线。"""
import functools

from route.app import *
import database
import Relay
from route.api.Common import Text

# 公共库（社区池）的固定凭证：字面量，任何人都能用，不需要注册
PUBLIC_KEY = "ah-xxxx"


class Failure(Exception):
	"""入站错误：带 http 状态与错误类型，由各协议自己渲染成对应的错误体。"""

	def __init__(self, Message, Status=400, Type="invalid_request_error", Code=None):
		super().__init__(Message)
		self.Message = Message
		self.Status = Status
		self.Type = Type
		self.Code = Code


def Bearer():
	"""取 Authorization: Bearer <key>。"""
	Header = flask.request.headers.get("Authorization") or ""
	if Header.lower().startswith("bearer "):
		return Header[7:].strip() or None
	return None


def APIKey(AllowAnonymous=False):
	"""
	按优先级取调用凭证：Authorization: Bearer -> x-api-key -> x-goog-api-key -> ?key=
	AllowAnonymous 为真并且一个都没带时，退回公共库的固定凭证 ah-xxxx（Ollama 这类不带鉴权的客户端用）。
	"""
	Key = Text(
		Bearer()
		or flask.request.headers.get("x-api-key")
		or flask.request.headers.get("x-goog-api-key")
		or flask.request.args.get("key")
	)
	if not Key and AllowAnonymous:
		return PUBLIC_KEY
	return Key


def Authenticate(AllowAnonymous=False):
	"""取凭证并解析成调用方；失败抛 Failure。"""
	Caller = database.key.Resolve.ByAPIKey(APIKey(AllowAnonymous) or "")
	if Caller is None:
		raise Failure("API Key 无效：请在请求头带上 Bearer ah-xxxx（公共库）或你的个人密钥 ah-<id>", 401, "invalid_request_error", "invalid_api_key")
	if not Caller.get("enabled", True):
		raise Failure("该 API Key 已被停用", 401, "invalid_request_error", "invalid_api_key")
	return Caller


def Body():
	"""取 JSON 请求体，必须是对象（不看 Content-Type，兼容各种客户端）。"""
	Data = flask.request.get_json(force=True, silent=True)
	if not isinstance(Data, dict):
		raise Failure("请求体必须是 JSON 对象", 400)
	return Data


def Parse(Adapter, Data, Model=None, Stream=None, Parser="ParseRequest"):
	"""把请求体转成 canonical request；Model / Stream 用于覆盖 URL 里带的模型与流式标记。"""
	Handler = getattr(Adapter, Parser, None)
	if Handler is None:
		raise Failure(f"协议 {getattr(Adapter, 'NAME', '?')} 不支持 {Parser}", 400)
	try:
		Request = Handler(Data)
	except (KeyError, TypeError, ValueError) as Error:
		raise Failure(f"请求体解析失败：{Error}", 400)
	if Model:
		Request["model"] = Model
	if Stream is not None:
		Request["stream"] = bool(Stream)
	return Request


def NeedMessages(Request):
	"""大部分协议都要求至少有一条消息。"""
	if not Request.get("messages"):
		raise Failure("messages 不能为空", 400)
	return Request


def Run(Request, Caller):
	"""canonical request -> 上游，返回 (结果, 命中的候选)。"""
	try:
		return Relay.Call(Request, Request.get("model"), bool(Request.get("stream")), Caller)
	except Relay.NoKeyError as Error:
		raise Failure(str(Error), 503, "no_available_key", "no_available_key")
	except Relay.UpstreamError as Error:
		raise Failure(str(Error), 502, "upstream_error", "upstream_error")


def Headers(Row):
	"""把命中的上游 key 标在响应头里，方便排查。"""
	return {"X-AIHub-Key": str(Row["id"]), "X-AIHub-Model": str(Row["model"])}


def JSON(Payload, Extra=None):
	return flask.Response(flask.json.dumps(Payload, ensure_ascii=False), mimetype="application/json", headers=Extra or {})


def Respond(Caller, Adapter, Request, Render=None, StreamRender=None, StreamMimetype="text/event-stream"):
	"""跑完中继并按协议渲染：流式走 StreamRender（默认 Adapter.RenderStream），非流式走 Render。"""
	Result, Row = Run(Request, Caller)
	if Request.get("stream"):
		Renderer = StreamRender or Adapter.RenderStream
		Response = flask.Response(Renderer(Result, Request), mimetype=StreamMimetype, headers=Headers(Row))
		Response.headers["Cache-Control"] = "no-cache"
		Response.headers["X-Accel-Buffering"] = "no"
		return Response
	Renderer = Render or Adapter.RenderResponse
	return JSON(Renderer(Result, Request), Headers(Row))


def Guard(Render):
	"""装饰器：把 Failure 交给 Render 转成该协议的错误响应。"""
	def Wrapper(Handler):
		@functools.wraps(Handler)
		def Inner(*Args, **Kwargs):
			try:
				return Handler(*Args, **Kwargs)
			except Failure as Error:
				return Render(Error)
		return Inner
	return Wrapper


def OpenAIError(Error):
	"""OpenAI（含 Responses）风格的错误体。"""
	Payload = {"error": {"message": Error.Message, "type": Error.Type}}
	if Error.Code:
		Payload["error"]["code"] = Error.Code
	return flask.jsonify(Payload), Error.Status


def AnthropicError(Error):
	"""Anthropic 风格的错误体。"""
	if Error.Status == 401:
		Type = "authentication_error"
	elif Error.Status >= 500:
		Type = "api_error"
	else:
		Type = "invalid_request_error"
	return flask.jsonify({"type": "error", "error": {"type": Type, "message": Error.Message}}), Error.Status


def OllamaError(Error):
	"""Ollama 风格：错误就是一个字符串字段。"""
	return flask.jsonify({"error": Error.Message}), Error.Status


_GEMINI_STATUS = {
	400: "INVALID_ARGUMENT",
	401: "UNAUTHENTICATED",
	403: "PERMISSION_DENIED",
	404: "NOT_FOUND",
	429: "RESOURCE_EXHAUSTED",
	500: "INTERNAL",
	502: "INTERNAL",
	503: "UNAVAILABLE",
}


def GeminiError(Error):
	"""Gemini 风格的错误体。"""
	Status = _GEMINI_STATUS.get(Error.Status, "UNKNOWN")
	return flask.jsonify({"error": {"code": Error.Status, "message": Error.Message, "status": Status}}), Error.Status