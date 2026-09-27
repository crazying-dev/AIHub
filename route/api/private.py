"""私有库管理接口：登录用户上传自己的上游 key，只给自己创建的个人密钥使用。

- POST /api/private/upload : 上传，返回 {"id": ...}（私有库 id 不是凭证，不对外暴露成 ah-）
- POST /api/private/list   : 当前用户私有库全部条目（上游密钥已打码，不返回 userid）
- POST /api/private/delete : 删除自己私有库里的某条 key
"""
from route.app import *
import KeyAction
import protocol
from route.api.Common import Int, Text, UserID


@app.route("/api/private/upload", methods=["POST"])
def PrivateUpload():
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
	KeyID = KeyAction.NewPrivateKey(UID, URL, Key, Protocol, Model, Text(Data.get("name")), Priority, MaxUse, Text(Data.get("text")))
	return flask.jsonify({"id": KeyID})


@app.route("/api/private/list", methods=["POST"])
def PrivateList():
	"""当前用户私有库全部条目"""
	UID = UserID()
	if UID is None:
		return "Error", 401
	return flask.jsonify(KeyAction.GetPrivateKeys(UID))


@app.route("/api/private/delete", methods=["POST"])
def PrivateDelete():
	"""删除自己私有库里的某条 key，body 传 {"id": "..."}"""
	UID = UserID()
	if UID is None:
		return "Error", 401
	Data = flask.request.get_json(silent=True) or {}
	KeyID = Text(Data.get("id"))
	if not KeyID:
		return flask.jsonify({"error": "缺少 id"}), 400
	if not KeyAction.DeletePrivateKey(UID, KeyID):
		return flask.jsonify({"error": "没有找到这条 key"}), 404
	return "OK"
