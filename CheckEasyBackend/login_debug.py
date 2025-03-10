#!/usr/bin/env python3
"""
standalone_login_debug.py

独立的登录调试脚本，用于自动提取登录过程中的关键信息，
包括用户记录、数据库中存储的 hashed_password、密码验证结果等。

用法：
    python standalone_login_debug.py <email> <plain_password>
"""

import asyncio
import sys
import logging
from contextlib import asynccontextmanager

from sqlalchemy.future import select
from app.core.db import get_async_db
from app.core.security import verify_password, hash_password
from app.modules.auth.register.models import User

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger("standalone_login_debug")

@asynccontextmanager
async def db_context():
    """
    包装 get_async_db() 生成器，以便使用 async with。
    """
    gen = get_async_db()
    db = await gen.__anext__()
    try:
        yield db
    finally:
        await gen.aclose()

async def debug_login(email: str, plain_password: str):
    async with db_context() as db:
        # 查询用户记录
        result = await db.execute(select(User).filter(User.email == email))
        user = result.scalars().first()
        if not user:
            print(f"[Error] 用户未在数据库中找到: {email}")
            return

        # 输出用户记录的关键信息
        print("=== 登录调试信息 ===")
        print(f"用户邮箱: {user.email}")
        print(f"数据库中存储的 hashed_password: {user.hashed_password}")
        print(f"用户 is_active 状态: {user.is_active}")
        print(f"用户 verification_status: {user.verification_status}")

        # 使用 verify_password 验证输入密码与存储的哈希是否匹配
        is_valid = verify_password(plain_password, user.hashed_password)
        print(f"调用 verify_password(plain_password, stored_hash) 返回: {is_valid}")

        # 生成新哈希并验证，确认当前环境的密码处理逻辑
        new_hash = hash_password(plain_password)
        is_valid_new = verify_password(plain_password, new_hash)
        print(f"使用 hash_password 生成的新哈希: {new_hash}")
        print(f"调用 verify_password(plain_password, new_hash) 返回 (应为 True): {is_valid_new}")

        # 自动诊断并给出结论
        if is_valid:
            print("诊断结论: 数据库中存储的哈希能够验证输入密码，密码验证逻辑正常。")
        else:
            print("诊断结论: 数据库中存储的哈希无法验证输入密码，可能存在双重哈希或数据截断问题。")
        
        # 对比哈希前缀（仅用于参考，因随机盐原因两次生成的哈希不同）
        print("存储哈希前10位:", user.hashed_password[:10])
        print("新生成哈希前10位:", new_hash[:10])
        print("=======================")

if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("用法: python standalone_login_debug.py <email> <plain_password>")
        sys.exit(1)
    email_arg = sys.argv[1]
    password_arg = sys.argv[2]
    asyncio.run(debug_login(email_arg, password_arg))