"""OpenAI / Anthropic 兼容的对话补全（真正的中继实现）。

- POST /v1/chat/completions : OpenAI 协议入站
- POST /v1/messages         : Anthropic 协议入站
- GET  /v1/models           : 社区池当前可用的模型标识

鉴权：Authorization: Bearer ah-xxxx（Anthropic 入站也接受 x-api-key）。
路由：model=auto 时选优先级最高的社区 key；填具体模型名时先按上游 model 名匹配，
      全部匹配不上，再按上传者给 key 起的 name 匹配。
"""
from route.app import *
import database
import protocol
import Relay


def _APIKey():
	Header = flask.request.headers.get("Authorization") or ""
	if Header.lower().startswith("bearer "):
		return Header[7:].strip()
	Key = flask.request.headers.get("x-api-key")
	return Key.strip() if Key else None


def _Error(Message, Status, Type="invalid_request_error"):
	return flask.jsonify({"error": {"message": Message, "type": Type}}), Status


def _Chat(Protocol):
	APIKey = _APIKey()
	if not APIKey:
		return _Error("缺少 API Key：请在 Authorization 头里带上 Bearer ah-xxxx", 401)
	Caller = database.key.Resolve.ByAPIKey(APIKey)
	if Caller is None:
		return _Error("API Key 无效", 401)
	if not Caller.get("enabled", True):
		return _Error("该 API Key 已被停用", 401)
	Body = flask.request.get_json(silent=True)
	if not isinstance(Body, dict):
		return _Error("请求体必须是 JSON", 400)
	Adapter = protocol.Get(Protocol)
	try:
		Request = Adapter.ParseRequest(Body)
	except (KeyError, TypeError, ValueError) as Error:
		return _Error(f"请求体解析失败：{Error}", 400)
	if not Request.get("messages"):
		return _Error("messages 不能为空", 400)
	Stream = bool(Request.get("stream"))
	try:
		Result, Row = Relay.Call(Request, Request.get("model"), Stream)
	except Relay.NoKeyError as Error:
		return _Error(str(Error), 503, "no_available_key")
	except Relay.UpstreamError as Error:
		return _Error(str(Error), 502, "upstream_error")
	Headers = {"X-AIHub-Key": str(Row["id"]), "X-AIHub-Model": str(Row["model"])}
	if Stream:
		Headers["Cache-Control"] = "no-cache"
		Headers["X-Accel-Buffering"] = "no"
		return flask.Response(Adapter.RenderStream(Result, Request), mimetype="text/event-stream", headers=Headers)
	Payload = flask.json.dumps(Adapter.RenderResponse(Result, Request), ensure_ascii=False)
	return flask.Response(Payload, mimetype="application/json", headers=Headers)


@app.route("/v1/chat/completions", methods=["POST"])
def ChatCompletions():
	"""OpenAI 协议入站"""
	return _Chat("openai")


@app.route("/v1/messages", methods=["POST"])
def Messages():
	"""Anthropic 协议入站"""
	return _Chat("anthropic")


@app.route("/v1/models", methods=["GET"])
def Models():
	"""社区池当前可用的模型标识（含 auto）"""
	if database.key.Resolve.ByAPIKey(_APIKey() or "") is None:
		return _Error("API Key 无效", 401)
	Data = [{"id": Name, "object": "model", "created": 0, "owned_by": "community"} for Name in Relay.Models()]
	return flask.jsonify({"object": "list", "data": Data})

