# File: CheckEasyBackend/scripts/check_db.py
from app.core.db import engine
from sqlalchemy import inspect

def inspect_database():
    inspector = inspect(engine)
    # 获取所有表名
    tables = inspector.get_table_names()
    print("数据库中存在的表：", tables)

    # 遍历每个表，打印字段信息
    for table in tables:
        print(f"\n表：{table}")
        columns = inspector.get_columns(table)
        for column in columns:
            print(f"  - {column['name']} ({column['type']})")

if __name__ == "__main__":
    inspect_database()