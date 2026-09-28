"""协议适配层。

入站协议（调用方 -> AIHub，路由挂在 route/proxy/ 下）：
- openai    ：POST /v1/chat/completions、POST /v1/completions、POST /v1/embeddings、GET /v1/models
- anthropic ：POST /v1/messages、POST /v1/messages/count_tokens
- responses ：POST /v1/responses（OpenAI Responses API）
- ollama    ：POST /api/chat、POST /api/generate、GET /api/tags、GET /api/version
- gemini    ：POST /v1beta/models/{model}:generateContent | :streamGenerateContent | :countTokens、GET /v1beta/models

上游协议（AIHub -> 厂商，由 key 的 protocol 字段决定）：
- openai / anthropic / gemini

每个适配器按需实现：
	ParseRequest(Body) -> canonical request          # 入站解析
	RenderResponse(Response, Request) -> dict         # canonical -> 入站非流式响应
	RenderStream(Chunks, Request) -> Iterator[str]    # canonical 分片 -> 入站流式文本
	Call(Request, BaseURL, ApiKey, Model, Stream)     # canonical -> 上游（返回响应或分片生成器）

注意：这里不在模块顶层 import 各适配器（连带 SDK）。gemini 的 SDK 冷启动导入要上百秒，
一律走惰性导入，避免拖慢 Flask 启动。
"""
import importlib

# 上游协议：key 的 protocol 字段的可选值
_UPSTREAM_MODULES = {
	"openai": "protocol.openai",
	"anthropic": "protocol.anthropic",
	"gemini": "protocol.gemini",
}

# 入站协议：客户端可以直接对接的协议入口
_INBOUND_MODULES = {
	"openai": "protocol.openai",
	"anthropic": "protocol.anthropic",
	"responses": "protocol.responses",
	"ollama": "protocol.ollama",
	"gemini": "protocol.gemini",
}

# 用户上传 key 时可能填的协议名，统一归一到内部标识（只用于上游）
_ALIASES = {
	"openai": "openai",
	"oai": "openai",
	"openai-compatible": "openai",
	"openai_compatible": "openai",
	"compatible": "openai",
	"chat": "openai",
	"chat-completions": "openai",
	"chat_completions": "openai",
	"azure": "openai",
	"azure-openai": "openai",
	"gpt": "openai",
	"v1": "openai",
	"anthropic": "anthropic",
	"claude": "anthropic",
	"messages": "anthropic",
	"gemini": "gemini",
	"google": "gemini",
	"google-gemini": "gemini",
	"genai": "gemini",
	"google-ai": "gemini",
}

# 可以作为“入站协议”的（客户端协议入口）
INBOUND = ("openai", "anthropic", "responses", "ollama", "gemini")
# 可以作为“上游协议”的（即 key 的 protocol 字段支持的）
UPSTREAM = ("openai", "anthropic", "gemini")


def Normalize(Protocol):
	"""把用户填写的上游协议名归一到内部标识，认不出来返回 None。"""
	if not Protocol:
		return None
	return _ALIASES.get(str(Protocol).strip().lower())


def Get(Protocol):
	"""按上游协议名取适配器模块，不认识就抛 ValueError。"""
	Name = Normalize(Protocol)
	if Name is None:
		raise ValueError(f"不支持的协议：{Protocol}")
	return importlib.import_module(_UPSTREAM_MODULES[Name])


def Inbound(Protocol):
	"""按入站协议名取适配器模块，不认识就抛 ValueError。"""
	Name = str(Protocol or "").strip().lower()
	if Name not in _INBOUND_MODULES:
		raise ValueError(f"不支持的入站协议：{Protocol}")
	return importlib.import_module(_INBOUND_MODULES[Name])