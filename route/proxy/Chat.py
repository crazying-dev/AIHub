"""OpenAI / Anthropic 兼容的对话与补全（真正的中继实现）。

- POST /v1/chat/completions       : OpenAI Chat Completions 入站
- POST /v1/completions            : OpenAI Completions（legacy）入站
- POST /v1/messages               : Anthropic Messages 入站
- POST /v1/messages/count_tokens  : Anthropic 令牌计数（本地估算）
- GET  /v1/models                 : 当前调用方可用的模型标识

鉴权：Authorization: Bearer <key>（Anthropic 入站也接受 x-api-key）。两种 key：
- 字面量 ah-xxxx：走公共库（社区池 otherkey），任何人都能用，不需要注册；
- 个人密钥 ah-<id>：只走本人私有库（privatekey），且受该密钥的 canuse 白名单约束。

路由：model=auto 时选优先级最高的可用 key；填具体模型名时先按上游 model 名匹配，
      全都匹配不上，再按上传者给 key 起的 name 兜底。
"""
from route.app import *
import protocol
import Relay
from protocol import common
from route.proxy.Common import (
	AnthropicError,
	Authenticate,
	Body,
	Guard,
	NeedMessages,
	OpenAIError,
	Parse,
	Respond,
)


@app.route("/v1/chat/completions", methods=["POST"], strict_slashes=False)
@Guard(OpenAIError)
def ChatCompletions():
	"""OpenAI Chat Completions 协议入站"""
	Caller = Authenticate()
	Adapter = protocol.Inbound("openai")
	Request = NeedMessages(Parse(Adapter, Body()))
	return Respond(Caller, Adapter, Request)


@app.route("/v1/completions", methods=["POST"], strict_slashes=False)
@Guard(OpenAIError)
def Completions():
	"""OpenAI Completions（legacy）协议入站"""
	Caller = Authenticate()
	Adapter = protocol.Inbound("openai")
	Request = NeedMessages(Parse(Adapter, Body(), Parser="ParseCompletionRequest"))
	return Respond(
		Caller,
		Adapter,
		Request,
		Render=Adapter.RenderCompletion,
		StreamRender=Adapter.RenderCompletionStream,
	)


@app.route("/v1/messages", methods=["POST"], strict_slashes=False)
@Guard(AnthropicError)
def Messages():
	"""Anthropic Messages 协议入站"""
	Caller = Authenticate()
	Adapter = protocol.Inbound("anthropic")
	Request = NeedMessages(Parse(Adapter, Body()))
	return Respond(Caller, Adapter, Request)


@app.route("/v1/messages/count_tokens", methods=["POST"], strict_slashes=False)
@Guard(AnthropicError)
def CountTokens():
	"""
	Anthropic 的令牌计数。

	AIHub 是中继，上游协议各不相同，没有统一的分词器，所以这里返回本地估算值
	（见 protocol/common.py 的 EstimateTokens），够客户端做上下文预算用。
	"""
	Authenticate()
	Adapter = protocol.Inbound("anthropic")
	Request = Parse(Adapter, Body())
	return flask.jsonify({"input_tokens": common.EstimateTokens(Request)})


@app.route("/v1/models", methods=["GET"], strict_slashes=False)
@Guard(OpenAIError)
def Models():
	"""当前调用方（公共库 / 私有库）可用的模型标识（含 auto）"""
	Caller = Authenticate()
	Data = [{"id": Name, "object": "model", "created": 0, "owned_by": "aihub"} for Name in Relay.Models(Caller)]
	return flask.jsonify({"object": "list", "data": Data})