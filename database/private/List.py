"""查询私有库 key（privatekey 表）。"""
from database.community.List import ToItem
from database.conn import conn, text

# 列表与调度用的是同一批列，集中一处维护
_COLUMNS = "id, userid, url, model, key, protocol, text, name, priority, maxuse, used, enabled, created_at"


def ListByUser(UserID) -> list:
	"""
	获取某个用户私有库里的全部 key
	上游密钥已打码；**不返回 userid**，因为私有库永远只给本人看
	return list[dict]
	"""
	sql = text(f"SELECT {_COLUMNS} FROM privatekey WHERE userid = :userid ORDER BY priority DESC, used ASC, created_at ASC")
	result = conn.execute(sql, {"userid": UserID})
	items = []
	for row in result.mappings().all():
		item = ToItem(row)
		item.pop("userid", None)
		items.append(item)
	return items
