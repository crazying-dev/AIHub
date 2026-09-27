"""Gemini（Google Generative Language）协议适配：目前只作为上游协议。

google-genai 的冷启动导入很慢（首次可能上百秒），所以 SDK 一律在 Call 里惰性导入。
"""
from protocol import common

NAME = "gemini"


def _Parts(Parts):
	"""canonical parts -> Gemini 的 parts。"""
	Result = []
	for Part in Parts:
		if Part.get("type") == "text":
			Result.append({"text": Part.get("text") or ""})
		elif Part.get("type") == "image" and Part.get("data"):
			Result.append({"inline_data": {"mime_type": Part.get("media_type") or "image/png", "data": Part.get("data")}})
	return Result


def _Contents(Request):
	"""canonical messages -> Gemini 的 contents。"""
	Result = []
	for Message in common.MergeSameRole(Request.get("messages") or []):
		Role = "model" if Message["role"] == "assistant" else "user"
		Parts = list(_Parts(Message.get("content") or []))
		for ToolCall in Message.get("tool_calls") or []:
			Parts.append({"function_call": {"name": ToolCall.get("name"), "args": common.Loads(ToolCall.get("arguments"))}})
		if Message["role"] == "tool":
			Parts.append({"function_response": {"name": Message.get("name") or "tool", "response": {"result": common.AsText(Message.get("content"))}}})
		if Parts:
			Result.append({"role": Role, "parts": Parts})
	return Result


def _Text(Raw):
	"""取 Gemini 响应里的文本（无候选/被安全拦截时会抛异常）。"""
	try:
		return Raw.text or ""
	except Exception:
		return ""


def _Finish(FinishReason):
	Name = getattr(FinishReason, "name", None) or str(FinishReason or "")
	if "MAX_TOKENS" in Name:
		return "length"
	if "SAFETY" in Name or "BLOCK" in Name:
		return "content_filter"
	return "stop"


def _Usage(Raw, Prompt=0, Completion=0):
	Usage = getattr(Raw, "usage_metadata", None)
	return common.MakeUsage(
		getattr(Usage, "prompt_token_count", 0) or Prompt,
		getattr(Usage, "candidates_token_count", 0) or Completion,
	)


def ToCanonical(Raw, Model=None) -> dict:
	"""上游响应 -> canonical response。"""
	Candidates = getattr(Raw, "candidates", None) or []
	Finish = getattr(Candidates[0], "finish_reason", None) if Candidates else None
	Message = {"role": "assistant", "content": _Text(Raw) or None}
	return common.Response(None, Model, Message, _Finish(Finish), _Usage(Raw))


def ParseStream(Chunks, Model=None):
	"""上游 Gemini 流 -> canonical 分片（生成器）。"""
	First = True
	Prompt = 0
	Completion = 0
	Finish = None
	for Raw in Chunks:
		Text = _Text(Raw)
		Usage = _Usage(Raw, Prompt, Completion)
		Prompt = Usage["prompt_tokens"]
		Completion = Usage["completion_tokens"]
		Candidates = getattr(Raw, "candidates", None) or []
		if Candidates:
			Finish = getattr(Candidates[0], "finish_reason", None) or Finish
		Delta = {"content": Text} if Text else {}
		if First:
			Delta["role"] = "assistant"
			First = False
		yield common.Chunk(None, Model, Delta)
	yield common.Chunk(None, Model, {}, _Finish(Finish), common.MakeUsage(Prompt, Completion))


def Call(Request, BaseURL, ApiKey, Model, Stream=False):
	"""用官方 google-genai SDK 把请求打到上游。"""
	from google import genai
	from google.genai import types

	Options = types.HttpOptions(base_url=BaseURL) if BaseURL else None
	Client = genai.Client(api_key=ApiKey, http_options=Options)
	Config = types.GenerateContentConfig(
		system_instruction=Request.get("system") or None,
		temperature=Request.get("temperature"),
		top_p=Request.get("top_p"),
		max_output_tokens=Request.get("max_tokens"),
		stop_sequences=Request.get("stop") if isinstance(Request.get("stop"), list) else None,
	)
	Contents = _Contents(Request)
	if Stream:
		return ParseStream(Client.models.generate_content_stream(model=Model, contents=Contents, config=Config), Model)
	return ToCanonical(Client.models.generate_content(model=Model, contents=Contents, config=Config), Model)


def ParseRequest(Body) -> dict:
	"""Gemini 暂不支持作为入站协议。"""
	raise ValueError("Gemini 目前只作为上游协议，入站请用 /v1/chat/completions 或 /v1/messages")


def RenderResponse(Response, Request) -> dict:
	return Response


def RenderStream(Chunks, Request):
	for Data in Chunks:
		yield common.SSELine(Data)
	yield "data: [DONE]\n\n"
