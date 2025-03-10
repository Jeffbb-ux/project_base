import requests
import logging
from urllib.parse import urlencode
from datetime import datetime, timedelta
from typing import Dict, Any

from app.core.config import settings
from app.core.security import create_access_token  # 从 security 模块调用 JWT 生成函数
from app.modules.auth.register.models import User
from sqlalchemy.future import select
from sqlalchemy.ext.asyncio import AsyncSession

logger = logging.getLogger("CheckEasyBackend.auth.oauth.services")

def get_google_authorization_url() -> str:
    """
    构造并返回 Google OAuth 授权 URL。

    返回的 URL 包含必要参数，如 client_id、redirect_uri、scope、response_type、access_type 和 prompt，
    供用户跳转到 Google 授权页面。

    Returns:
        str: 完整的 Google OAuth 授权 URL。
    """
    params = {
        "client_id": settings.OAUTH_CLIENT_ID,
        "redirect_uri": settings.OAUTH_REDIRECT_URI,
        "response_type": "code",
        "scope": "openid email profile",
        "access_type": "offline",  # 请求刷新令牌
        "prompt": "consent"         # 强制显示同意页面
    }
    base_url = "https://accounts.google.com/o/oauth2/v2/auth"
    auth_url = f"{base_url}?{urlencode(params)}"
    logger.info("Generated Google OAuth authorization URL: %s", auth_url)
    return auth_url

def exchange_code_for_token(code: str) -> Dict[str, Any]:
    """
    使用授权码向 Google 的 Token 端点交换 access_token 和 refresh_token。

    Args:
        code (str): 从 Google 授权回调中获得的授权码。

    Returns:
        dict: 包含 access_token、refresh_token、expires_in 等信息的字典；出错时返回包含错误信息的字典。
    """
    token_url = "https://oauth2.googleapis.com/token"
    data = {
        "code": code,
        "client_id": settings.OAUTH_CLIENT_ID,
        "client_secret": settings.OAUTH_CLIENT_SECRET,
        "redirect_uri": settings.OAUTH_REDIRECT_URI,
        "grant_type": "authorization_code"
    }
    headers = {"Content-Type": "application/x-www-form-urlencoded"}
    try:
        response = requests.post(token_url, data=data, headers=headers, timeout=10)
        logger.info("Google token response status: %s", response.status_code)
        logger.info("Google token response text: %s", response.text)  # 关键调试信息
        response.raise_for_status()
        token_data = response.json()
        logger.info("Exchanged authorization code for token successfully.")
        return token_data
    except requests.RequestException as e:
        logger.error("Error exchanging code for token: %s", e, exc_info=True)
        return {"error": str(e)}

def get_user_info_from_provider(access_token: str) -> Dict[str, Any]:
    """
    使用 access_token 向 Google 的 UserInfo 端点请求用户信息。

    Args:
        access_token (str): Google OAuth 授权后获取的 access_token。

    Returns:
        dict: 包含用户信息的字典，如 email、name、picture 等；出错时返回包含错误信息的字典。
    """
    userinfo_url = "https://www.googleapis.com/oauth2/v3/userinfo"
    headers = {
        "Authorization": f"Bearer {access_token}"
    }
    try:
        response = requests.get(userinfo_url, headers=headers, timeout=10)
        response.raise_for_status()
        user_info = response.json()
        logger.info("Fetched Google user info successfully.")
        return user_info
    except requests.RequestException as e:
        logger.error("Error fetching Google user info: %s", e, exc_info=True)
        return {"error": str(e)}

async def create_or_update_user_from_oauth(oauth_user_info: Dict[str, Any], db: AsyncSession) -> User:
    """
    根据 OAuth 返回的用户信息，在真实数据库中创建或更新本地用户账户。

    Args:
        oauth_user_info (dict): 包含第三方用户信息的字典（例如 email、name、picture）。
        db (AsyncSession): 异步数据库会话，用于查询和更新用户数据。

    Returns:
        User: 更新或新创建的用户 ORM 对象。

    Raises:
        ValueError: 如果 oauth_user_info 中不包含 email 信息，或未提供数据库会话。
    """
    email = oauth_user_info.get("email")
    if not email:
        raise ValueError("OAuth user info does not contain email.")
    if db is None:
        raise ValueError("Database session must be provided.")
    
    result = await db.execute(select(User).where(User.email == email))
    user = result.scalars().first()
    if user:
        user.username = oauth_user_info.get("name", user.username)
        logger.info("Updated existing user with email: %s", email)
    else:
        user = User(
            username=oauth_user_info.get("name"),
            email=email,
            hashed_password="",  # OAuth 用户无需密码登录，可后续通过其他方式设置密码
            is_active=True
        )
        db.add(user)
        logger.info("Created new user with email: %s", email)
    await db.commit()
    await db.refresh(user)
    return user

class TokenService:
    """
    Token 服务，用于生成 access token。
    """
    @staticmethod
    def create_access_token(user: User, expires_delta: timedelta = None) -> str:
        """
        根据用户信息生成 JWT access token。

        Args:
            user (User): 用户 ORM 对象。
            expires_delta (timedelta, optional): 令牌过期时间。默认为 settings.ACCESS_TOKEN_EXPIRE_MINUTES 分钟。

        Returns:
            str: 生成的 JWT token 字符串。
        """
        payload = {"sub": str(user.id)}
        if expires_delta:
            expire = datetime.utcnow() + expires_delta
        else:
            expire = datetime.utcnow() + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
        payload.update({"exp": expire})
        token = create_access_token(payload, expires_delta)  # 调用 core.security 中的函数
        logger.info("Access token created for user_id: %s, expires at %s", user.id, expire.isoformat())
        return token

def validate_state_parameter(state: str, expected_state: str) -> bool:
    """
    校验 state 参数，防止 CSRF 攻击。

    Args:
        state (str): 从 OAuth 回调中获得的 state 参数。
        expected_state (str): 预期的 state 值（通常是请求时生成的 correlation_id）。

    Returns:
        bool: 如果 state 符合预期返回 True，否则返回 False。
    """
    valid = state == expected_state
    if not valid:
        logger.warning("State parameter validation failed: received %s, expected %s", state, expected_state)
    return valid