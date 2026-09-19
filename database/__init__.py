"""
数据库，使用SQL，.env储存SQL连接字段

API Key:
ah-{Key ID}
"""
import database.user as user
import database.InitDatabase as __initdb
import database.persistent as persistent
import database.email as Email
import database.key as key

__initdb.InitUser()
__initdb.InitKEY()
__initdb.InitOtherKey()
__initdb.InitUseMessage()
__initdb.InitEmail()

__all__ = ["user", "persistent", "Email", "key"]
