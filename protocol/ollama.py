"""Ollama 协议适配：目前只作为入站协议（/api/chat、/api/generate、/api/tags）。

Ollama 和 OpenAI 的差别：
- 传输用 NDJSON（每行一个 JSON）而不是 SSE；
- /api/chat 的出参是 {"message": {...}, "done": bool}，/api/generate 是 {"response": "..."}；
- 采样参数放在 options 里（temperature / top_p / num_predict / stop）；
- 工具调用的 arguments 是对象，不是 JSON 字符串。
"""
import time

from protocol import common

NAME = "ollama"

# canonical 的 finish_reason -> Ollama 的 done_reason
DONE_REASONS = {
	"stop": "stop",
	"length": "length",
	"tool_calls": "stop",
	"content_filter": "stop",
}


def _Now() -> str:
	"""Ollama 的 created_at 是 RFC3339 时间串。"""
	return time.strftime("%Y-%m-%dT%H:%M:%S.000000Z", time.gmtime())


def _ModelName(Name) -> str:
	"""Ollama 的模型名习惯带 :latest 后缀，没有标签的补一个。"""
	Name = str(Name or "")
	return Name if ":" in Name else Name + ":latest"


def _Parts(Content, Images=None):
	"""Ollama 的 content（str 或 parts）+ images -> canonical parts。"""
	Parts = []
	if isinstance(Content, str):
		if Content:
			Parts.append({"type": "text", "text": Content})
	elif isinstance(Content, list):
		for Part in Content:
			if isinstance(Part, str):
				Parts.append({"type": "text", "text": Part})
			elif isinstance(Part, dict) and Part.get("type") in (None, "text"):
				if Part.get("text"):
					Parts.append({"type": "text", "text": Part["text"]})
	for Image in Images or []:
		Parts.append({"type": "image", "media_type": "image/png", "data": Image})
	return Parts


def _Tools(Tools):
	"""Ollama 的 tool 定义（就是 OpenAI 的 function 结构）-> canonical 的 tool 定义。"""
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


def _Calls(Calls):
	"""Ollama 的 tool_calls（arguments 是对象）-> canonical 的 tool_calls（arguments 是字符串）。"""
	Result = []
	for Call in Calls or []:
		Function = Call.get("function") or {}
		Result.append({
			"id": Call.get("id") or common.NewID("call"),
			"name": Function.get("name"),
			"arguments": common.Dumps(Function.get("arguments") or {}),
		})
	return Result


def _OllamaCalls(Calls):
	"""canonical 的 tool_calls -> Ollama 的 tool_calls（arguments 还原成对象）。"""
	Result = []
	for Call in Calls or []:
		Function = Call.get("function") or {}
		Result.append({
			"function": {
				"name": Function.get("name"),
				"arguments": common.Loads(Function.get("arguments")),
			},
		})
	return Result


def _Options(Body):
	"""Ollama 的 options -> canonical 的采样参数。"""
	Options = Body.get("options") or {}
	Stop = Options.get("stop")
	if isinstance(Stop, str):
		Stop = [Stop]
	return {
		"temperature": Options.get("temperature"),
		"top_p": Options.get("top_p"),
		"max_tokens": Options.get("num_predict"),
		"stop": Stop,
	}


def _Canonical(Body, Messages, System) -> dict:
	Options = _Options(Body)
	return {
		"model": Body.get("model"),
		"system": System or None,
		"messages": Messages,
		"temperature": Options["temperature"],
		"top_p": Options["top_p"],
		"max_tokens": Options["max_tokens"],
		"stop": Options["stop"],
		"stream": bool(Body.get("stream", True)),
		"tools": _Tools(Body.get("tools")),
		"tool_choice": None,
		"raw": Body,
	}


def ParseRequest(Body) -> dict:
	"""入站：Ollama /api/chat 请求体 -> canonical request。"""
	System = []
	Messages = []
	for Message in Body.get("messages") or []:
		if not isinstance(Message, dict):
			continue
		Role = str(Message.get("role") or "user").lower()
		if Role == "system":
			Text = common.AsText(Message.get("content"))
			if Text:
				System.append(Text)
			continue
		if Role == "tool":
			Messages.append({
				"role": "tool",
				"tool_call_id": Message.get("tool_call_id") or Message.get("name"),
				"content": _Parts(Message.get("content")),
			})
			continue
		Item = {
			"role": "assistant" if Role == "assistant" else "user",
			"content": _Parts(Message.get("content"), Message.get("images")),
		}
		Calls = _Calls(Message.get("tool_calls"))
		if Calls:
			Item["tool_calls"] = Calls
		Messages.append(Item)
	return _Canonical(Body, Messages, "\n".join(System))


def ParseGenerate(Body) -> dict:
	"""入站：Ollama /api/generate 请求体 -> canonical request。"""
	System = common.AsText(Body.get("system"))
	Messages = [{"role": "user", "content": _Parts(Body.get("prompt"), Body.get("images"))}]
	return _Canonical(Body, Messages, System)


def _Durations():
	"""上游耗时没有单独计时，给 0（客户端只拿它做展示）。"""
	return {"total_duration": 0, "load_duration": 0, "prompt_eval_duration": 0, "eval_duration": 0}


def _Counts(Response):
	Usage = Response.get("usage") or {}
	return {
		"prompt_eval_count": Usage.get("prompt_tokens") or 0,
		"eval_count": Usage.get("completion_tokens") or 0,
	}


def RenderResponse(Response, Request) -> dict:
	"""canonical response -> Ollama /api/chat 响应体。"""
	Choice = (Response.get("choices") or [{}])[0]
	Message = Choice.get("message") or {}
	Result = {
		"model": Response.get("model") or Request.get("model"),
		"created_at": _Now(),
		"message": {"role": "assistant", "content": Message.get("content") or ""},
		"done": True,
		"done_reason": DONE_REASONS.get(Choice.get("finish_reason"), "stop"),
	}
	Calls = _OllamaCalls(Message.get("tool_calls"))
	if Calls:
		Result["message"]["tool_calls"] = Calls
	Result.update(_Counts(Response))
	Result.update(_Durations())
	return Result


def RenderGenerate(Response, Request) -> dict:
	"""canonical response -> Ollama /api/generate 响应体。"""
	Choice = (Response.get("choices") or [{}])[0]
	Message = Choice.get("message") or {}
	Result = {
		"model": Response.get("model") or Request.get("model"),
		"created_at": _Now(),
		"response": Message.get("content") or "",
		"done": True,
		"done_reason": DONE_REASONS.get(Choice.get("finish_reason"), "stop"),
	}
	Result.update(_Counts(Response))
	Result.update(_Durations())
	return Result


def _Line(Data) -> str:
	"""Ollama 的一帧：一行 JSON。"""
	return common.Dumps(Data) + "\n"


def _Stream(Chunks, Request, Generate=False):
	"""canonical 分片 -> Ollama 的 NDJSON 流；工具调用集中在最后一行。"""
	Model = Request.get("model")
	Prompt = 0
	Completion = 0
	Finish = None
	Calls = []
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
		if Delta.get("tool_calls"):
			Calls.extend(_OllamaCalls(Delta["tool_calls"]))
		Text = Delta.get("content")
		if Text:
			if Generate:
				yield _Line({"model": Model, "created_at": _Now(), "response": Text, "done": False})
			else:
				yield _Line({"model": Model, "created_at": _Now(), "message": {"role": "assistant", "content": Text}, "done": False})
	Last = {
		"model": Model,
		"created_at": _Now(),
		"done": True,
		"done_reason": DONE_REASONS.get(Finish, "stop"),
		"prompt_eval_count": Prompt,
		"eval_count": Completion,
	}
	Last.update(_Durations())
	Last["response" if Generate else "message"] = "" if Generate else {"role": "assistant", "content": ""}
	if not Generate and Calls:
		Last["message"]["tool_calls"] = Calls
	yield _Line(Last)


def RenderStream(Chunks, Request):
	"""/api/chat 的 NDJSON 流。"""
	return _Stream(Chunks, Request, Generate=False)


def RenderGenerateStream(Chunks, Request):
	"""/api/generate 的 NDJSON 流。"""
	return _Stream(Chunks, Request, Generate=True)


def RenderTags(Names):
	"""GET /api/tags：把可用模型名包装成 Ollama 的模型列表。"""
	Models = []
	for Name in Names:
		Full = _ModelName(Name)
		Models.append({
			"name": Full,
			"model": Full,
			"modified_at": _Now(),
			"size": 0,
			"digest": "",
			"details": {
				"format": "aihub",
				"family": "aihub",
				"families": None,
				"parameter_size": "",
				"quantization_level": "",
			},
		})
	return {"models": Models}


def RenderVersion():
	"""GET /api/version：给一个不算旧的版本号，避免客户端判定能力不足。"""
	return {"version": "0.6.2-aihub"}


def RenderShow(Model):
	"""POST /api/show：客户端只关心能否拿到基本信息。"""
	return {
		"license": "",
		"modelfile": "# AIHub 中继模型：" + str(Model or ""),
		"parameters": "",
		"template": "",
		"details": {
			"format": "aihub",
			"family": "aihub",
			"families": None,
			"parameter_size": "",
			"quantization_level": "",
		},
		"model_info": {},
		"capabilities": ["completion", "tools"],
	}