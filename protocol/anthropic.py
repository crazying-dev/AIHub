"""Anthropic（Claude Messages）协议适配：既是入站协议（/v1/messages），也可作为上游协议。"""
import anthropic

from protocol import common

NAME = "anthropic"


def _Finish(StopReason):
	"""Anthropic 的 stop_reason -> OpenAI 的 finish_reason。"""
	if StopReason == "max_tokens":
		return "length"
	if StopReason == "tool_use":
		return "tool_calls"
	return "stop"


def _StopReason(FinishReason):
	"""OpenAI 的 finish_reason -> Anthropic 的 stop_reason。"""
	if FinishReason == "length":
		return "max_tokens"
	if FinishReason == "tool_calls":
		return "tool_use"
	return "end_turn"


def _Blocks(Parts):
	"""canonical parts -> Anthropic 的 content blocks。"""
	Result = []
	for Part in Parts:
		Type = Part.get("type")
		if Type == "text":
			Result.append({"type": "text", "text": Part.get("text") or ""})
		elif Type == "image":
			if Part.get("data"):
				Result.append({
					"type": "image",
					"source": {
						"type": "base64",
						"media_type": Part.get("media_type") or "image/png",
						"data": Part.get("data"),
					},
				})
			elif Part.get("url"):
				Result.append({"type": "image", "source": {"type": "url", "url": Part["url"]}})
	return Result


def _Parts(Blocks):
	"""Anthropic 的 content blocks -> canonical parts。"""
	if isinstance(Blocks, str):
		return [{"type": "text", "text": Blocks}]
	Result = []
	for Block in Blocks or []:
		if not isinstance(Block, dict):
			continue
		Type = Block.get("type")
		if Type == "text":
			Result.append({"type": "text", "text": Block.get("text") or ""})
		elif Type == "image":
			Source = Block.get("source") or {}
			if Source.get("type") == "base64":
				Result.append({"type": "image", "media_type": Source.get("media_type"), "data": Source.get("data")})
			else:
				Result.append({"type": "image", "url": Source.get("url")})
	return Result


def _Tools(Tools):
	"""Anthropic 的 tool 定义 -> canonical 的 tool 定义。"""
	if not Tools:
		return None
	Result = []
	for Tool in Tools:
		Result.append({
			"name": Tool.get("name"),
			"description": Tool.get("description"),
			"parameters": Tool.get("input_schema"),
		})
	return Result


def _CanonicalTools(Tools):
	"""canonical 的 tool 定义 -> Anthropic 的 tool 定义。"""
	Result = []
	for Tool in Tools:
		Result.append({
			"name": Tool.get("name"),
			"description": Tool.get("description"),
			"input_schema": Tool.get("parameters") or {"type": "object", "properties": {}},
		})
	return Result


def ParseRequest(Body) -> dict:
	"""入站：Anthropic /v1/messages 请求体 -> canonical request。"""
	System = Body.get("system")
	SystemText = System if isinstance(System, str) else common.AsText(System)
	Messages = []
	for Message in Body.get("messages") or []:
		Role = str(Message.get("role") or "user").lower()
		Blocks = Message.get("content")
		if isinstance(Blocks, str):
			Blocks = [{"type": "text", "text": Blocks}]
		Parts = []
		ToolCalls = []
		ToolResults = []
		for Block in Blocks or []:
			Type = Block.get("type")
			if Type == "text":
				Parts.append({"type": "text", "text": Block.get("text") or ""})
			elif Type == "image":
				Parts.extend(_Parts([Block]))
			elif Type == "tool_use":
				ToolCalls.append({
					"id": Block.get("id"),
					"name": Block.get("name"),
					"arguments": common.Dumps(Block.get("input") or {}),
				})
			elif Type == "tool_result":
				ToolResults.append({
					"role": "tool",
					"tool_call_id": Block.get("tool_use_id"),
					"content": _Parts(Block.get("content")),
				})
		Messages.extend(ToolResults)
		Item = {"role": "assistant" if Role == "assistant" else "user", "content": Parts}
		if ToolCalls:
			Item["tool_calls"] = ToolCalls
		if Item["content"] or Item.get("tool_calls"):
			Messages.append(Item)
	return {
		"model": Body.get("model"),
		"system": SystemText or None,
		"messages": Messages,
		"temperature": Body.get("temperature"),
		"top_p": Body.get("top_p"),
		"max_tokens": Body.get("max_tokens"),
		"stop": Body.get("stop_sequences"),
		"stream": bool(Body.get("stream")),
		"tools": _Tools(Body.get("tools")),
		"tool_choice": Body.get("tool_choice"),
		"raw": Body,
	}


def BuildParams(Request, Model) -> dict:
	"""canonical request -> Anthropic 上游调用参数。"""
	Messages = []
	for Message in common.MergeSameRole(Request.get("messages") or []):
		if Message["role"] == "tool":
			Messages.append({
				"role": "user",
				"content": [{
					"type": "tool_result",
					"tool_use_id": Message.get("tool_call_id"),
					"content": common.AsText(Message.get("content")),
				}],
			})
			continue
		Blocks = _Blocks(Message.get("content") or [])
		for ToolCall in Message.get("tool_calls") or []:
			Blocks.append({
				"type": "tool_use",
				"id": ToolCall.get("id") or common.NewID("toolu"),
				"name": ToolCall.get("name"),
				"input": common.Loads(ToolCall.get("arguments")),
			})
		if not Blocks:
			Blocks = [{"type": "text", "text": ""}]
		Messages.append({"role": "assistant" if Message["role"] == "assistant" else "user", "content": Blocks})
	Params = {"model": Model, "messages": Messages, "max_tokens": Request.get("max_tokens") or 4096}
	if Request.get("system"):
		Params["system"] = Request["system"]
	if Request.get("temperature") is not None:
		Params["temperature"] = min(max(float(Request["temperature"]), 0.0), 1.0)
	if Request.get("stop"):
		Stop = Request["stop"]
		Params["stop_sequences"] = Stop if isinstance(Stop, list) else [Stop]
	if Request.get("tools"):
		Params["tools"] = _CanonicalTools(Request["tools"])
	return Params


def ToCanonical(Raw, Model=None) -> dict:
	"""上游响应 -> canonical response。"""
	Data = common.Dump(Raw)
	if Data.get("choices"):
		return Data
	Texts = []
	ToolCalls = []
	for Block in Data.get("content") or []:
		Type = Block.get("type")
		if Type == "text":
			Texts.append(Block.get("text") or "")
		elif Type == "tool_use":
			ToolCalls.append({
				"id": Block.get("id"),
				"type": "function",
				"function": {
					"name": Block.get("name"),
					"arguments": common.Dumps(Block.get("input") or {}),
				},
			})
	Usage = Data.get("usage") or {}
	Prompt = Usage.get("input_tokens") or 0
	Completion = Usage.get("output_tokens") or 0
	Message = {"role": "assistant", "content": "".join(Texts) or None}
	if ToolCalls:
		Message["tool_calls"] = ToolCalls
	return common.Response(Data.get("id"), Data.get("model") or Model, Message, _Finish(Data.get("stop_reason")), common.MakeUsage(Prompt, Completion))


def ParseStream(Events, Model=None):
	"""上游 Anthropic 事件流 -> canonical 分片（生成器）。"""
	State = {"id": None, "model": Model, "tool_index": 0, "finish": None, "prompt": 0, "completion": 0}
	for Event in Events:
		Data = common.Dump(Event)
		Type = Data.get("type")
		if Type == "message_start":
			Message = Data.get("message") or {}
			State["id"] = Message.get("id")
			State["model"] = Message.get("model") or Model
			Usage = Message.get("usage") or {}
			State["prompt"] = Usage.get("input_tokens") or 0
			yield common.Chunk(State["id"], State["model"], {"role": "assistant", "content": ""})
		elif Type == "content_block_start":
			Block = Data.get("content_block") or {}
			if Block.get("type") == "tool_use":
				yield common.Chunk(State["id"], State["model"], {"tool_calls": [{"index": State["tool_index"], "id": Block.get("id"), "type": "function", "function": {"name": Block.get("name"), "arguments": ""}}]})
				State["tool_index"] += 1
		elif Type == "content_block_delta":
			Delta = Data.get("delta") or {}
			if Delta.get("type") == "text_delta" and Delta.get("text"):
				yield common.Chunk(State["id"], State["model"], {"content": Delta["text"]})
			elif Delta.get("type") == "input_json_delta" and Delta.get("partial_json"):
				Index = max(State["tool_index"] - 1, 0)
				yield common.Chunk(State["id"], State["model"], {"tool_calls": [{"index": Index, "function": {"arguments": Delta["partial_json"]}}]})
		elif Type == "message_delta":
			Delta = Data.get("delta") or {}
			if Delta.get("stop_reason"):
				State["finish"] = Delta["stop_reason"]
			Usage = Data.get("usage") or {}
			if Usage.get("output_tokens"):
				State["completion"] = Usage["output_tokens"]
		elif Type == "message_stop":
			yield common.Chunk(State["id"], State["model"], {}, _Finish(State["finish"]), common.MakeUsage(State["prompt"], State["completion"]))


def Call(Request, BaseURL, ApiKey, Model, Stream=False):
	"""用官方 anthropic SDK 把请求打到上游。"""
	Client = anthropic.Anthropic(api_key=ApiKey or "not-needed", base_url=BaseURL or None)
	Params = BuildParams(Request, Model)
	if Stream:
		Params["stream"] = True
		return ParseStream(Client.messages.create(**Params), Model)
	return ToCanonical(Client.messages.create(**Params), Model)


def RenderResponse(Response, Request) -> dict:
	"""canonical response -> Anthropic 的 message 响应体。"""
	Choice = (Response.get("choices") or [{}])[0]
	Message = Choice.get("message") or {}
	Blocks = []
	if Message.get("content"):
		Blocks.append({"type": "text", "text": Message["content"]})
	for ToolCall in Message.get("tool_calls") or []:
		Function = ToolCall.get("function") or {}
		Blocks.append({
			"type": "tool_use",
			"id": ToolCall.get("id") or common.NewID("toolu"),
			"name": Function.get("name"),
			"input": common.Loads(Function.get("arguments")),
		})
	if not Blocks:
		Blocks.append({"type": "text", "text": ""})
	Usage = Response.get("usage") or {}
	return {
		"id": Response.get("id") or common.NewID("msg"),
		"type": "message",
		"role": "assistant",
		"model": Response.get("model") or Request.get("model"),
		"content": Blocks,
		"stop_reason": _StopReason(Choice.get("finish_reason")),
		"stop_sequence": None,
		"usage": {
			"input_tokens": Usage.get("prompt_tokens", 0),
			"output_tokens": Usage.get("completion_tokens", 0),
		},
	}


def RenderStream(Chunks, Request):
	"""canonical 分片 -> Anthropic 的 SSE 事件流。"""
	State = {"started": False, "id": None, "model": Request.get("model"), "text_index": None, "tools": {}, "order": [], "next": 0, "finish": None, "prompt": 0, "completion": 0}
	for Data in Chunks:
		Choice = (Data.get("choices") or [{}])[0]
		Delta = Choice.get("delta") or {}
		Usage = Data.get("usage") or {}
		if Data.get("id"):
			State["id"] = Data["id"]
		if Data.get("model"):
			State["model"] = Data["model"]
		if Usage.get("prompt_tokens"):
			State["prompt"] = Usage["prompt_tokens"]
		if Usage.get("completion_tokens"):
			State["completion"] = Usage["completion_tokens"]
		if Choice.get("finish_reason"):
			State["finish"] = Choice["finish_reason"]
		if not State["started"]:
			yield _Start(State)
			State["started"] = True
		Text = Delta.get("content")
		if Text:
			if State["text_index"] is None:
				State["text_index"] = State["next"]
				State["next"] += 1
				State["order"].append(State["text_index"])
				yield common.SSEEvent("content_block_start", {"type": "content_block_start", "index": State["text_index"], "content_block": {"type": "text", "text": ""}})
			yield common.SSEEvent("content_block_delta", {"type": "content_block_delta", "index": State["text_index"], "delta": {"type": "text_delta", "text": Text}})
		for ToolCall in Delta.get("tool_calls") or []:
			Key = ToolCall.get("index", 0)
			Function = ToolCall.get("function") or {}
			if Key not in State["tools"]:
				Index = State["next"]
				State["next"] += 1
				State["tools"][Key] = Index
				State["order"].append(Index)
				yield common.SSEEvent("content_block_start", {"type": "content_block_start", "index": Index, "content_block": {"type": "tool_use", "id": ToolCall.get("id") or common.NewID("toolu"), "name": Function.get("name") or "", "input": {}}})
			if Function.get("arguments"):
				yield common.SSEEvent("content_block_delta", {"type": "content_block_delta", "index": State["tools"][Key], "delta": {"type": "input_json_delta", "partial_json": Function["arguments"]}})
	if not State["started"]:
		yield _Start(State)
		State["started"] = True
	for Index in State["order"]:
		yield common.SSEEvent("content_block_stop", {"type": "content_block_stop", "index": Index})
	yield common.SSEEvent("message_delta", {"type": "message_delta", "delta": {"stop_reason": _StopReason(State["finish"]), "stop_sequence": None}, "usage": {"output_tokens": State["completion"]}})
	yield common.SSEEvent("message_stop", {"type": "message_stop"})


def _Start(State):
	"""Anthropic 流的第一个事件必须是 message_start。"""
	return common.SSEEvent("message_start", {"type": "message_start", "message": {"id": State["id"] or common.NewID("msg"), "type": "message", "role": "assistant", "model": State["model"], "content": [], "stop_reason": None, "stop_sequence": None, "usage": {"input_tokens": State["prompt"], "output_tokens": 0}}})
