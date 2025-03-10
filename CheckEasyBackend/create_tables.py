# create_tables.py
import asyncio
from app.core.db import Base, async_engine

async def create_tables():
    async with async_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

asyncio.run(create_tables())