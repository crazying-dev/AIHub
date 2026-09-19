from database.conn import conn, text

def Get(UserID)->list:
	sql = text("select * from key where userid = :UserID")
	result = conn.execute(sql, {"UserID":UserID})
	key_list = ["ah-" + str(r._asdict()["id"]) for r in result.all()]
	return key_list
