"""Gemini（Google Generative Language）协议适配：既作为上游协议，也作为入站协议。

入站（Google 原生 REST 风格，鉴权用 ?key= 或 x-goog-api-key）：
- POST /v1beta/models/{model}:generateContent
- POST /v1beta/models/{model}:streamGenerateContent
- POST /v1beta/models/{model}:countTokens
- GET  /v1beta/models
上游：google-genai 的冷启动导入很慢（首次可能上百秒），所以 SDK 一律在 Call 里惰性导入。
"""
from protocol import common

NAME = "gemini"

# canonical 的 finish_reason -> Gemini 的 finishReason
_FINISH_OUT = {
	"stop": "STOP",
	"length": "MAX_TOKENS",
	"tool_calls": "STOP",
	"content_filter": "SAFETY",
}


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
	"""Gemini 的 finishReason -> canonical 的 finish_reason。"""
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


def _InPart(Part):
	"""Gemini 的单个 part -> (类型, canonical 片段)。"""
	if not isinstance(Part, dict):
		return None
	if Part.get("text") is not None:
		return "text", {"type": "text", "text": Part.get("text") or ""}
	Inline = Part.get("inline_data") or Part.get("inlineData")
	if Inline:
		return "image", {"type": "image", "media_type": Inline.get("mime_type") or Inline.get("mimeType"), "data": Inline.get("data")}
	Call = Part.get("function_call") or Part.get("functionCall")
	if Call:
		return "call", {"id": common.NewID("call"), "name": Call.get("name"), "arguments": common.Dumps(Call.get("args") or {})}
	Response = Part.get("function_response") or Part.get("functionResponse")
	if Response:
		Payload = Response.get("response")
		Text = common.AsText(Payload.get("result") if isinstance(Payload, dict) else Payload)
		return "result", {"role": "tool", "tool_call_id": Response.get("name"), "content": [{"type": "text", "text": Text}]}
	return None


def _ContentsRequest(Contents):
	"""Gemini 的 contents -> canonical messages。"""
	Messages = []
	for Content in Contents or []:
		if not isinstance(Content, dict):
			continue
		Role = str(Content.get("role") or "user").lower()
		Parts = []
		ToolCalls = []
		ToolResults = []
		for Part in Content.get("parts") or []:
			Parsed = _InPart(Part)
			if Parsed is None:
				continue
			Kind, Value = Parsed
			if Kind == "call":
				ToolCalls.append(Value)
			elif Kind == "result":
				ToolResults.append(Value)
			else:
				Parts.append(Value)
		Messages.extend(ToolResults)
		Item = {"role": "assistant" if Role == "model" else "user", "content": Parts}
		if ToolCalls:
			Item["tool_calls"] = ToolCalls
		if Item["content"] or Item.get("tool_calls"):
			Messages.append(Item)
	return Messages


def _SystemText(System):
	"""Gemini 的 systemInstruction -> 纯文本。"""
	if not System:
		return None
	if isinstance(System, str):
		return System
	Parts = System.get("parts") if isinstance(System, dict) else None
	Text = common.AsText([{"text": Part.get("text")} for Part in Parts or [] if isinstance(Part, dict)])
	return Text or None


def ParseRequest(Body) -> dict:
	"""入站：Gemini generateContent 请求体 -> canonical request（model 由 URL 决定，这里留空）。"""
	Config = Body.get("generationConfig") or Body.get("generation_config") or {}
	Tools = None
	for Tool in Body.get("tools") or []:
		if not isinstance(Tool, dict):
			continue
		Declarations = Tool.get("functionDeclarations") or Tool.get("function_declarations") or []
		for Declaration in Declarations:
			if not isinstance(Declaration, dict) or not Declaration.get("name"):
				continue
			Tools = Tools or []
			Tools.append({
				"name": Declaration.get("name"),
				"description": Declaration.get("description"),
				"parameters": Declaration.get("parameters"),
			})
	return {
		"model": None,
		"system": _SystemText(Body.get("systemInstruction") or Body.get("system_instruction")),
		"messages": _ContentsRequest(Body.get("contents") or Body.get("content")),
		"temperature": Config.get("temperature"),
		"top_p": Config.get("topP") if Config.get("topP") is not None else Config.get("top_p"),
		"max_tokens": Config.get("maxOutputTokens") or Config.get("max_output_tokens"),
		"stop": Config.get("stopSequences") or Config.get("stop_sequences"),
		"stream": False,
		"tools": Tools,
		"tool_choice": None,
		"raw": Body,
	}


def _OutParts(Message):
	"""canonical message -> Gemini 的 parts。"""
	Parts = []
	if Message.get("content"):
		Parts.append({"text": Message["content"]})
	for Call in Message.get("tool_calls") or []:
		Function = Call.get("function") or {}
		Parts.append({"functionCall": {"name": Function.get("name"), "args": common.Loads(Function.get("arguments"))}})
	return Parts


def RenderResponse(Response, Request) -> dict:
	"""canonical response -> Gemini 的 generateContent 响应体。"""
	Choice = (Response.get("choices") or [{}])[0]
	Message = Choice.get("message") or {}
	Parts = _OutParts(Message) or [{"text": ""}]
	Usage = Response.get("usage") or {}
	Prompt = Usage.get("prompt_tokens") or 0
	Completion = Usage.get("completion_tokens") or 0
	return {
		"candidates": [{
			"content": {"role": "model", "parts": Parts},
			"finishReason": _FINISH_OUT.get(Choice.get("finish_reason"), "STOP"),
			"index": 0,
			"safetyRatings": [],
		}],
		"usageMetadata": {
			"promptTokenCount": Prompt,
			"candidatesTokenCount": Completion,
			"totalTokenCount": Prompt + Completion,
		},
		"modelVersion": Response.get("model") or Request.get("model"),
	}


def RenderStream(Chunks, Request):
	"""canonical 分片 -> Gemini 的 SSE 文本（等价于 ?alt=sse）。"""
	for Data in Chunks:
		Choice = (Data.get("choices") or [{}])[0]
		Delta = Choice.get("delta") or {}
		Parts = _OutParts({"content": Delta.get("content"), "tool_calls": Delta.get("tool_calls")})
		Finish = Choice.get("finish_reason")
		if not Parts and not Finish:
			continue
		Candidate = {"content": {"role": "model", "parts": Parts}, "index": 0}
		if Finish:
			Candidate["finishReason"] = _FINISH_OUT.get(Finish, "STOP")
		Frame = {"candidates": [Candidate], "modelVersion": Request.get("model")}
		Usage = Data.get("usage") or {}
		if Usage.get("prompt_tokens") or Usage.get("completion_tokens"):
			Prompt = Usage.get("prompt_tokens") or 0
			Completion = Usage.get("completion_tokens") or 0
			Frame["usageMetadata"] = {
				"promptTokenCount": Prompt,
				"candidatesTokenCount": Completion,
				"totalTokenCount": Prompt + Completion,
			}
		yield common.SSELine(Frame)


def RenderModels(Names):
	"""GET /v1beta/models 的响应体。"""
	Models = []
	for Name in Names:
		Models.append({
			"name": "models/" + str(Name),
			"displayName": str(Name),
			"description": "AIHub 中继模型",
			"supportedGenerationMethods": ["generateContent", "streamGenerateContent", "countTokens"],
		})
	return {"models": Models}


def RenderCountTokens(Total) -> dict:
	"""countTokens 的响应体。"""
	return {"totalTokens": int(Total)}