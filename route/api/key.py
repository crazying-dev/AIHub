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

@app.route('/api/key/get', methods=["POST"])
def KeyGet():
	cookies = flask.request.cookies
	UserToken = cookies.get("token")
	UserID = cookies.get("id") or cookies.get("ID")
	if not database.user.verify.verifyUser_UserID___UserToken(UserID, UserToken):
		return "Error", 401
	else:
		return flask.jsonify(KeyAction.Get(UserID))

