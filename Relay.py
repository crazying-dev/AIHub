"""模型中继的统一入口。

职责：
1. 根据调用方请求的 model 从社区池里挑候选 key（auto / 上游 model 名 / 上传者给 key 起的 name）；
2. 依次尝试候选，按候选自己的协议把请求打到上游；
3. 每次真正打到上游就 used + 1（成功失败都计，避免刷失败绕过限额）。
"""
import database
import protocol


class NoKeyError(Exception):
	"""社区池里没有可用于该模型的 key。"""


class UpstreamError(Exception):
	"""所有候选 key 都调失败了。"""


def Candidates(Model):
	"""
	按调用方请求的 model 取候选列表（已按 priority / 剩余次数排好序）
	- auto（或没填）：返回整个池子
	- 具体模型名：先按上游 model 名匹配；全都匹配不上，再按上传者给 key 起的 name 兜底
	"""
	Pool = database.community.Candidates.Candidates()
	if not Model or str(Model).lower() == "auto":
		return Pool
	Model = str(Model)
	ByModel = [Row for Row in Pool if Row["model"] == Model]
	if ByModel:
		return ByModel
	return [Row for Row in Pool if Row["name"] == Model]


def Call(Request, Model, Stream=False):
	"""
	依次尝试候选 key
	return (canonical 响应或分片生成器, 命中的候选)
	"""
	Pool = Candidates(Model)
	if not Pool:
		raise NoKeyError(f"社区池里没有可用于模型 {Model} 的 key")
	LastError = None
	for Row in Pool:
		try:
			Adapter = protocol.Get(Row["protocol"])
		except ValueError as Error:
			LastError = Error
			continue
		# 协议认得出来才算“真正要发起上游调用”，此时计数
		database.community.Use.Use(Row["id"])
		try:
			return Adapter.Call(Request, Row["url"], Row["key"], Row["model"], Stream), Row
		except Exception as Error:
			LastError = Error
			continue
	raise UpstreamError(str(LastError) if LastError else "上游调用失败")


def Models():
	"""社区池当前可用的模型标识（含 auto）"""
	Names = database.community.Candidates.Models()
	return ["auto"] + [Name for Name in Names if Name != "auto"]
