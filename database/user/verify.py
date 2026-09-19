"""验证用户"""
from database.conn import conn, text
import hashlib

def verifyUser_UserID___UserToken(UserID, UserToken) -> bool:
	sql = text("""
	            SELECT * FROM users
	            WHERE token = :token_val AND id = :id_val
	        """)
	# 执行，传入参数字典
	result = conn.execute(
		sql,
		{"token_val": UserToken, "id_val": UserID}
	)
	row = result.fetchone()
	if row:
		return True
	else:
		return False

def verifyUser_UserEmail___UserPassword(UserEmail, UserPassword):
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
		return True
	else:
		return False
