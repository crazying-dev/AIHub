"""
数据库，使用SQL，.env储存SQL连接字段

API Key:
ah-{Key ID}

- key 表：用户在控制台创建的个人密钥
- otherkey 表：用户上传的社区密钥（含自己的上游厂商 key），见 database/community
"""
import database.user as user
import database.InitDatabase as __initdb
import database.persistent as persistent
import database.email as Email
import database.key as key
import database.community as community

__initdb.InitUser()
__initdb.InitKEY()
__initdb.InitOtherKey()
__initdb.InitUseMessage()
__initdb.InitEmail()

__all__ = ["user", "persistent", "Email", "key", "community"]

