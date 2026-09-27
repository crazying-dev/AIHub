import os
from sqlalchemy import create_engine,text
import atexit

database_url = os.getenv('DATABASE_URL')

# SQLAlchemy 2.1 起 postgresql:// 的默认驱动由 psycopg2 改成了 psycopg(3)，
# 而本仓库依赖的是 psycopg2-binary；这里把驱动显式写进 URL，
# 避免 SQLAlchemy 升到 2.1+ 后报 ModuleNotFoundError: No module named 'psycopg'。
if database_url and database_url.startswith('postgresql://'):
	database_url = 'postgresql+psycopg2://' + database_url[len('postgresql://'):]

engine = create_engine(database_url)

conn = engine.connect()

atexit.register(conn.close)
