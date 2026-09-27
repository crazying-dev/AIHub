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
	row = result.fetchone()
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
	row = result.fetchone()
	if row:
		return row["token"]
	else:
		return False