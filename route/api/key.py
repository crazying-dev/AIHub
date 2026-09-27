"""个人密钥管理接口。

- POST /api/key/new    : 新建密钥（可带 {"canuse": [私有 key id...]} 指定授权范围，缺省 = 本人私有库全部）
- POST /api/key/list   : 密钥列表（含授权范围）
- POST /api/key/scope  : 修改某条密钥的授权范围
- POST /api/key/get    : 兼容旧接口，只返回 ah-xxxx 字符串列表
- POST /api/key/delete : 吊销密钥
"""
from route.app import *
import KeyAction
from route.api.Common import Text, TextList, UserID


@app.route('/api/key/new', methods=["POST"])
def KeyNew():
	"""新建个人密钥；body 可选 {"canuse": [...]}，空 = 可以使用本人私有库全部 key"""
	UID = UserID()
	if UID is None:
		return "Error", 401
	Data = flask.request.get_json(silent=True) or {}
	KeyAction.NewKey(UID, TextList(Data.get("canuse")))
	return "OK"


@app.route('/api/key/list', methods=["POST"])
def KeyList():
	"""当前用户的密钥列表（含授权范围）"""
	UID = UserID()
	if UID is None:
		return "Error", 401
	return flask.jsonify(KeyAction.ListKeys(UID))


@app.route('/api/key/scope', methods=["POST"])
def KeyScope():
	"""修改某条密钥的授权范围；body {"key": "ah-xxx", "canuse": [私有 key id...]}，空 = 全部"""
	UID = UserID()
	if UID is None:
		return "Error", 401
	Data = flask.request.get_json(silent=True) or {}
	Key = Text(Data.get("key") or Data.get("id"))
	if not Key:
		return flask.jsonify({"error": "缺少 key"}), 400
	if not KeyAction.SetKeyScope(UID, Key, TextList(Data.get("canuse"))):
		return flask.jsonify({"error": "没有找到这个密钥"}), 404
	return "OK"


@app.route('/api/key/delete', methods=["POST"])
def KeyDelete():
	"""吊销（删除）自己创建的个人密钥，body 传 {"key": "ah-xxxx"}"""
	UID = UserID()
	if UID is None:
		return "Error", 401
	Data = flask.request.get_json(silent=True) or {}
	Key = Text(Data.get("key") or Data.get("id"))
	if not Key:
		return flask.jsonify({"error": "缺少 key"}), 400
	if not KeyAction.DeleteKey(UID, Key):
		return flask.jsonify({"error": "没有找到这个密钥"}), 404
	return "OK"


@app.route('/api/key/get', methods=["POST"])
def KeyGet():
	"""兼容旧接口：只返回 ah-xxxx 字符串列表"""
	UID = UserID()
	if UID is None:
		return "Error", 401
	return flask.jsonify(KeyAction.Get(UID))
