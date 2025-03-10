# File: CheckEasyBackend/scripts/test_db_connection.py
from sqlalchemy import create_engine
from app.core.config import settings

engine = create_engine(settings.DATABASE_URL)

try:
    connection = engine.connect()
    print("数据库连接成功！")
    connection.close()
except Exception as e:
    print("数据库连接失败：", e)