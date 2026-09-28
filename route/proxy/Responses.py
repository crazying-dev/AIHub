"""OpenAI Responses API 入站：POST /v1/responses（Codex CLI / 新版 OpenAI SDK 用它）。"""
from route.app import *
import protocol
from route.proxy.Common import Authenticate, Body, Guard, NeedMessages, OpenAIError, Parse, Respond


@app.route("/v1/responses", methods=["POST"])
@Guard(OpenAIError)
def Responses():
	"""OpenAI Responses API 协议入站"""
	Caller = Authenticate()
	Adapter = protocol.Inbound("responses")
	Request = NeedMessages(Parse(Adapter, Body()))
	return Respond(Caller, Adapter, Request)