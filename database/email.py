import time
from database.conn import conn, text

def NewEmail(email, code):
	"""
	储存新的email验证码

	email 是主键（一个邮箱只留一条验证码），所以用 UPSERT：
	重复请求时覆盖旧验证码与时间戳，否则第二次INSERT 会撞主键报错。
	"""
	sql = text("""
			INSERT INTO email (email, code, ts)
			VALUES (:email, :code, :ts)
			ON CONFLICT (email) DO UPDATE
			SET code = EXCLUDED.code, ts = EXCLUDED.ts
	""")
	conn.execute(sql,{
		"email":email,
		"code":code,
		"ts": str(int(time.time()))
	})
	conn.commit()


def LastTS(email) -> int:
	"""
	该邮箱最近一次发验证码的时间（unix 秒）；查不到记录时返回 0
	用于注册接口的发信冷却判断
	"""
	sql = text("""
			SELECT ts FROM email
			WHERE email = :email
	""")
	row = conn.execute(sql, {"email": email}).mappings().fetchone()
	if row is None:
		return 0
	try:
		return int(row["ts"])
	except (TypeError, ValueError):
		return 0

def Verify(email, code):
	"""
	验证email验证码
	return bool
	"""
	sql = text("""
			SELECT * FROM email
			WHERE email = :email AND code = :code
	""")
	result = conn.execute(sql,{
		"email":email,
		"code":code
	})
	row = result.fetchone()
	if row:
		return True
	else:
		return False