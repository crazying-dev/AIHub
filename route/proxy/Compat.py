"""客户端兼容层：跨域（CORS）、结尾斜杠容错、错误响应 JSON 化。

中继面是要被各种客户端直连的（OpenAI / Anthropic / Gemini / Ollama 的 SDK，
以及跑在浏览器里的 Web 界面），它们常见的三个坑：

1. 浏览器里的 Web 客户端是跨域调用，会先发 OPTIONS 预检；
   响应里没有 Access-Control-Allow-* 头，浏览器会直接把请求拦下来。
2. base_url 末尾多一个斜杠（https://ai.yjlt.top/v1/ 再拼 /chat/completions
   就变成 /v1/chat/completions/），Flask 默认的 strict_slashes 会判成 405。
3. 方法用错（例如 POST /v1/models）时，Flask 默认回一坨 HTML 错误页，
   客户端解析不了，界面上只能显示「未知错误 / Method Not Allowed」。

这里统一兜住这三种情况，且只在**中继面**生效：
/v1/*、/v1beta/*、Ollama 的 /api/<动作>。
管理面 /api/*（sign / key / community / private，走 Cookie 鉴权）绝不参与跨域，
否则等于把账号接口开放给任意第三方页面。
"""
from route.app import *
from route.proxy.Common import AnthropicError, Failure, GeminiError, OllamaError, OpenAIError

# Ollama 客户端会打的动作；只有这些 /api/<动作> 算中继面（其余 /api/* 是走 Cookie 的管理接口）
OLLAMA_ACTIONS = {
	"chat",
	"generate",
	"embed",
	"embeddings",
	"tags",
	"ps",
	"version",
	"show",
	"pull",
	"push",
	"create",
	"delete",
	"copy",
	"blobs",
	"head",
}

# 允许的跨域方法与请求头；请求头优先回显预检里声明的那一份，回显不到再给这份默认值
CORS_METHODS = "GET, POST, OPTIONS"
CORS_HEADERS = "Authorization, Content-Type, x-api-key, x-goog-api-key, anthropic-version, anthropic-beta, x-stainless-*, api-key"
CORS_MAX_AGE = "86400"
# 浏览器默认只让页面读到少数几个标准响应头，命中信息要显式暴露出去
CORS_EXPOSE = "X-AIHub-Key, X-AIHub-Model"

# 路径 -> 错误体形状。形状复用各协议自己的渲染器，保证和正常报错一致
_RENDERERS = {
	"openai": OpenAIError,
	"anthropic": AnthropicError,
	"ollama": OllamaError,
	"gemini": GeminiError,
}


def Normalized(Path):
	"""把请求路径规整成 /a/b 的形式（丢掉多余斜杠与结尾斜杠），方便前缀判断。"""
	Parts = [Part for Part in str(Path or "").split("/") if Part]
	return "/" + "/".join(Parts)


def IsRelay(Path):
	"""该路径是否属于对外开放的中继面。"""
	Text = Normalized(Path)
	if Text == "/v1" or Text.startswith("/v1/"):
		return True
	if Text == "/v1beta" or Text.startswith("/v1beta/"):
		return True
	Parts = Text.strip("/").split("/")
	return len(Parts) == 2 and Parts[0] == "api" and Parts[1] in OLLAMA_ACTIONS


def Protocol(Path):
	"""按路径判断是哪个客户端协议，用来决定错误体的形状。"""
	Text = Normalized(Path)
	if Text.startswith("/v1beta"):
		return "gemini"
	if Text.startswith("/v1/messages"):
		return "anthropic"
	if Text.startswith("/api/"):
		return "ollama"
	return "openai"


def FailureResponse(Message, Status, Path):
	"""按路径对应的协议渲染一条 JSON 错误，返回 (响应, 状态码)。"""
	Response, Code = _RENDERERS[Protocol(Path)](Failure(Message, Status))
	return Response, Code


@app.after_request
def Cors(Response):
	"""中继面统一补跨域响应头（普通请求与 OPTIONS 预检都会走到这里）。"""
	if not IsRelay(flask.request.path):
		return Response
	Response.headers.setdefault("Access-Control-Allow-Origin", "*")
	Response.headers.setdefault("Access-Control-Allow-Methods", CORS_METHODS)
	Requested = flask.request.headers.get("Access-Control-Request-Headers")
	Response.headers.setdefault("Access-Control-Allow-Headers", Requested or CORS_HEADERS)
	Response.headers.setdefault("Access-Control-Max-Age", CORS_MAX_AGE)
	Response.headers.setdefault("Access-Control-Expose-Headers", CORS_EXPOSE)
	return Response


@app.errorhandler(404)
def RelayNotFound(Error):
	"""中继面找不到端点：给 JSON，而不是让人看不懂的 HTML。"""
	if not IsRelay(flask.request.path):
		return Error
	return FailureResponse("端点不存在：" + Normalized(flask.request.path), 404, flask.request.path)


@app.errorhandler(405)
def RelayMethodNotAllowed(Error):
	"""中继面方法用错：给 JSON，并把 Allow 头带上，告诉客户端该用什么方法。"""
	if not IsRelay(flask.request.path):
		return Error
	Allowed = Error.get_response().headers.get("Allow") or ""
	Response, Code = FailureResponse(
		"该端点不支持 " + flask.request.method + " 方法，支持：" + (Allowed or "GET、POST"),
		405,
		flask.request.path,
	)
	Response.headers["Allow"] = Allowed
	return Response, Code