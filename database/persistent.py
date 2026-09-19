"""
持续性任务
"""
from database.conn import conn, text
import threading
import time

class main:
	def __init__(self):
		self.time_last_5min = lambda:int(time.time()) - 300
		self.time_last_30d = lambda:int(time.time())- 60*60*24*30

	def email(self):
		sql = text("""
		        DELETE FROM email
		        WHERE CAST(ts AS BIGINT) < :threshold
		    """)
		while True:
			result = conn.execute(sql, {"threshold": self.time_last_5min()})
			conn.commit()
			print(f"已删除邮箱记录，行数：{result.rowcount}")
			time.sleep(1)
		
	def message(self):
		sql = text("""
		        DELETE FROM usemessage
		        WHERE CAST(ts AS BIGINT) < :threshold
		    """)
		while True:
			result = conn.execute(sql, {"threshold": self.time_last_30d()})
			conn.commit()
			print(f"已删除消息记录，行数：{result.rowcount}")
			time.sleep(1)