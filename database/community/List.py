"""查询社区 key。"""
from database.conn import conn, text

# 列表与调度用的是同一批列，集中一处维护
_COLUMNS = "id, userid, url, model, key, protocol, text, name, priority, maxuse, used, enabled, created_at"


def MaskKey(Key):
	"""上游密钥打码：只留头尾，避免列表接口泄露明文。"""
	if not Key:
		return ""
	if len(Key) <= 12:
		return Key[:4] + "****"
	return Key[:6] + "****" + Key[-4:]


def ToItem(row):
	"""数据库行 -> 接口返回的字典（不含明文 key）。"""
	item = dict(row)
	item["key"] = MaskKey(item.get("key"))
	if item.get("maxuse") is None:
		item["remaining"] = None
	else:
		item["remaining"] = max(item["maxuse"] - item.get("used", 0), 0)
	return item


def ListByUser(UserID) -> list:
	"""
	获取某个用户上传的全部社区 key
	return list[dict]
	"""
	sql = text(f"SELECT {_COLUMNS} FROM otherkey WHERE userid = :userid ORDER BY created_at DESC")
	result = conn.execute(sql, {"userid": UserID})
	return [ToItem(row) for row in result.mappings().all()]


def All(CallerID=None) -> list:
	"""
	社区池全部条目（社区页浏览用，按调度优先级排序）
	上游密钥已打码；**不返回 userid**，仅把调用方自己的条目标记 mine=True
	return list[dict]
	"""
	sql = text(f"SELECT {_COLUMNS} FROM otherkey ORDER BY priority DESC, used ASC, created_at ASC")
	result = conn.execute(sql)
	items = []
	for row in result.mappings().all():
		item = ToItem(row)
		Owner = item.pop("userid")
		item["mine"] = bool(CallerID) and Owner == CallerID
		items.append(item)
	return items


def GetOne(KeyID):
	"""
	按 id 取一条社区 key（含明文 key，仅内部调度使用）
	return dict|None
	"""
	sql = text(f"SELECT {_COLUMNS} FROM otherkey WHERE id = :id")
	row = conn.execute(sql, {"id": KeyID}).mappings().first()
	return dict(row) if row else None
