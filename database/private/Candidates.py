"""私有库调度：白名单归一化、候选排序与可用模型列表。"""
from database.conn import conn, text

_COLUMNS = "id, userid, url, model, key, protocol, text, name, priority, maxuse, used, enabled, created_at"


def Normalize(CanUse):
	"""
	把 key.canuse 归一化为“私有 key id 列表”，或 None（None 表示不限制 = 本人私有库全部 key）
	- None / "" / 空列表 -> None
	- list / tuple / set / 逗号分隔字符串 -> list[str]（去重、去空）
	return list[str]|None
	"""
	if CanUse is None:
		return None
	if isinstance(CanUse, str):
		Parts = CanUse.split(",")
	else:
		try:
			Parts = list(CanUse)
		except TypeError:
			Parts = [CanUse]
	Ids = []
	for Part in Parts:
		Value = str(Part).strip()
		if Value and Value not in Ids:
			Ids.append(Value)
	return Ids or None


def _Where(UserID, CanUse) -> tuple:
	"""
	拼出“某用户私有库 + canuse 白名单”的 WHERE 片段与绑定参数
	显式生成命名占位符，避免不同驱动对 IN 展开支持的差异
	return (sql片段, params)
	"""
	Params = {"userid": UserID}
	Filter = ""
	Ids = Normalize(CanUse)
	if Ids is not None:
		Names = []
		for Index, KeyID in enumerate(Ids):
			Name = f"canuse{Index}"
			Names.append(":" + Name)
			Params[Name] = KeyID
		Filter = " AND id IN (" + ", ".join(Names) + ")"
	return Filter, Params


def Candidates(UserID, CanUse=None) -> list:
	"""
	取某个用户私有库里“还能用”的 key，按调度优先级排序：
	priority 越大越优先 -> 已用次数越少越优先 -> 上传越早越优先
	CanUse 为空 -> 该用户全部私有 key；否则只取白名单内的 id
	return list[dict]
	"""
	Filter, Params = _Where(UserID, CanUse)
	sql = text(f"""
			SELECT {_COLUMNS} FROM privatekey
			WHERE userid = :userid AND enabled = TRUE AND (maxuse IS NULL OR used < maxuse){Filter}
			ORDER BY priority DESC, used ASC, created_at ASC
	""")
	result = conn.execute(sql, Params)
	return [dict(row) for row in result.mappings().all()]


def Models(UserID, CanUse=None) -> list:
	"""
	私有库里当前可用的模型标识（上游 model 名 + 用户起的 name），供 /v1/models 展示
	return list[str]
	"""
	Filter, Params = _Where(UserID, CanUse)
	sql = text(f"""
			SELECT DISTINCT model, name FROM privatekey
			WHERE userid = :userid AND enabled = TRUE AND (maxuse IS NULL OR used < maxuse){Filter}
	""")
	result = conn.execute(sql, Params)
	models = set()
	for row in result.mappings().all():
		if row["model"]:
			models.add(row["model"])
		if row["name"]:
			models.add(row["name"])
	return sorted(models)
