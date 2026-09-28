"""OpenAI Responses API 适配：目前只作为入站协议（POST /v1/responses）。

和 Chat Completions 的区别：
- 入参是 input + instructions（不是 messages）；input 可以是字符串，也可以是 item 列表；
- 出参是 output item 列表（message / function_call），不是 choices；
- 流式事件带事件名（response.output_text.delta 等），不是只有 data 行的 SSE。

canonical 仍然是 chat 那一套，这里只做两头的形状转换。
"""
from protocol import common

NAME = "responses"


def _Parts(Content):
	"""Responses 的 content（str 或 [{type}]）-> canonical parts。"""
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
		if Type in (None, "input_text", "output_text", "text", "summary_text"):
			if Part.get("text"):
				Parts.append({"type": "text", "text": Part["text"]})
		elif Type in ("input_image", "image_url"):
			Image = Part.get("image_url") or Part.get("image")
			Url = Image.get("url") if isinstance(Image, dict) else Image
			Parts.append({"type": "image", "url": Url})
		else:
			Parts.append(dict(Part))
	return Parts


def _Tools(Tools):
	"""Responses 的 tool 定义（扁平结构）-> canonical 的 tool 定义。"""
	if not Tools:
		return None
	Result = []
	for Tool in Tools:
		if not isinstance(Tool, dict):
			continue
		Function = Tool.get("function") or Tool
		if not Function.get("name"):
			continue
		Result.append({
			"name": Function.get("name"),
			"description": Function.get("description"),
			"parameters": Function.get("parameters"),
		})
	return Result or None


def _InputItems(Input):
	"""Responses 的 input -> canonical messages（system/developer 会被提到 instructions）。"""
	System = []
	Messages = []
	if Input is None:
		return System, Messages
	if isinstance(Input, str):
		return System, [{"role": "user", "content": [{"type": "text", "text": Input}]}]
	for Item in Input:
		if isinstance(Item, str):
			Messages.append({"role": "user", "content": [{"type": "text", "text": Item}]})
			continue
		if not isinstance(Item, dict):
			continue
		Type = Item.get("type") or "message"
		if Type == "function_call":
			Messages.append({
				"role": "assistant",
				"content": [],
				"tool_calls": [{
					"id": Item.get("call_id") or Item.get("id"),
					"name": Item.get("name"),
					"arguments": Item.get("arguments") or "",
				}],
			})
			continue
		if Type == "function_call_output":
			Messages.append({
				"role": "tool",
				"tool_call_id": Item.get("call_id"),
				"content": [{"type": "text", "text": common.AsText(Item.get("output"))}],
			})
			continue
		if Type in ("reasoning", "item_reference"):
			continue
		Role = str(Item.get("role") or "user").lower()
		if Role in ("system", "developer"):
			Text = common.AsText(Item.get("content"))
			if Text:
				System.append(Text)
			continue
		if Role == "tool":
			Messages.append({"role": "tool", "tool_call_id": Item.get("tool_call_id"), "content": _Parts(Item.get("content"))})
			continue
		Message = {"role": "assistant" if Role == "assistant" else "user", "content": _Parts(Item.get("content"))}
		for Call in Item.get("tool_calls") or []:
			Function = Call.get("function") or {}
			Message.setdefault("tool_calls", []).append({
				"id": Call.get("id"),
				"name": Function.get("name"),
				"arguments": Function.get("arguments") or "",
			})
		Messages.append(Message)
	return System, Messages


def _FromMessages(Messages):
	"""兜底：有些客户端把 chat 风格的 messages 直接丢过来。"""
	System = []
	Items = []
	for Message in Messages or []:
		if not isinstance(Message, dict):
			continue
		Role = str(Message.get("role") or "user").lower()
		if Role in ("system", "developer"):
			Text = common.AsText(Message.get("content"))
			if Text:
				System.append(Text)
			continue
		if Role == "tool":
			Items.append({"role": "tool", "tool_call_id": Message.get("tool_call_id"), "content": _Parts(Message.get("content"))})
			continue
		Item = {"role": "assistant" if Role == "assistant" else "user", "content": _Parts(Message.get("content"))}
		for Call in Message.get("tool_calls") or []:
			Function = Call.get("function") or {}
			Item.setdefault("tool_calls", []).append({
				"id": Call.get("id"),
				"name": Function.get("name"),
				"arguments": Function.get("arguments") or "",
			})
		Items.append(Item)
	return System, Items


def ParseRequest(Body) -> dict:
	"""入站：Responses /v1/responses 请求体 -> canonical request。"""
	System = []
	if Body.get("instructions"):
		System.append(common.AsText(Body.get("instructions")))
	Extra, Messages = _InputItems(Body.get("input"))
	System.extend(Extra)
	if not Messages and Body.get("messages"):
		Extra, Messages = _FromMessages(Body.get("messages"))
		System.extend(Extra)
	return {
		"model": Body.get("model"),
		"system": "\n".join(Text for Text in System if Text) or None,
		"messages": Messages,
		"temperature": Body.get("temperature"),
		"top_p": Body.get("top_p"),
		"max_tokens": Body.get("max_output_tokens") or Body.get("max_tokens"),
		"stop": None,
		"stream": bool(Body.get("stream")),
		"tools": _Tools(Body.get("tools")),
		"tool_choice": Body.get("tool_choice"),
		"raw": Body,
	}


def _MessageItem(ItemID, Text, Status):
	"""Responses 的 message item。"""
	Content = [] if Status == "in_progress" else [{"type": "output_text", "text": Text, "annotations": []}]
	return {"type": "message", "id": ItemID, "role": "assistant", "status": Status, "content": Content}


def _CallItem(Info, Status):
	"""Responses 的 function_call item。"""
	return {
		"type": "function_call",
		"id": Info["item_id"],
		"call_id": Info["call_id"],
		"name": Info["name"],
		"arguments": Info["arguments"],
		"status": Status,
	}


def RenderResponse(Response, Request) -> dict:
	"""canonical response -> Responses 的响应体。"""
	Choice = (Response.get("choices") or [{}])[0]
	Message = Choice.get("message") or {}
	Text = Message.get("content") or ""
	Output = []
	for Call in Message.get("tool_calls") or []:
		Function = Call.get("function") or {}
		Output.append({
			"type": "function_call",
			"id": common.NewID("fc"),
			"call_id": Call.get("id") or common.NewID("call"),
			"name": Function.get("name"),
			"arguments": Function.get("arguments") or "",
			"status": "completed",
		})
	if Text or not Output:
		Output.append(_MessageItem(common.NewID("msg"), Text, "completed"))
	Usage = Response.get("usage") or {}
	Prompt = Usage.get("prompt_tokens") or 0
	Completion = Usage.get("completion_tokens") or 0
	return {
		"id": Response.get("id") or common.NewID("resp"),
		"object": "response",
		"created_at": Response.get("created") or common.Now(),
		"status": "completed",
		"model": Response.get("model") or Request.get("model"),
		"output": Output,
		"parallel_tool_calls": True,
		"tools": [],
		"usage": {"input_tokens": Prompt, "output_tokens": Completion, "total_tokens": Prompt + Completion},
		"error": None,
		"incomplete_details": {"reason": "max_output_tokens"} if Choice.get("finish_reason") == "length" else None,
		"instructions": Request.get("system"),
		"metadata": {},
	}


def RenderStream(Chunks, Request):
	"""canonical 分片 -> Responses 的带事件名 SSE 文本。"""
	ResponseID = common.NewID("resp")
	MessageID = common.NewID("msg")
	Created = common.Now()
	Model = Request.get("model")
	Text = []
	TextIndex = None
	Tools = {}
	Order = []
	Finish = None
	Prompt = 0
	Completion = 0

	def Output(Status):
		Items = []
		for Kind, Key in Order:
			if Kind == "text":
				Items.append(_MessageItem(MessageID, "".join(Text), Status))
			else:
				Items.append(_CallItem(Tools[Key], Status))
		return Items

	def Response(Status):
		Data = {
			"id": ResponseID,
			"object": "response",
			"created_at": Created,
			"status": Status,
			"model": Model,
			"output": Output(Status),
			"parallel_tool_calls": True,
			"tools": [],
			"error": None,
			"incomplete_details": {"reason": "max_output_tokens"} if (Status == "completed" and Finish == "length") else None,
			"instructions": Request.get("system"),
			"metadata": {},
		}
		if Status == "in_progress":
			Data["usage"] = None
		else:
			Data["usage"] = {"input_tokens": Prompt, "output_tokens": Completion, "total_tokens": Prompt + Completion}
		return Data

	def StartText():
		return [
			("response.output_item.added", {"type": "response.output_item.added", "output_index": TextIndex, "item": _MessageItem(MessageID, "", "in_progress")}),
			("response.content_part.added", {"type": "response.content_part.added", "item_id": MessageID, "output_index": TextIndex, "content_index": 0, "part": {"type": "output_text", "text": "", "annotations": []}}),
		]

	yield common.SSEEvent("response.created", {"type": "response.created", "response": Response("in_progress")})
	yield common.SSEEvent("response.in_progress", {"type": "response.in_progress", "response": Response("in_progress")})
	for Data in Chunks:
		Choice = (Data.get("choices") or [{}])[0]
		Delta = Choice.get("delta") or {}
		Usage = Data.get("usage") or {}
		if Usage.get("prompt_tokens"):
			Prompt = Usage["prompt_tokens"]
		if Usage.get("completion_tokens"):
			Completion = Usage["completion_tokens"]
		if Choice.get("finish_reason"):
			Finish = Choice["finish_reason"]
		Chunk = Delta.get("content")
		if Chunk:
			if TextIndex is None:
				TextIndex = len(Order)
				Order.append(("text", None))
				for Event, Payload in StartText():
					yield common.SSEEvent(Event, Payload)
			Text.append(Chunk)
			yield common.SSEEvent("response.output_text.delta", {"type": "response.output_text.delta", "item_id": MessageID, "output_index": TextIndex, "content_index": 0, "delta": Chunk})
		for Call in Delta.get("tool_calls") or []:
			Key = Call.get("index", 0)
			Function = Call.get("function") or {}
			Info = Tools.get(Key)
			if Info is None:
				Info = {
					"item_id": common.NewID("fc"),
					"call_id": Call.get("id") or common.NewID("call"),
					"name": Function.get("name") or "",
					"arguments": "",
					"index": len(Order),
				}
				Tools[Key] = Info
				Order.append(("tool", Key))
				yield common.SSEEvent("response.output_item.added", {"type": "response.output_item.added", "output_index": Info["index"], "item": _CallItem(Info, "in_progress")})
			if Function.get("name") and not Info["name"]:
				Info["name"] = Function["name"]
			if Function.get("arguments"):
				Info["arguments"] += Function["arguments"]
				yield common.SSEEvent("response.function_call_arguments.delta", {"type": "response.function_call_arguments.delta", "item_id": Info["item_id"], "output_index": Info["index"], "delta": Function["arguments"]})
	if not Order:
		TextIndex = 0
		Order.append(("text", None))
		for Event, Payload in StartText():
			yield common.SSEEvent(Event, Payload)
	for Index, (Kind, Key) in enumerate(Order):
		if Kind == "text":
			Full = "".join(Text)
			yield common.SSEEvent("response.output_text.done", {"type": "response.output_text.done", "item_id": MessageID, "output_index": Index, "content_index": 0, "text": Full})
			yield common.SSEEvent("response.content_part.done", {"type": "response.content_part.done", "item_id": MessageID, "output_index": Index, "content_index": 0, "part": {"type": "output_text", "text": Full, "annotations": []}})
			yield common.SSEEvent("response.output_item.done", {"type": "response.output_item.done", "output_index": Index, "item": _MessageItem(MessageID, Full, "completed")})
		else:
			Info = Tools[Key]
			yield common.SSEEvent("response.function_call_arguments.done", {"type": "response.function_call_arguments.done", "item_id": Info["item_id"], "output_index": Index, "arguments": Info["arguments"]})
			yield common.SSEEvent("response.output_item.done", {"type": "response.output_item.done", "output_index": Index, "item": _CallItem(Info, "completed")})
	yield common.SSEEvent("response.completed", {"type": "response.completed", "response": Response("completed")})