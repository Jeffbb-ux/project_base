#!/usr/bin/env python3
"""
diagnose.py

自动排查密码验证问题的诊断脚本：
1. 查询数据库中指定用户的 hashed_password。
2. 生成当前环境下的新哈希，并对比验证结果。
3. 使用 pwd_context.verify_and_update 检查旧哈希是否需要更新，并打印相关信息。
4. 输出 bcrypt 和 passlib 的版本信息。

使用方法：
    python diagnose.py <email> <plain_password>
"""

import asyncio
import sys
import logging
from contextlib import asynccontextmanager

from sqlalchemy.future import select

from app.core.db import get_async_db
from app.core.security import hash_password, verify_password, pwd_context
from app.modules.auth.register.models import User

logger = logging.getLogger("diagnose")
logging.basicConfig(level=logging.DEBUG)

@asynccontextmanager
async def db_context():
    """
    包装 get_async_db() 生成器，使其可以用 async with 使用。
    """
    gen = get_async_db()
    db = await gen.__anext__()
    try:
        yield db
    finally:
        await gen.aclose()

async def diagnose(email: str, plain_password: str):
    async with db_context() as db:
        # 直接查询用户，不加载 manual_reviews
        query = select(User).filter(User.email == email)
        try:
            result = await db.execute(query)
            user = result.scalars().first()
        except Exception as e:
            print("【错误】执行查询时发生异常：", e)
            return

        if not user:
            print(f"【错误】未在数据库中找到用户：{email}")
            return

        print(f"【信息】查询到用户：{user.email}")
        stored_hash = user.hashed_password
        print(f"【信息】数据库存储的 hashed_password：{stored_hash}")

        # 生成当前环境下的新哈希
        new_hash = hash_password(plain_password)
        print(f"【信息】当前环境生成的新哈希：{new_hash}")

        # 分别验证密码与数据库中旧哈希和新生成的哈希
        verify_stored = verify_password(plain_password, stored_hash)
        print(f"【结果】使用存储的哈希验证密码：{verify_stored}")

        verify_new = verify_password(plain_password, new_hash)
        print(f"【结果】使用新生成的哈希验证密码：{verify_new}")

        # 使用 verify_and_update 检查旧哈希是否需要更新
        valid, updated_hash = pwd_context.verify_and_update(plain_password, stored_hash)
        print(f"【检查】使用 verify_and_update 检查存储哈希：有效={valid}, 更新哈希={updated_hash}")
        if updated_hash and updated_hash != stored_hash:
            print("【提示】旧哈希需要更新，新哈希应为：", updated_hash)
        else:
            print("【提示】旧哈希不需要更新或已是最新。")

        # 对比哈希前7位（例如成本因子、盐长度等信息）
        print(f"【对比】存储哈希前7位：{stored_hash[:7]}")
        print(f"【对比】新哈希前7位：{new_hash[:7]}")

        # 输出环境中 bcrypt 与 passlib 的版本信息
        try:
            import bcrypt
            print(f"【环境】bcrypt 版本：{bcrypt.__version__}")
        except Exception as e:
            print(f"【错误】获取 bcrypt 版本失败：{e}")

        try:
            import passlib
            from passlib import __version__ as passlib_version
            print(f"【环境】passlib 版本：{passlib_version}")
        except Exception as e:
            print(f"【错误】获取 passlib 版本失败：{e}")

if __name__ == '__main__':
    if len(sys.argv) < 3:
        print("Usage: python diagnose.py <email> <plain_password>")
        sys.exit(1)
    email_arg = sys.argv[1]
    password_arg = sys.argv[2]
    asyncio.run(diagnose(email_arg, password_arg))