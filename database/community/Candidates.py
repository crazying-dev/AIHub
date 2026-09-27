"""社区池调度：候选排序与可用模型列表。"""
from database.conn import conn, text

_COLUMNS = "id, userid, url, model, key, protocol, text, name, priority, maxuse, used, enabled, created_at"


def Candidates() -> list:
	"""
	取出所有“还能用”的社区 key，按调度优先级排序：
	priority 越大越优先 -> 已用次数越少越优先 -> 上传越早越优先
	return list[dict]
	"""
	sql = text(f"""
			SELECT {_COLUMNS} FROM otherkey
			WHERE enabled = TRUE AND (maxuse IS NULL OR used < maxuse)
			ORDER BY priority DESC, used ASC, created_at ASC
	""")
	result = conn.execute(sql)
	return [dict(row) for row in result.mappings().all()]


def Models() -> list:
	"""
	社区池当前可用的模型标识（上游 model 名 + 上传者起的 name），供 /v1/models 展示
	return list[str]
	"""
	sql = text("""
			SELECT DISTINCT model, name FROM otherkey
			WHERE enabled = TRUE AND (maxuse IS NULL OR used < maxuse)
	""")
	result = conn.execute(sql)
	models = set()
	for row in result.mappings().all():
		if row["model"]:
			models.add(row["model"])
		if row["name"]:
			models.add(row["name"])
	return sorted(models)
