"""OpenAI 协议适配：既是入站协议（/v1/chat/completions），也是最常见的上游协议。"""
import openai

from protocol import common

NAME = "openai"


def _Tools(Tools):
	"""OpenAI 的 tool 定义 -> canonical 的 tool 定义。"""
	if not Tools:
		return None
	Result = []
	for Tool in Tools:
		Function = Tool.get("function") if isinstance(Tool, dict) else None
		if Function:
			Result.append({
				"name": Function.get("name"),
				"description": Function.get("description"),
				"parameters": Function.get("parameters"),
			})
		else:
			Result.append(Tool)
	return Result


def _CanonicalTools(Tools):
	"""canonical 的 tool 定义 -> OpenAI 的 tool 定义。"""
	Result = []
	for Tool in Tools:
		Result.append({
			"type": "function",
			"function": {
				"name": Tool.get("name"),
				"description": Tool.get("description"),
				"parameters": Tool.get("parameters") or {"type": "object", "properties": {}},
			},
		})
	return Result


def _Parts(Content):
	"""OpenAI 的 content（str 或 [{type}]）-> canonical parts。"""
	if Content is None:
		return []
	if isinstance(Content, str):
		return [{"type": "text", "text": Content}]
	Parts = []
	for Part in Content:
		if isinstance(Part, str):
			Parts.append({"type": "text", "text": Part})
			continue
		if not isinstance(Part, dict):
			continue
		Type = Part.get("type")
		if Type in (None, "text", "input_text", "output_text"):
			if Part.get("text"):
				Parts.append({"type": "text", "text": Part["text"]})
		elif Type in ("image_url", "input_image"):
			Image = Part.get("image_url") or Part.get("image")
			Url = Image.get("url") if isinstance(Image, dict) else Image
			Parts.append({"type": "image", "url": Url})
		else:
			Parts.append(dict(Part))
	return Parts


def _Content(Parts):
	"""canonical parts -> OpenAI 的 content（全是文本时压成字符串，兼容性最好）。"""
	Result = []
	for Part in Parts:
		Type = Part.get("type")
		if Type == "text":
			Result.append({"type": "text", "text": Part.get("text") or ""})
		elif Type == "image":
			Url = Part.get("url") or "data:" + str(Part.get("media_type") or "image/png") + ";base64," + str(Part.get("data") or "")
			Result.append({"type": "image_url", "image_url": {"url": Url}})
		else:
			Result.append(dict(Part))
	if all(Item.get("type") == "text" for Item in Result):
		return "".join(Item.get("text") or "" for Item in Result)
	return Result


def _ToolCalls(ToolCalls):
	"""canonical 的 tool_calls -> OpenAI 的 tool_calls。"""
	Result = []
	for Call in ToolCalls:
		Result.append({
			"id": Call.get("id") or common.NewID("call"),
			"type": "function",
			"function": {
				"name": Call.get("name"),
				"arguments": Call.get("arguments") or "",
			},
		})
	return Result


def ParseRequest(Body) -> dict:
	"""入站：OpenAI /v1/chat/completions 请求体 -> canonical request。"""
	System = []
	Messages = []
	for Message in Body.get("messages") or []:
		Role = str(Message.get("role") or "user").lower()
		if Role in ("system", "developer"):
			Text = common.AsText(Message.get("content"))
			if Text:
				System.append(Text)
			continue
		if Role == "tool":
			Messages.append({
				"role": "tool",
				"tool_call_id": Message.get("tool_call_id"),
				"content": _Parts(Message.get("content")),
			})
			continue
		Item = {"role": "assistant" if Role == "assistant" else "user", "content": _Parts(Message.get("content"))}
		if Message.get("tool_calls"):
			Item["tool_calls"] = []
			for Call in Message["tool_calls"]:
				Function = Call.get("function") or {}
				Item["tool_calls"].append({
					"id": Call.get("id"),
					"name": Function.get("name"),
					"arguments": Function.get("arguments") or "",
				})
		Messages.append(Item)
	return {
		"model": Body.get("model"),
		"system": "\n".join(System) or None,
		"messages": Messages,
		"temperature": Body.get("temperature"),
		"top_p": Body.get("top_p"),
		"max_tokens": Body.get("max_tokens") or Body.get("max_completion_tokens"),
		"stop": Body.get("stop"),
		"stream": bool(Body.get("stream")),
		"tools": _Tools(Body.get("tools")),
		"tool_choice": Body.get("tool_choice"),
		"raw": Body,
	}


def BuildParams(Request, Model) -> dict:
	"""canonical request -> OpenAI 上游调用参数。"""
	Messages = []
	if Request.get("system"):
		Messages.append({"role": "system", "content": Request["system"]})
	for Message in Request.get("messages") or []:
		if Message["role"] == "tool":
			Messages.append({
				"role": "tool",
				"tool_call_id": Message.get("tool_call_id"),
				"content": common.AsText(Message.get("content")),
			})
			continue
		Item = {"role": Message["role"], "content": _Content(Message.get("content") or [])}
		if Message.get("tool_calls"):
			Item["tool_calls"] = _ToolCalls(Message["tool_calls"])
		Messages.append(Item)
	Params = {"model": Model, "messages": Messages}
	if Request.get("temperature") is not None:
		Params["temperature"] = Request["temperature"]
	if Request.get("top_p") is not None:
		Params["top_p"] = Request["top_p"]
	if Request.get("max_tokens") is not None:
		Params["max_tokens"] = Request["max_tokens"]
	if Request.get("stop"):
		Params["stop"] = Request["stop"]
	if Request.get("tools"):
		Params["tools"] = _CanonicalTools(Request["tools"])
		if Request.get("tool_choice"):
			Params["tool_choice"] = Request["tool_choice"]
	return Params


def ToCanonical(Raw) -> dict:
	"""上游响应 -> canonical response。OpenAI 系上游本来就是 canonical，基本是原样返回。"""
	Data = common.Dump(Raw)
	Data.setdefault("object", "chat.completion")
	Data.setdefault("created", common.Now())
	if not Data.get("id"):
		Data["id"] = common.NewID()
	return Data


def Call(Request, BaseURL, ApiKey, Model, Stream=False):
	"""用官方 openai SDK 把请求打到上游。"""
	Client = openai.OpenAI(api_key=ApiKey or "not-needed", base_url=BaseURL or None)
	Params = BuildParams(Request, Model)
	if Stream:
		Params["stream"] = True
		return (ToCanonical(Chunk) for Chunk in Client.chat.completions.create(**Params))
	return ToCanonical(Client.chat.completions.create(**Params))


def RenderResponse(Response, Request) -> dict:
	"""canonical response -> OpenAI 入站响应（本协议下就是原样）。"""
	return Response


def RenderStream(Chunks, Request):
	"""canonical 分片 -> OpenAI 的 SSE 文本。"""
	for Data in Chunks:
		yield common.SSELine(Data)
	yield "data: [DONE]\n\n"


def ParseCompletionRequest(Body) -> dict:
	"""入站：OpenAI /v1/completions（legacy）请求体 -> canonical request。"""
	Prompt = Body.get("prompt")
	if isinstance(Prompt, list):
		Text = "\n".join(str(Item) for Item in Prompt)
	elif Prompt is None:
		Text = ""
	else:
		Text = str(Prompt)
	return {
		"model": Body.get("model"),
		"system": None,
		"messages": [{"role": "user", "content": [{"type": "text", "text": Text}]}],
		"temperature": Body.get("temperature"),
		"top_p": Body.get("top_p"),
		"max_tokens": Body.get("max_tokens"),
		"stop": Body.get("stop"),
		"stream": bool(Body.get("stream")),
		"tools": None,
		"tool_choice": None,
		"raw": Body,
	}


def RenderCompletion(Response, Request) -> dict:
	"""canonical response -> OpenAI 的 text_completion 结构（legacy /v1/completions）。"""
	Choice = (Response.get("choices") or [{}])[0]
	Message = Choice.get("message") or {}
	Usage = Response.get("usage") or {}
	return {
		"id": Response.get("id") or common.NewID("cmpl"),
		"object": "text_completion",
		"created": Response.get("created") or common.Now(),
		"model": Response.get("model") or Request.get("model"),
		"choices": [{
			"text": Message.get("content") or "",
			"index": 0,
			"logprobs": None,
			"finish_reason": Choice.get("finish_reason") or "stop",
		}],
		"usage": Usage or common.MakeUsage(),
	}


def RenderCompletionStream(Chunks, Request):
	"""canonical 分片 -> legacy /v1/completions 的 SSE 文本。"""
	Model = Request.get("model")
	for Data in Chunks:
		Choice = (Data.get("choices") or [{}])[0]
		Delta = Choice.get("delta") or {}
		Frame = {
			"id": Data.get("id") or common.NewID("cmpl"),
			"object": "text_completion",
			"created": Data.get("created") or common.Now(),
			"model": Data.get("model") or Model,
			"choices": [{
				"text": Delta.get("content") or "",
				"index": 0,
				"logprobs": None,
				"finish_reason": Choice.get("finish_reason"),
			}],
		}
		if Data.get("usage"):
			Frame["usage"] = Data["usage"]
		yield common.SSELine(Frame)
	yield "data: [DONE]\n\n"


def Embeddings(BaseURL, ApiKey, Model, Payload) -> dict:
	"""把 embeddings 请求打到 OpenAI 兼容上游（只有 openai 协议支持 embeddings）。"""
	Client = openai.OpenAI(api_key=ApiKey or "not-needed", base_url=BaseURL or None)
	Params = {"model": Model, "input": Payload.get("input")}
	for Field in ("encoding_format", "dimensions", "user"):
		if Payload.get(Field) is not None:
			Params[Field] = Payload[Field]
	return common.Dump(Client.embeddings.create(**Params))