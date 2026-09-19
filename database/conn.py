import os
from sqlalchemy import create_engine,text
import atexit

database_url = os.getenv('DATABASE_URL')
engine = create_engine(database_url)

conn = engine.connect()
atexit.register(conn.close)
