from database.conn import conn, text
import uuid

def NewKey(UserID):
	"""
	新建key
	return keyid
	"""
	sql=text("""
			INSERT INTO key (id, userid)
			VALUES (:id, :userid)
	""")
	keyid = uuid.uuid4()
	
	conn.execute(sql, {"id":keyid, "userid": UserID})
	conn.commit()
	return keyid
