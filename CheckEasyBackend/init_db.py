# 文件路径: CheckEasyBackend/init_db.py

import asyncio
from app.core.db import Base, async_engine
from app.modules.auth.register.models import User
from app.modules.checkin.models import CheckinRecord  # <-- 正确导入类名

async def init_models():
    async with async_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

if __name__ == "__main__":
    asyncio.run(init_models())