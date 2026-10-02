"""OpenAI Embeddings 入站：POST /v1/embeddings。

embeddings 没有 canonical 环节（那是给对话用的），这里按 model 挑一条 openai 协议的上游 key 直接转发。
"""
from route.app import *
import Relay
from route.proxy.Common import Authenticate, Body, Failure, Guard, Headers, JSON, OpenAIError


@app.route("/v1/embeddings", methods=["POST"], strict_slashes=False)
@Guard(OpenAIError)
def Embeddings():
	"""OpenAI Embeddings 协议入站"""
	Caller = Authenticate()
	Data = Body()
	if Data.get("model") is None:
		raise Failure("model 不能为空", 400)
	if Data.get("input") in (None, "", []):
		raise Failure("input 不能为空", 400)
	try:
		Result, Row = Relay.Embed(Data, Data.get("model"), Caller)
	except Relay.NoKeyError as Error:
		raise Failure(str(Error), 503, "no_available_key", "no_available_key")
	except Relay.UpstreamError as Error:
		raise Failure(str(Error), 502, "upstream_error", "upstream_error")
	Payload = Result if isinstance(Result, dict) else {}
	Payload.setdefault("object", "list")
	Payload.setdefault("model", Row["model"])
	return JSON(Payload, Headers(Row))