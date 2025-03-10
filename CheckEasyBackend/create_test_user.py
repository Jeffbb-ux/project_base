# 路径: CheckEasyBackend/create_test_user.py
import asyncio
from app.core.db import AsyncSessionLocal
from app.modules.auth.register.models import User
from app.modules.auth.login.utils import hash_password

async def create_user():
    async with AsyncSessionLocal() as session:
        user = User(
            username="john_doe",
            email="john@example.com",
            hashed_password=hash_password("Passw0rd!"),
            is_active=True
        )
        session.add(user)
        await session.commit()
        print("Test user created successfully!")

asyncio.run(create_user())