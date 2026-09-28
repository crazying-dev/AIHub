"""Ollama 兼容入站。

- POST /api/chat     ：对话（NDJSON 流）
- POST /api/generate ：补全（NDJSON 流）
- GET  /api/tags     ：可用模型列表
- GET  /api/ps       ：常驻模型（中继没有常驻模型，返回空列表）
- GET  /api/version  ：版本号
- POST /api/show     ：模型详情

Ollama 客户端默认不带鉴权头，所以这里没带凭证时退回公共库（ah-xxxx）；
想让它用私有库，就在请求头带 Authorization: Bearer ah-<id>。
"""
from route.app import *
import protocol
import Relay
from route.proxy.Common import Authenticate, Body, Guard, NeedMessages, OllamaError, Parse, Respond

NDJSON = "application/x-ndjson"


@app.route("/api/chat", methods=["POST"])
@Guard(OllamaError)
def Chat():
	"""Ollama 对话协议入站"""
	Caller = Authenticate(AllowAnonymous=True)
	Adapter = protocol.Inbound("ollama")
	Request = NeedMessages(Parse(Adapter, Body()))
	return Respond(Caller, Adapter, Request, StreamMimetype=NDJSON)


@app.route("/api/generate", methods=["POST"])
@Guard(OllamaError)
def Generate():
	"""Ollama 补全协议入站"""
	Caller = Authenticate(AllowAnonymous=True)
	Adapter = protocol.Inbound("ollama")
	Request = NeedMessages(Parse(Adapter, Body(), Parser="ParseGenerate"))
	return Respond(
		Caller,
		Adapter,
		Request,
		Render=Adapter.RenderGenerate,
		StreamRender=Adapter.RenderGenerateStream,
		StreamMimetype=NDJSON,
	)


@app.route("/api/tags", methods=["GET"])
@Guard(OllamaError)
def Tags():
	"""可用模型列表"""
	Adapter = protocol.Inbound("ollama")
	return flask.jsonify(Adapter.RenderTags(Relay.Models(Authenticate(AllowAnonymous=True))))


@app.route("/api/ps", methods=["GET"])
@Guard(OllamaError)
def Ps():
	"""中继没有常驻模型，返回空列表即可（部分客户端会轮询它）。"""
	return flask.jsonify({"models": []})


@app.route("/api/version", methods=["GET"])
def Version():
	"""版本号"""
	Adapter = protocol.Inbound("ollama")
	return flask.jsonify(Adapter.RenderVersion())


@app.route("/api/show", methods=["POST"])
@Guard(OllamaError)
def Show():
	"""模型详情"""
	Adapter = protocol.Inbound("ollama")
	Data = Body()
	return flask.jsonify(Adapter.RenderShow(Data.get("model") or Data.get("name")))