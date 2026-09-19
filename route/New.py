from route.app import *

@app.route("/new", methods=["POST"])
def new():
	cookies = flask.request.cookies
	Data = flask.request.get_json()
	UserToken = cookies.get("token")
	UserID = cookies.get("ID")
