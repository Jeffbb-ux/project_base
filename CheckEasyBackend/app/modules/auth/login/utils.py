# File: CheckEasyBackend/app/modules/auth/login/utils.py

import os
import logging
import jwt
from datetime import datetime, timedelta, timezone
from sqlalchemy.future import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.security import verify_password  # 使用统一的验证函数
from app.modules.auth.register.models import User

logger = logging.getLogger("CheckEasyBackend.auth.login.utils")

# 从环境变量加载 JWT 配置
JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY", "your-secret-key")
JWT_ALGORITHM = os.getenv("JWT_ALGORITHM", "HS256")
JWT_EXPIRE_MINUTES = int(os.getenv("JWT_EXPIRE_MINUTES", "30"))
TOKEN_PREFIX = os.getenv("TOKEN_PREFIX", "token-for-")

def hash_password(password: str) -> str:
    """
    对密码进行 bcrypt 哈希处理，内置加盐。
    """
    try:
        import bcrypt  # 如果需要在这里使用，可以单独使用，但建议统一使用 app.core.security.hash_password
        hashed = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
        return hashed
    except Exception as e:
        logger.error("Error hashing password: %s", e, exc_info=True)
        raise

async def verify_credentials(email: str, password: str, db: AsyncSession) -> bool:
    """
    验证用户凭据：
    1. 通过 ORM 查询数据库中对应 email 的用户记录。
    2. 使用统一的 verify_password 对比提交的密码与数据库中存储的哈希值。
    3. 返回 True 表示验证成功，否则返回 False。
    """
    try:
        result = await db.execute(select(User).filter(User.email == email))
        user = result.scalars().first()
        if not user:
            logger.warning("User not found: %s", email)
            return False

        # 使用统一的密码验证函数
        if verify_password(password, user.hashed_password):
            logger.info("User credentials verified for: %s", email)
            return True
        else:
            logger.warning("Password mismatch for user: %s", email)
            return False
    except Exception as e:
        logger.error(
            "Exception during credential verification for user %s: %s",
            email,
            e,
            exc_info=True
        )
        return False