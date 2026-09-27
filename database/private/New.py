"""上传一条私有库 key。"""
import time
import uuid

from database.conn import conn, text


def NewKey(UserID, URL, Model, Key, Protocol, Text=None, Name=None, Priority=50, MaxUse=None):
	"""
	新建私有 key
	return keyid
	"""
	sql = text("""
			INSERT INTO privatekey
				(id, userid, url, model, key, protocol, text, name, priority, maxuse, used, enabled, created_at)
			VALUES
				(:id, :userid, :url, :model, :key, :protocol, :text, :name, :priority, :maxuse, 0, TRUE, :created_at)
	""")
	keyid = str(uuid.uuid4())
	conn.execute(sql, {
		"id": keyid,
		"userid": UserID,
		"url": URL,
		"model": Model,
		"key": Key,
		"protocol": Protocol,
		"text": Text,
		"name": Name,
		"priority": Priority,
		"maxuse": MaxUse,
		"created_at": int(time.time()),
	})
	conn.commit()
	return keyid
