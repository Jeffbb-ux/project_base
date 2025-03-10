# File: CheckEasyBackend/app/core/oauth.py

import requests
import logging
from urllib.parse import urlencode
from app.core.config import settings

logger = logging.getLogger("CheckEasyBackend.core.oauth")

def get_google_authorization_url() -> str:
    """
    构造并返回 Google OAuth 授权 URL。

    该 URL 包含必要的参数，如 client_id、redirect_uri、scope、response_type 等，
    供用户跳转到 Google 授权页面。

    Returns:
        str: 完整的 Google OAuth 授权 URL。
    """
    params = {
        "client_id": settings.GOOGLE_CLIENT_ID,
        "redirect_uri": settings.GOOGLE_REDIRECT_URI,
        "response_type": "code",
        "scope": "openid email profile",
        "access_type": "offline",  # 请求刷新令牌
        "prompt": "consent"  # 强制显示同意页面，以确保获取 refresh_token
        # 可选添加 state 参数用于防止 CSRF 攻击，如："state": "your_state_value"
    }
    base_url = "https://accounts.google.com/o/oauth2/v2/auth"
    auth_url = f"{base_url}?{urlencode(params)}"
    logger.info("Generated Google OAuth authorization URL: %s", auth_url)
    return auth_url

def exchange_google_code_for_token(code: str) -> dict:
    """
    使用授权码向 Google 的 Token 端点交换 access_token（以及 refresh_token 等信息）。

    参数:
        code (str): 从 Google 授权回调中获取的授权码。

    Returns:
        dict: 包含 access_token、refresh_token、expires_in 等字段的字典，
              如果失败则返回包含错误信息的字典，例如 {"error": "error message"}。
    """
    token_url = "https://oauth2.googleapis.com/token"
    data = {
        "code": code,
        "client_id": settings.GOOGLE_CLIENT_ID,
        "client_secret": settings.GOOGLE_CLIENT_SECRET,
        "redirect_uri": settings.GOOGLE_REDIRECT_URI,
        "grant_type": "authorization_code"
    }
    try:
        response = requests.post(token_url, data=data, timeout=10)
        response.raise_for_status()
        token_data = response.json()
        logger.info("Exchanged authorization code for token successfully.")
        return token_data
    except requests.RequestException as e:
        logger.error("Error exchanging code for token: %s", e, exc_info=True)
        return {"error": str(e)}

def get_google_user_info(access_token: str) -> dict:
    """
    使用 access_token 向 Google 的 UserInfo 端点请求用户信息。

    参数:
        access_token (str): Google OAuth 授权后获取的 access_token。

    Returns:
        dict: 包含用户信息的字典，如 email、name、picture 等，
              如果失败则返回包含错误信息的字典，例如 {"error": "error message"}。
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