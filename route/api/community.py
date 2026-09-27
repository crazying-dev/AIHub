"""公共库（社区池）管理接口：任何登录用户都可以上传自己的上游 key 到公共库。

公共库统一用字面量 ah-xxxx 调用，不需要注册、也不需要新建个人密钥。

- POST /api/community/upload : 上传，返回 {"key": "ah-<id>"}（历史凭证，等价于公共库中的这一条）
- POST /api/community/pool   : 公共库全部条目（公开浏览，不需要登录）
- POST /api/community/list   : 当前用户上传的 key 列表（上游密钥已打码）
- POST /api/community/delete : 删除自己上传的 key
"""
from route.app import *
import KeyAction
import protocol
from route.api.Common import Int, Text, UserID


@app.route("/api/community/upload", methods=["POST"])
def CommunityUpload():
	UID = UserID()
	if UID is None:
		return "Error", 401
	Data = flask.request.get_json(silent=True) or {}
	URL = Text(Data.get("url"))
	Key = Text(Data.get("key"))
	Model = Text(Data.get("model"))
	if not (URL and Key and Model):
		return flask.jsonify({"error": "url / key / model 均为必填"}), 400
	Protocol = protocol.Normalize(Data.get("protocol") or "openai")
	if Protocol not in protocol.UPSTREAM:
		return flask.jsonify({"error": "protocol 只支持 openai / anthropic / gemini"}), 400
	Priority = Int(Data.get("priority"), 50)
	MaxUse = Int(Data.get("maxuse"), None)
	if MaxUse is not None and MaxUse < 0:
		return flask.jsonify({"error": "maxuse 不能为负数"}), 400
	if Priority is None:
		Priority = 50
	APIKey = KeyAction.NewCommunityKey(UID, URL, Key, Protocol, Model, Text(Data.get("name")), Priority, MaxUse, Text(Data.get("text")))
	return flask.jsonify({"key": APIKey})


@app.route("/api/community/pool", methods=["POST"])
def CommunityPool():
	"""公共库全部条目，公开可浏览（不需要登录）；登录用户自己的条目标记 mine=true"""
	return flask.jsonify(KeyAction.GetCommunityPool(UserID()))


@app.route("/api/community/list", methods=["POST"])
def CommunityList():
	UID = UserID()
	if UID is None:
		return "Error", 401
	return flask.jsonify(KeyAction.GetCommunityKeys(UID))


@app.route("/api/community/delete", methods=["POST"])
def CommunityDelete():
	UID = UserID()
	if UID is None:
		return "Error", 401
	Data = flask.request.get_json(silent=True) or {}
	KeyID = Text(Data.get("id"))
	if not KeyID:
		return flask.jsonify({"error": "缺少 id"}), 400
	if not KeyAction.DeleteCommunityKey(UID, KeyID):
		return flask.jsonify({"error": "没有找到这条 key"}), 404
	return "OK"
