"""
包含库：
user | key | keyuse | otherkey | usemessage | email
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
			text TEXT
		);
		"""
		)
	)
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
