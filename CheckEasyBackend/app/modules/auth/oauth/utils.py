# File: CheckEasyBackend/app/modules/auth/oauth/utils.py

import logging
import httpx
import jwt
from datetime import datetime, timedelta
from typing import Any, Dict
from sqlalchemy.future import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings  # 全局配置模块，包含 OAuth、JWT 等配置
from app.modules.auth.register.models import User  # 用户 ORM 模型

logger = logging.getLogger("CheckEasyBackend.auth.oauth.utils")

async def exchange_code_for_token(code: str) -> Dict[str, Any]:
    """
    使用授权码交换 OAuth 提供商的访问令牌
    真实项目中需调用 OAuth 提供商的 Token 接口。
    """
    try:
        data = {
            "grant_type": "authorization_code",
            "code": code,
            "redirect_uri": settings.OAUTH_REDIRECT_URI,
            "client_id": settings.OAUTH_CLIENT_ID,
            "client_secret": settings.OAUTH_CLIENT_SECRET,
        }
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.post(settings.OAUTH_TOKEN_URL, data=data)
            response.raise_for_status()
            token_data = response.json()
            logger.info("Exchanged code for token successfully", extra={"code": code})
            return token_data
    except Exception as e:
        logger.error("Error exchanging code for token: %s", e, exc_info=True)
        raise

async def get_user_info_from_provider(access_token: str) -> Dict[str, Any]:
    """
    使用访问令牌从 OAuth 提供商获取用户信息
    真实项目中需调用 OAuth 提供商的用户信息接口，返回的数据格式由各家决定。
    """
    try:
        headers = {"Authorization": f"Bearer {access_token}"}
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(settings.OAUTH_USERINFO_URL, headers=headers)
            response.raise_for_status()
            user_info = response.json()
            logger.info("Fetched user info from provider successfully", extra={"access_token": access_token})
            return user_info
    except Exception as e:
        logger.error("Error fetching user info from provider: %s", e, exc_info=True)
        raise

async def create_or_update_user_from_oauth(oauth_user_info: Dict[str, Any], db: AsyncSession) -> User:
    """
    根据 OAuth 返回的用户信息，在真实数据库中创建或更新本地用户账户
    假设 oauth_user_info 包含 'email', 'name', 'avatar', 'provider' 等信息。
    如果用户已存在（以邮箱为唯一标识），则更新用户信息，否则创建新用户。
    """
    try:
        email = oauth_user_info.get("email")
        if not email:
            raise ValueError("OAuth user info missing email")

        result = await db.execute(select(User).filter(User.email == email))
        user = result.scalars().first()
        if user:
            # 更新用户信息（如用户名、头像等），这里根据需求自行扩展更新逻辑
            user.username = oauth_user_info.get("name") or user.username
            # 如有其他字段（如头像、来源平台等）也可在此更新
            logger.info("Updated existing user from OAuth info", extra={"user_id": user.id})
        else:
            # 生成用户名：例如使用邮箱前缀或第三方 id 生成唯一用户名
            username = oauth_user_info.get("name") or email.split("@")[0]
            user = User(
                username=username,
                email=email,
                hashed_password="",  # OAuth 登录无需密码，或存储随机密码
                is_active=True,      # OAuth 用户默认激活（可根据实际业务调整）
            )
            db.add(user)
            logger.info("Created new user from OAuth info", extra={"username": username})
        await db.commit()
        await db.refresh(user)
        return user
    except Exception as e:
        logger.error("Error creating/updating user from OAuth info: %s", e, exc_info=True)
        raise

def create_jwt_token(username: str) -> str:
    """
    根据用户名生成 JWT Token。
    Token 包含用户名（sub）和过期时间（exp），使用全局配置中定义的密钥和算法。
    """
    try:
        expire = datetime.utcnow() + timedelta(minutes=settings.JWT_EXPIRE_MINUTES)
        payload = {"sub": username, "exp": expire}
        token = jwt.encode(payload, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)
        logger.info("Generated JWT token for user", extra={"username": username})
        return token
    except Exception as e:
        logger.error("Error generating JWT token for user %s: %s", username, e, exc_info=True)
        raise