from route.app import *
import random
import re
import time
import database
import Mail

# 同一邮箱两次发验证码的最小间隔（秒），与前端注册页的 60 秒倒计时对齐
RESEND_INTERVAL = 60

# 邮箱格式的粗校验，只用来挡住明显不是邮箱的输入；地址是否真实可达由 SMTP 服务器判断
EMAIL_RE = re.compile(r"^[^\s@]+@[^\s@]+\.[^\s@]+$")

@app.route('/api/sign/up/1', methods=["POST"])
def SignUp1():
	"""注册第一步：向邮箱发送 6 位验证码。"""
	data = flask.request.get_json(silent=True) or {}
	email = str(data.get('email') or '').strip()
	if not EMAIL_RE.match(email):
		return flask.jsonify({"error": "请输入合法的邮箱地址"}), 401
	if not Mail.Configured():
		return flask.jsonify({"error": "邮件服务未配置，请联系管理员"}), 500

	# 冷却：同一邮箱 60秒内只能发一次
	elapsed = int(time.time()) - database.Email.LastTS(email)
	if elapsed < RESEND_INTERVAL:
		return flask.jsonify({"error": f"发送过于频繁，请 {RESEND_INTERVAL - elapsed} 秒后再试"}), 429

	# 验证码固定为随机 6 位
	code = f"{random.randint(0, 999999):06d}"
	# 先发信、后写库：发送失败时不会留下验证码记录，用户可以立即重试（不受冷却限制）
	try:
		Mail.SendCode(email, code)
	except Mail.MailError as error:
		# 具体原因（认证失败 / 超时）只打到控制台，不回给前端，避免泄露发信配置
		print(f"[Mail] 验证码发送失败 -> {email}：{error}", flush=True)
		return flask.jsonify({"error": "验证码发送失败，请稍后重试"}), 502

	database.Email.NewEmail(email, code)
	return "OK"

@app.route('/api/sign/up/2', methods=["POST"])
def SignUp2():
	data = flask.request.get_json(silent=True) or {}
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
	data = flask.request.get_json(silent=True) or {}
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