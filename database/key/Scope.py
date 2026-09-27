"""设置个人密钥的授权范围。"""
from database.conn import conn, text


def SetCanUse(UserID, KeyID, CanUse) -> bool:
	"""
	改写某条个人密钥的 canuse
	CanUse：逗号分隔的私有 key id 字符串，None 表示不限制（本人私有库全部 key）
	return bool，是否真的改到了（带 userid 条件，防止越权）
	"""
	sql = text("UPDATE key SET canuse = :canuse WHERE id = :id AND userid = :userid")
	result = conn.execute(sql, {"canuse": CanUse, "id": KeyID, "userid": UserID})
	conn.commit()
	return bool(result.rowcount)
