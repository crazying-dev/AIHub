"""查询个人密钥。"""
from database.conn import conn, text
from database.private.Candidates import Normalize


def Get(UserID) -> list:
	"""
	获取用户的所有 key（只返回 ah-xxxx 字符串，兼容旧的 /api/key/get）
	return keylist
	"""
	sql = text("select * from key where userid = :UserID")
	result = conn.execute(sql, {"UserID": UserID})
	return ["ah-" + str(row["id"]) for row in result.mappings().all()]


def List(UserID) -> list:
	"""
	获取用户的所有 key（含授权范围）
	return list[dict]，形如 {"key": "ah-xxx", "canuse": [私有 key id...], "all": bool}
	all=True 表示未限定范围，即可以使用本人私有库全部 key
	"""
	sql = text("select id, canuse from key where userid = :UserID")
	result = conn.execute(sql, {"UserID": UserID})
	items = []
	for row in result.mappings().all():
		Ids = Normalize(row["canuse"]) or []
		items.append({"key": "ah-" + str(row["id"]), "canuse": Ids, "all": not Ids})
	return items
