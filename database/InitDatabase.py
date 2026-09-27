"""
包含库：
user | key | otherkey | privatekey | usemessage | email
"""

from database.conn import conn, text

def InitUser():
	conn.execute(
		text(
			"""
		CREATE TABLE IF NOT EXISTS users (
			id TEXT PRIMARY KEY,
			username VARCHAR(64) NOT NULL UNIQUE,
			password VARCHAR(256) NOT NULL,
			avatar VARCHAR(255) NOT NULL,
			email VARCHAR(255) NOT NULL,
			token VARCHAR(512) NOT NULL
		);
		"""
		)
	)
	conn.commit()

def InitKEY():
	conn.execute(
		text(
			"""
		CREATE TABLE IF NOT EXISTS key (
			id TEXT PRIMARY KEY,
			userid TEXT NOT NULL,
			canuse TEXT
		);
		"""
		)
	)
	conn.commit()

def InitOtherKey():
	"""
	公共库（otherkey）：用户上传自己的上游 key，凭证是固定的字面量 ah-xxxx，任何人带上它都能调用。
	- name：上传者给这条 key 起的名字（model 匹配不上时按它兜底匹配）
	- priority：优先级，数字越大越优先（默认 50）
	- maxuse：调用次数上限，NULL 表示不限
	- used：已调用次数
	- enabled：是否参与调度
	- created_at：上传时间（unix 秒）
	"""
	conn.execute(
		text(
			"""
		CREATE TABLE IF NOT EXISTS otherkey (
			id TEXT PRIMARY KEY,
			userid TEXT NOT NULL,
			url TEXT NOT NULL,
			model TEXT NOT NULL,
			key TEXT NOT NULL,
			protocol TEXT NOT NULL,
			text TEXT,
			name TEXT,
			priority INTEGER NOT NULL DEFAULT 50,
			maxuse INTEGER,
			used INTEGER NOT NULL DEFAULT 0,
			enabled BOOLEAN NOT NULL DEFAULT TRUE,
			created_at BIGINT
		);
		"""
		)
	)
	# 老库升级：CREATE TABLE IF NOT EXISTS 不会给已存在的表补列，这里逐列幂等补齐。
	for ddl in (
		"ALTER TABLE otherkey ADD COLUMN IF NOT EXISTS name TEXT",
		"ALTER TABLE otherkey ADD COLUMN IF NOT EXISTS priority INTEGER NOT NULL DEFAULT 50",
		"ALTER TABLE otherkey ADD COLUMN IF NOT EXISTS maxuse INTEGER",
		"ALTER TABLE otherkey ADD COLUMN IF NOT EXISTS used INTEGER NOT NULL DEFAULT 0",
		"ALTER TABLE otherkey ADD COLUMN IF NOT EXISTS enabled BOOLEAN NOT NULL DEFAULT TRUE",
		"ALTER TABLE otherkey ADD COLUMN IF NOT EXISTS created_at BIGINT",
	):
		conn.execute(text(ddl))
	# 历史行补上时间戳，保证调度排序稳定（已补齐后这条 UPDATE 为空操作）
	conn.execute(text("UPDATE otherkey SET created_at = 0 WHERE created_at IS NULL"))
	conn.commit()

def InitPrivateKey():
	"""
	私有库（privatekey）：用户上传自己的上游 key，只给本人的个人密钥 ah-<id> 使用。
	字段与 otherkey 完全一致，区别只在调度来源与可见范围。
	"""
	conn.execute(
		text(
			"""
		CREATE TABLE IF NOT EXISTS privatekey (
			id TEXT PRIMARY KEY,
			userid TEXT NOT NULL,
			url TEXT NOT NULL,
			model TEXT NOT NULL,
			key TEXT NOT NULL,
			protocol TEXT NOT NULL,
			text TEXT,
			name TEXT,
			priority INTEGER NOT NULL DEFAULT 50,
			maxuse INTEGER,
			used INTEGER NOT NULL DEFAULT 0,
			enabled BOOLEAN NOT NULL DEFAULT TRUE,
			created_at BIGINT
		);
		"""
		)
	)
	# 与 otherkey 同样的幂等补列，兼容“表已存在但缺列”的老库。
	for ddl in (
		"ALTER TABLE privatekey ADD COLUMN IF NOT EXISTS name TEXT",
		"ALTER TABLE privatekey ADD COLUMN IF NOT EXISTS priority INTEGER NOT NULL DEFAULT 50",
		"ALTER TABLE privatekey ADD COLUMN IF NOT EXISTS maxuse INTEGER",
		"ALTER TABLE privatekey ADD COLUMN IF NOT EXISTS used INTEGER NOT NULL DEFAULT 0",
		"ALTER TABLE privatekey ADD COLUMN IF NOT EXISTS enabled BOOLEAN NOT NULL DEFAULT TRUE",
		"ALTER TABLE privatekey ADD COLUMN IF NOT EXISTS created_at BIGINT",
	):
		conn.execute(text(ddl))
	conn.execute(text("UPDATE privatekey SET created_at = 0 WHERE created_at IS NULL"))
	conn.commit()

def InitUseMessage():
	conn.execute(
		text(
			"""
		CREATE TABLE IF NOT EXISTS usemessage (
			ts TEXT PRIMARY KEY,
			message TEXT NOT NULL,
			userid TEXT NOT NULL
		);
		"""
		)
	)
	conn.commit()

def InitEmail():
	conn.execute(
		text(
			"""
		CREATE TABLE IF NOT EXISTS email (
			email TEXT PRIMARY KEY,
			code TEXT NOT NULL,
			ts TEXT NOT NULL
		);
		"""
		)
	)
	conn.commit()
