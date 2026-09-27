"""有关 key 操作的统一入口。

三个概念：
- 个人密钥（key 表）：控制台自建，形如 ah-<id>；调用 /v1 时只能调度本人私有库里的 key，
  并且要落在该密钥的 canuse 白名单内（canuse 为空 = 本人私有库全部 key）。
- 私有库（privatekey 表）：用户上传自己的上游 key，只给自己的个人密钥使用，见 database/private。
- 公共库 / 社区池（otherkey 表）：用户上传的上游 key，凭证是固定的字面量 ah-xxxx，任何人带上它都能调用。
"""
import database
from database.private.Candidates import Normalize


def _JoinCanUse(Ids):
	"""把授权范围归一化成逗号分隔的字符串；空 -> None（表示可访问本人私有库全部 key）"""
	Values = Normalize(Ids)
	return ",".join(Values) if Values else None


def NewKey(UserID, CanUse=None):
	"""
	新建个人密钥
	CanUse：授权使用的私有 key id 列表；None / 空 = 本人私有库全部 key
	return key
	"""
	keyid = database.key.New.NewKey(UserID, _JoinCanUse(CanUse))
	return f"ah-{keyid}"


def ListKeys(UserID):
	"""当前用户的全部个人密钥（含授权范围）"""
	return database.key.Get.List(UserID)


def SetKeyScope(UserID, Key, CanUse) -> bool:
	"""修改某条个人密钥的授权范围，Key 带不带 ah- 前缀都行"""
	if Key and Key.startswith("ah-"):
		Key = Key[3:]
	return database.key.Scope.SetCanUse(UserID, Key, _JoinCanUse(CanUse))


def DeleteKey(UserID, Key) -> bool:
	"""吊销（删除）自己创建的个人密钥，Key 带不带 ah- 前缀都行"""
	if Key and Key.startswith("ah-"):
		Key = Key[3:]
	return database.key.Delete.Delete(UserID, Key)


def NewPrivateKey(UserID, URL, Key, Protocol, Model, Name=None, Priority=50, MaxUse=None, Text=None):
	"""
	上传一条私有库 key（用户自己的上游厂商 key），返回 keyid
	私有库的 id 不是对外凭证，只有本人的个人密钥能调度到它
	"""
	return database.private.New.NewKey(UserID, URL, Model, Key, Protocol, Text, Name, Priority, MaxUse)


def GetPrivateKeys(UserID):
	"""当前用户私有库的 key 列表（上游密钥已打码）"""
	return database.private.List.ListByUser(UserID)


def DeletePrivateKey(UserID, KeyID) -> bool:
	"""删除自己私有库里的某条 key"""
	return database.private.Delete.Delete(UserID, KeyID)


def NewCommunityKey(UserID, URL, Key, Protocol, Model, Name=None, Priority=50, MaxUse=None, Text=None):
	"""
	上传一条公共库（社区池）key，返回对外使用的 ah-xxxx
	"""
	keyid = database.community.New.NewKey(UserID, URL, Model, Key, Protocol, Text, Name, Priority, MaxUse)
	return f"ah-{keyid}"


def GetCommunityKeys(UserID):
	"""当前用户上传的公共库 key 列表（上游密钥已打码）"""
	return database.community.List.ListByUser(UserID)


def DeleteCommunityKey(UserID, KeyID) -> bool:
	"""删除自己上传的公共库 key，keyid 带不带 ah- 前缀都行"""
	if KeyID and KeyID.startswith("ah-"):
		KeyID = KeyID[3:]
	return database.community.Delete.Delete(UserID, KeyID)


def GetCommunityPool(UserID=None):
	"""公共库全部条目（社区页浏览用，上游密钥已打码；自己的条目标记 mine）"""
	return database.community.List.All(UserID)


Get = database.key.Get.Get
