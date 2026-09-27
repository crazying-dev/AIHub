"""
数据库，使用SQL，.env储存SQL连接字段

API Key:
ah-{Key ID}      # 个人密钥：只调度本人私有库（受 key.canuse 白名单约束）
ah-xxxx          # 公共库的固定凭证：任何人带上它都能调用社区池（otherkey）

- key 表：用户在控制台创建的个人密钥
- otherkey 表：用户上传的公共库/社区密钥（含自己的上游厂商 key），见 database/community
- privatekey 表：用户上传的私有库密钥，只给自己用，见 database/private
"""
import database.user as user
import database.InitDatabase as __initdb
import database.persistent as persistent
import database.email as Email
import database.key as key
import database.community as community
import database.private as private

__initdb.InitUser()
__initdb.InitKEY()
__initdb.InitOtherKey()
__initdb.InitPrivateKey()
__initdb.InitUseMessage()
__initdb.InitEmail()

__all__ = ["user", "persistent", "Email", "key", "community", "private"]

