"""协议适配层。

入站协议（调用方 -> AIHub）：
- openai    ：POST /v1/chat/completions
- anthropic ：POST /v1/messages
上游协议（AIHub -> 厂商，由社区 key 的 protocol 字段决定）：
- openai / anthropic / gemini

每个适配器统一实现：
	ParseRequest(Body) -> canonical request          # 入站解析
	RenderResponse(Response, Request) -> dict         # canonical -> 入站非流式响应
	RenderStream(Chunks, Request) -> Iterator[str]    # canonical 分片 -> 入站 SSE 文本
	Call(Request, BaseURL, ApiKey, Model, Stream)     # canonical -> 上游（返回响应或分片生成器）

注意：这里不在模块顶层 import 各适配器（连带 SDK）。gemini 的 SDK 冷启动导入要上百秒，
一律走惰性导入，避免拖慢 Flask 启动。
"""
import importlib

_MODULES = {
	"openai": "protocol.openai",
	"anthropic": "protocol.anthropic",
	"gemini": "protocol.gemini",
}

# 用户上传 key 时可能填的协议名，统一归一到内部标识
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

# 可以直接作为“入站协议”的（即 /v1 路由支持的）
INBOUND = ("openai", "anthropic")
# 可以作为“上游协议”的（即社区 key 的 protocol 字段支持的）
UPSTREAM = ("openai", "anthropic", "gemini")


def Normalize(Protocol):
	"""把用户填写的协议名归一到内部标识，认不出来返回 None。"""
	if not Protocol:
		return None
	return _ALIASES.get(str(Protocol).strip().lower())


def Get(Protocol):
	"""按协议名取适配器模块，不认识就抛 ValueError。"""
	Name = Normalize(Protocol)
	if Name is None:
		raise ValueError(f"不支持的协议：{Protocol}")
	return importlib.import_module(_MODULES[Name])
