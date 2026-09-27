from route.app import *
import random
import database

@app.route('/api/sign/up/1', methods=["POST"])
def SignUp1():
	email = flask.request.get_json().get('email', None)
	if email is None:
		return "Error", 401
	# 验证码固定为随机 6 位
	code = f"{random.randint(0, 999999):06d}"
	database.Email.NewEmail(email, code)
	...
	# 此处写邮箱发送逻辑
	return "OK"

@app.route('/api/sign/up/2', methods=["POST"])
def SignUp2():
	data = flask.request.get_json()
	email = data.get('email', None)
	code = data.get('code', None)
	UserName = data.get('name', None)
	UserPassword = data.get('password', None)
	if not (email and code and UserName and UserPassword):
		return "Error", 401
	if database.Email.Verify(email, code):
		database.user.NewUser(UserName, email, UserPassword)
		return "OK"
	else:
		return "Error", 401

@app.route('/api/sign', methods=["POST"])
def Sign():
	data = flask.request.get_json()
	UserEmail = data.get('email', None)
	UserPassword = data.get('password', None)
	if not (UserEmail and UserPassword):
		return "Error", 401
	if database.user.verify.verifyUser_UserEmail___UserPassword(UserEmail, UserPassword):
		resp = flask.make_response("Cookie")
		resp.set_cookie(
			key="token",
			value=database.user.get.GetToken_UserEmail___UserPassword(UserEmail, UserPassword),
			max_age=86400 * 30,
			path="/",
			httponly=True
		)
		resp.set_cookie(
			key="id",
			value=database.user.get.GetID_UserEmail___UserPassword(UserEmail, UserPassword),
			max_age=86400 * 30,
			path="/",
			httponly=True
		)
		return resp
	else:
		return "Error", 401