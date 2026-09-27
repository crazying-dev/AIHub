"""有关key操作的统一入口。

- 个人 key（key 表）：控制台自建，形如 ah-xxxx
- 社区 key（otherkey 表）：用户上传自己的上游 key，对外同样暴露为 ah-xxxx
"""
import database


def NewKey(UserID):
	"""
	return key
	"""
	keyid = database.key.New.NewKey(UserID)
	return f"ah-{keyid}"


def NewCommunityKey(UserID, URL, Key, Protocol, Model, Name=None, Priority=50, MaxUse=None, Text=None):
	"""
	上传一条社区 key（用户自己的上游厂商 key），返回对外使用的 ah-xxxx
	"""
	keyid = database.community.New.NewKey(UserID, URL, Model, Key, Protocol, Text, Name, Priority, MaxUse)
	return f"ah-{keyid}"


def GetCommunityKeys(UserID):
	"""当前用户上传的社区 key 列表（上游密钥已打码）"""
	return database.community.List.ListByUser(UserID)


def DeleteCommunityKey(UserID, KeyID) -> bool:
	"""删除自己上传的社区 key，keyid 带不带 ah- 前缀都行"""
	if KeyID and KeyID.startswith("ah-"):
		KeyID = KeyID[3:]
	return database.community.Delete.Delete(UserID, KeyID)


Get = database.key.Get.Get

