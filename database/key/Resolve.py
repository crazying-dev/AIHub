"""按 ah-xxxx 反查密钥。

三条来源：
- 字面量 ah-xxxx：公共库（otherkey 表）的公共凭证，任何人都能用，不需要注册
- 个人密钥 ah-<key.id>：只能调度本人私有库（privatekey 表）里、且落在其 key.canuse 白名单内的 key
- 历史社区密钥 ah-<otherkey.id>：等价于公共库里的某一条（兼容旧数据）

注意：私有库的 id 不是凭证，这里刻意不查 privatekey，所以 ah-<private key id> 一律无效。
"""
from database.conn import conn, text

# 公共库的固定凭证：字面量 ah-xxxx（就是这四个 x，不可更换）
PUBLIC_KEY = "ah-xxxx"


def ByAPIKey(APIKey):
	"""
	解析调用方带来的密钥
	return dict|None，形如
	{"id": ..., "userid": ..., "source": "public"|"key"|"otherkey", "enabled": bool, "canuse": list|None}
	"""
	if not APIKey:
		return None
	APIKey = str(APIKey).strip()
	# 公共库凭证优先判定：它不是数据库里的某一行，就是这四个固定字符
	if APIKey == PUBLIC_KEY or APIKey == "xxxx":
		return {"id": "xxxx", "userid": None, "source": "public", "enabled": True, "canuse": None}
	KeyID = APIKey[3:] if APIKey.startswith("ah-") else APIKey
	row = conn.execute(
		text("SELECT id, userid, canuse FROM key WHERE id = :id"),
		{"id": KeyID}
	).mappings().first()
	if row:
		return {
			"id": row["id"],
			"userid": row["userid"],
			"source": "key",
			"enabled": True,
			"canuse": row["canuse"],
		}
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
			"canuse": None,
		}
	return None
