import hashlib
from database.conn import conn, text
import uuid

def NewUser(UserName, UserEmail, UserPassword):
	sql = text("""
	        INSERT INTO users (id, username, password, avatar, email, token)
	        VALUES (:id, :username, :password, :avatar, :email, :token)
	    """)
	conn.execute(sql, {
		"id": uuid.uuid4(),
		"username": UserName,
		"password":  hashlib.sha256(UserPassword.encode("utf-8")).hexdigest(),
		"avatar": "",
		"email": UserEmail,
		"token": hashlib.sha256((UserEmail + UserPassword).encode("utf-8")).hexdigest()
	})
	conn.commit()
