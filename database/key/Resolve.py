"""按 ah-xxxx 反查密钥。

个人密钥（key 表）与社区密钥（otherkey 表）产生的都是 ah-{id}，
调用 /v1/* 时两者都算有效凭证，所以这里按“先个人、后社区”的顺序查。
"""
from database.conn import conn, text


def ByAPIKey(APIKey):
	"""
	解析调用方带来的密钥
	return dict|None，形如 {"id": ..., "userid": ..., "source": "key"|"otherkey", "en": bool}
	"""
	if not APIKey:
		return None
	KeyID = APIKey[3:] if APIKey.startswith("ah-") else APIKey
	row = conn.execute(
		text("SELECT id, userid FROM key WHERE id = :id"),
		{"id": KeyID}
	).mappings().first()
	if row:
		return {"id": row["id"], "userid": row["userid"], "source": "key", "enabled": True}
	row = conn.execute(
		text("SELECT id, userid, enabled FROM otherkey WHERE id = :id"),
		{"id": KeyID}
	).mappings().first()
	if row:
		return {
			"id": row["id"],
			"userid": row["userid"],
			"source": "otherkey",
			"enabled": bool(row["enabled"]),
		}
	return None
