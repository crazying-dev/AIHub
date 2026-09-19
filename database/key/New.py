from database.conn import conn, text
import uuid

def NewKey(UserID):
	sql=text("""
			INSERT INTO key (keyid, userid)
			VALUES (:keyid, :userid)
	""")
	keyid = uuid.uuid4()
	
	conn.execute(sql, {"keyid":keyid, "userid": UserID})
	conn.commit()
	return keyid
