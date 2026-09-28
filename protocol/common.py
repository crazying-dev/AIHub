"""协议适配层的公共小工具。

canonical（统一中间格式）约定：
- 请求：{"model", "system", "messages", "temperature", "top_p", "max_tokens",
         "stop", "stream", "tools", "tool_choice", "raw"}
  messages 只含 user / assistant / tool 三种角色；
  content 统一是 parts 列表：[{"type": "text", "text": ...},
                             {"type": "image", "media_type": ..., "data": ...},
                             {"type": "image", "url": ...}]
  assistant 的 tool_calls 是：[{"id", "name", "arguments"}]（arguments 为 JSON 字符串）
  tool 消息形如：{"role": "tool", "tool_call_id": ..., "content": parts}
- 响应：OpenAI 的 chat.completion 结构（choices[].message / usage）
- 流式：OpenAI 的 chat.completion.chunk 结构（choices[].delta / usage）
"""
import json
import time
import uuid


def NewID(Prefix="chatcmpl") -> str:
	return f"{Prefix}-{uuid.uuid4().hex[:24]}"


def Now() -> int:
	return int(time.time())


def Dumps(Data) -> str:
	return json.dumps(Data, ensure_ascii=False)


def Loads(Text):
	"""把 JSON 字符串解析成对象，解析不了就返回空字典。"""
	if isinstance(Text, (dict, list)):
		return Text
	if not Text:
		return {}
	try:
		return json.loads(Text)
	except (TypeError, ValueError):
		return {}


def AsText(Content) -> str:
	"""把各种形态的 content 拍平成纯文本。"""
	if Content is None:
		return ""
	if isinstance(Content, str):
		return Content
	if isinstance(Content, list):
		Texts = []
		for part in Content:
			if isinstance(part, str):
				Texts.append(part)
			elif isinstance(part, dict) and part.get("text"):
				Texts.append(part["text"])
		return "".join(Texts)
	return str(Content)


def SSELine(Data) -> str:
	"""SSE 一帧：data: {...}\\n\\n"""
	if not isinstance(Data, str):
		Data = Dumps(Data)
	return "data: " + Data + "\n\n"


def SSEEvent(Event, Data) -> str:
	"""带事件名的 SSE 帧（Anthropic 要求 event: 行）。"""
	return "event: " + Event + "\ndata: " + Dumps(Data) + "\n\n"


def MakeUsage(Prompt=0, Completion=0) -> dict:
	Prompt = Prompt or 0
	Completion = Completion or 0
	return {"prompt_tokens": Prompt, "completion_tokens": Completion, "total_tokens": Prompt + Completion}


def Dump(Raw) -> dict:
	"""把官方 SDK 返回的对象转成 dict（本仓只处理 JSON 可序列化的字段）。"""
	if isinstance(Raw, dict):
		return dict(Raw)
	ToDict = getattr(Raw, "model_dump", None)
	if callable(ToDict):
		return ToDict()
	ToDict = getattr(Raw, "to_dict", None)
	if callable(ToDict):
		return ToDict()
	return dict(Raw)


def Chunk(ID, Model, Delta, Finish=None, Usage=None) -> dict:
	"""构造一个 canonical 流式分片。"""
	Data = {
		"id": ID or NewID(),
		"object": "chat.completion.chunk",
		"created": Now(),
		"model": Model,
		"choices": [{"index": 0, "delta": Delta or {}, "finish_reason": Finish}],
	}
	if Usage is not None:
		Data["usage"] = Usage
	return Data


def Response(ID, Model, Message, Finish="stop", Usage=None) -> dict:
	"""构造一个 canonical 非流式响应。"""
	return {
		"id": ID or NewID(),
		"object": "chat.completion",
		"created": Now(),
		"model": Model,
		"choices": [{"index": 0, "message": Message, "finish_reason": Finish}],
		"usage": Usage or MakeUsage(),
	}


def MergeSameRole(Messages) -> list:
	"""合并相邻同角色消息（OpenAI 侧允许连续同角色，Anthropic 要求 user/assistant 交替）。"""
	Merged = []
	for message in Messages:
		if Merged and Merged[-1]["role"] == message["role"] and message["role"] in ("user", "assistant"):
			Last = Merged[-1]
			Last["content"] = list(Last.get("content") or []) + list(message.get("content") or [])
			if message.get("tool_calls"):
				Last["tool_calls"] = list(Last.get("tool_calls") or []) + list(message["tool_calls"])
		else:
			Merged.append(message)
	return Merged


def _TokenCount(Text) -> int:
	"""粗估一段文本的 token 数：非 ASCII 字符按 1 个算，ASCII 每 4 个字符算 1 个。"""
	if not Text:
		return 0
	Wide = 0
	Narrow = 0
	for Character in Text:
		if ord(Character) > 0x7F:
			Wide += 1
		else:
			Narrow += 1
	return Wide + (Narrow + 3) // 4


def EstimateTokens(Request) -> int:
	"""估算 canonical request 的输入 token 数（count_tokens 用；图片按 85 个算）。

说明：AIHub 是中继，上游协议各不相同，没法用统一的真实分词器，
这里给的是保守估计——够客户端做上下文预算，不要当精确值用。
"""
	Total = 0
	if Request.get("system"):
		Total += _TokenCount(Request["system"])
	for Message in Request.get("messages") or []:
		Total += 4
		for Part in Message.get("content") or []:
			Type = Part.get("type")
			if Type == "text":
				Total += _TokenCount(Part.get("text"))
			elif Type == "image":
				Total += 85
		for Call in Message.get("tool_calls") or []:
			Total += _TokenCount(Call.get("name"))
			Total += _TokenCount(Call.get("arguments"))
	for Tool in Request.get("tools") or []:
		Total += _TokenCount(Tool.get("name"))
		Total += _TokenCount(Tool.get("description"))
		Total += _TokenCount(Dumps(Tool.get("parameters") or {}))
	return max(1, Total)