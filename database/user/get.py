"""读取用户信息。

注意：SQLAlchemy 2.1 起 Row 的下标只认整数（内部就是元组），
row["字段名"] 会抛 TypeError: tuple indices must be integers or slices, not str，
所以这里统一用 result.mappings() 拿到可以按字段名取值的行。
"""
import hashlib

from database.conn import conn, text


def GetID_UserEmail___UserPassword(UserEmail, UserPassword):
	"""
	通过Email和Password查找用户
	return bool|userid
	"""
	UserPassword_hash = hashlib.sha256(UserPassword.encode("utf-8")).hexdigest()
	sql = text("""
	            SELECT * FROM users
	            WHERE email = :email_val AND password = :password_val
	        """)
	result = conn.execute(
		sql,
		{"email_val": UserEmail, "password_val": UserPassword_hash}
	)
	row = result.mappings().fetchone()
	if row:
		return row["id"]
	else:
		return False

def GetToken_UserEmail___UserPassword(UserEmail, UserPassword):
	"""
	通过Email和Password查找用户
	return bool|usertoken
	"""
	UserPassword_hash = hashlib.sha256(UserPassword.encode("utf-8")).hexdigest()
	sql = text("""
	            SELECT * FROM users
	            WHERE email = :email_val AND password = :password_val
	        """)
	result = conn.execute(
		sql,
		{"email_val": UserEmail, "password_val": UserPassword_hash}
	)
	row = result.mappings().fetchone()
	if row:
		return row["token"]
	else:
		return False