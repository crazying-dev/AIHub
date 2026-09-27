"""新建个人密钥。"""
import uuid

from database.conn import conn, text

def NewKey(UserID, CanUse=None):
	"""
	新建 key
	CanUse：授权使用的私有 key id 列表（逗号分隔字符串 / 可迭代），None 或空 = 本人私有库全部 key
	return keyid
	"""
	sql=text("""
			INSERT INTO key (id, userid, canuse)
			VALUES (:id, :userid, :canuse)
	""")
	keyid = str(uuid.uuid4())

	conn.execute(sql, {"id":keyid, "userid": UserID, "canuse": CanUse})
	conn.commit()
	return keyid
