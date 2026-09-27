"""社区 key 管理接口：任何登录用户都可以上传自己的上游 key 到社区池。

- POST /api/community/upload : 上传，返回可直接使用的 ah-xxxx
- POST /api/community/list   : 当前用户上传的 key 列表（上游密钥已打码）
- POST /api/community/delete : 删除自己上传的 key
"""
from route.app import *
import database
import KeyAction
import protocol


def _UserID():
	"""从 Cookie 取登录态，校验通过返回 UserID，否则 None"""
	Cookies = flask.request.cookies
	UserID = Cookies.get("id") or Cookies.get("ID")
	UserToken = Cookies.get("token")
	if not UserID or not UserToken:
		return None
	if not database.user.verify.verifyUser_UserID___UserToken(UserID, UserToken):
		return None
	return UserID


def _Int(Value, Default=None):
	"""把前端传来的字符串/数字转成 int，非法就返回默认值"""
	if Value is None or Value == "":
		return Default
	try:
		return int(Value)
	except (TypeError, ValueError):
		return Default


def _Text(Value):
	Text = str(Value).strip() if Value is not None else ""
	return Text or None


@app.route("/api/community/upload", methods=["POST"])
def CommunityUpload():
	UserID = _UserID()
	if UserID is None:
		return "Error", 401
	Data = flask.request.get_json(silent=True) or {}
	URL = _Text(Data.get("url"))
	Key = _Text(Data.get("key"))
	Model = _Text(Data.get("model"))
	if not (URL and Key and Model):
		return flask.jsonify({"error": "url / key / model 均为必填"}), 400
	Protocol = protocol.Normalize(Data.get("protocol") or "openai")
	if Protocol not in protocol.UPSTREAM:
		return flask.jsonify({"error": "protocol 只支持 openai / anthropic / gemini"}), 400
	Priority = _Int(Data.get("priority"), 50)
	MaxUse = _Int(Data.get("maxuse"), None)
	if MaxUse is not None and MaxUse < 0:
		return flask.jsonify({"error": "maxuse 不能为负数"}), 400
	if Priority is None:
		Priority = 50
	APIKey = KeyAction.NewCommunityKey(UserID, URL, Key, Protocol, Model, _Text(Data.get("name")), Priority, MaxUse, _Text(Data.get("text")))
	return flask.jsonify({"key": APIKey})


@app.route("/api/community/list", methods=["POST"])
def CommunityList():
	UserID = _UserID()
	if UserID is None:
		return "Error", 401
	return flask.jsonify(KeyAction.GetCommunityKeys(UserID))


@app.route("/api/community/delete", methods=["POST"])
def CommunityDelete():
	UserID = _UserID()
	if UserID is None:
		return "Error", 401
	Data = flask.request.get_json(silent=True) or {}
	KeyID = _Text(Data.get("id"))
	if not KeyID:
		return flask.jsonify({"error": "缺少 id"}), 400
	if not KeyAction.DeleteCommunityKey(UserID, KeyID):
		return flask.jsonify({"error": "没有找到这条 key"}), 404
	return "OK"
