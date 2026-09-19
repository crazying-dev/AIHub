import time
from database.conn import conn, text

def NewEmail(email, code):
	sql = text("""
			INSERT INTO email (email, code, ts)
			VALUES (:email, :code, :ts)
	""")
	conn.execute(sql,{
		"email":email,
		"code":code,
		"ts": str(int(time.time()))
	})
	conn.commit()

def Verify(email, code):
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