"""Gemini 原生入站（Google Generative Language REST 风格）。

- GET  /v1beta/models                                ：可用模型列表
- POST /v1beta/models/{model}:generateContent        ：对话
- POST /v1beta/models/{model}:streamGenerateContent  ：对话（SSE 流）
- POST /v1beta/models/{model}:countTokens            ：令牌计数（本地估算）

鉴权：?key=<凭证>（Google 客户端的习惯）、x-goog-api-key 头，或 Authorization: Bearer。
"""
from route.app import *
import protocol
import Relay
from protocol import common
from route.proxy.Common import Authenticate, Body, Failure, GeminiError, Guard, Parse, Respond


def _Split(Rest):
	"""把 URL 里的 "models/gemini-2.0-flash:generateContent" 拆成 (模型名, 动作)。"""
	Rest = str(Rest or "").strip("/")
	Model, Separator, Action = Rest.rpartition(":")
	if not Separator:
		Model, Action = Rest, "generateContent"
	if Model.startswith("models/"):
		Model = Model[len("models/"):]
	Model = Model.strip("/")
	if not Model:
		raise Failure("路径里缺少模型名", 404)
	return Model, Action or "generateContent"


@app.route("/v1beta/models", methods=["GET"], strict_slashes=False)
@Guard(GeminiError)
def GeminiModels():
	"""可用模型列表"""
	Adapter = protocol.Inbound("gemini")
	return flask.jsonify(Adapter.RenderModels(Relay.Models(Authenticate())))


@app.route("/v1beta/models/<path:Rest>", methods=["POST"], strict_slashes=False)
@Guard(GeminiError)
def GeminiModelAction(Rest):
	"""generateContent / streamGenerateContent / countTokens"""
	Caller = Authenticate()
	Adapter = protocol.Inbound("gemini")
	Model, Action = _Split(Rest)
	if Action == "countTokens":
		Request = Parse(Adapter, Body(), Model=Model)
		return flask.jsonify(Adapter.RenderCountTokens(common.EstimateTokens(Request)))
	if Action not in ("generateContent", "streamGenerateContent"):
		raise Failure(f"不支持的模型动作：{Action}", 404)
	Request = Parse(Adapter, Body(), Model=Model, Stream=(Action == "streamGenerateContent"))
	return Respond(Caller, Adapter, Request)