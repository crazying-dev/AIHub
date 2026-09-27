"""私有库 key 用量累加。"""
from database.conn import conn, text


def Use(KeyID) -> None:
	"""
	一次真实的上游调用后把 used + 1
	用 SQL 自增而不是“先查再写”，避免并发下的读改写竞态
	"""
	sql = text("UPDATE privatekey SET used = used + 1 WHERE id = :id")
	conn.execute(sql, {"id": KeyID})
	conn.commit()
