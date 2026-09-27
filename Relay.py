"""模型中继的统一入口。

两种调度来源：
- 公共库（社区池 otherkey）：凭证是固定的字面量 ah-xxxx，任何调用方都能用；
- 私有库（privatekey）：调用方拿自己的个人密钥 ah-<id>，只在本人的私有 key（可按 canuse 白名单收窄）里挑。

职责：
1. 按来源 + 请求的 model 挑候选 key（auto / 上游 model 名 / 上传者给 key 起的 name）；
2. 依次尝试候选，按候选自己的协议把请求打到上游；
3. 每次真正打到上游就 used + 1（成功失败都计，避免刷失败绕过限额）。
"""
import database
import protocol


class NoKeyError(Exception):
	"""没有可用于该模型的 key。"""


class UpstreamError(Exception):
	"""所有候选 key 都调失败了。"""


def _IsPrivate(Caller):
	"""个人密钥（key 表）走私有库；其余（ah-xxxx 公共凭证 / 历史社区密钥）走公共库"""
	return bool(Caller) and Caller.get("source") == "key"


def _Label(Caller):
	return "私有库" if _IsPrivate(Caller) else "公共库"


def Candidates(Model, Caller=None):
	"""
	按调用方请求的 model 取候选列表（已按 priority / 剩余次数排好序）
	- 调用方是个人密钥：在本人私有库里挑，且受该密钥的 canuse 白名单限制
	- 否则：在整个公共库（社区池）里挑
	- auto（或没填）：返回整个池子
	- 具体模型名：先按上游 model 名匹配；全都匹配不上，再按上传者给 key 起的 name 兜底
	"""
	if _IsPrivate(Caller):
		Pool = database.private.Candidates.Candidates(Caller.get("userid"), Caller.get("canuse"))
	else:
		Pool = database.community.Candidates.Candidates()
	if not Model or str(Model).lower() == "auto":
		return Pool
	Model = str(Model)
	ByModel = [Row for Row in Pool if Row["model"] == Model]
	if ByModel:
		return ByModel
	return [Row for Row in Pool if Row["name"] == Model]


def Call(Request, Model, Stream=False, Caller=None):
	"""
	依次尝试候选 key
	return (canonical 响应或分片生成器, 命中的候选)
	"""
	Private = _IsPrivate(Caller)
	Pool = Candidates(Model, Caller)
	if not Pool:
		raise NoKeyError(f"{_Label(Caller)}里没有可用于模型 {Model} 的 key")
	LastError = None
	for Row in Pool:
		try:
			Adapter = protocol.Get(Row["protocol"])
		except ValueError as Error:
			LastError = Error
			continue
		# 协议认得出来才算“真正要发起上游调用”，此时计数
		if Private:
			database.private.Use.Use(Row["id"])
		else:
			database.community.Use.Use(Row["id"])
		try:
			return Adapter.Call(Request, Row["url"], Row["key"], Row["model"], Stream), Row
		except Exception as Error:
			LastError = Error
			continue
	raise UpstreamError(str(LastError) if LastError else "上游调用失败")


def Models(Caller=None):
	"""当前调用方可用的模型标识（含 auto）"""
	if _IsPrivate(Caller):
		Names = database.private.Candidates.Models(Caller.get("userid"), Caller.get("canuse"))
	else:
		Names = database.community.Candidates.Models()
	return ["auto"] + [Name for Name in Names if Name != "auto"]
