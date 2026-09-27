from route.app import *
import database
import KeyAction

@app.route('/api/key/new', methods=["POST"])
def KeyNew():
	UserID = flask.request.cookies.get("id") or flask.request.cookies.get("ID")
	UserToken = flask.request.cookies.get("token")
	if not database.user.verify.verifyUser_UserID___UserToken(UserID, UserToken):
		return "Error", 401
	else:
		KeyAction.NewKey(UserID)
		return "OK"

@app.route('/api/key/delete', methods=["POST"])
def KeyDelete():
	"""吊销（删除）自己创建的个人密钥，body 传 {"key": "ah-xxxx"}"""
	UserID = flask.request.cookies.get("id") or flask.request.cookies.get("ID")
	UserToken = flask.request.cookies.get("token")
	if not database.user.verify.verifyUser_UserID___UserToken(UserID, UserToken):
		return "Error", 401
	Data = flask.request.get_json(silent=True) or {}
	Key = str(Data.get("key") or Data.get("id") or "").strip()
	if not Key:
		return flask.jsonify({"error": "缺少 key"}), 400
	if not KeyAction.DeleteKey(UserID, Key):
		return flask.jsonify({"error": "没有找到这个密钥"}), 404
	return "OK"


@app.route('/api/key/get', methods=["POST"])
def KeyGet():
	cookies = flask.request.cookies
	UserToken = cookies.get("token")
	UserID = cookies.get("id") or cookies.get("ID")
	if not database.user.verify.verifyUser_UserID___UserToken(UserID, UserToken):
		return "Error", 401
	else:
		return flask.jsonify(KeyAction.Get(UserID))

