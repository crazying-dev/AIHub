"""删除私有库 key。"""
from database.conn import conn, text


def Delete(UserID, KeyID) -> bool:
	"""
	删除指定用户私有库里的某条 key（带上 userid 条件，防止越权删别人的）
	return bool，是否真的删掉了一条
	"""
	sql = text("DELETE FROM privatekey WHERE id = :id AND userid = :userid")
	result = conn.execute(sql, {"id": KeyID, "userid": UserID})
	conn.commit()
	return bool(result.rowcount)
