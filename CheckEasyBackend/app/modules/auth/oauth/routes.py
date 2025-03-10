# File: CheckEasyBackend/app/modules/auth/oauth/routes.py

import logging
import uuid
from urllib.parse import urlencode

from fastapi import APIRouter, HTTPException, Request, status, Depends
from fastapi.responses import RedirectResponse, JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.redis_client import r  # 引入 Redis 客户端
from app.core.db import get_async_db  # 数据库依赖，返回 AsyncSession
from app.core.config import settings  # 全局配置模块

# 业务/服务层函数，需要你在对应文件中自行实现
from app.modules.auth.oauth.schemas import OAuthCallbackResponse
from app.modules.auth.oauth.services import (
    exchange_code_for_token,
    get_user_info_from_provider,
    create_or_update_user_from_oauth,
    TokenService,
    validate_state_parameter,
)

router = APIRouter()
logger = logging.getLogger("CheckEasyBackend.auth.oauth")

@router.get("/login", summary="第三方 OAuth 登录入口", description="重定向到 OAuth 提供商的认证页面")
async def oauth_login():
    """
    1. 生成随机 state
    2. 将 state 存储在 Redis 中，设置有效期（例如 600 秒）
    3. 构造 OAuth 授权 URL，将 state 附加到参数中
    4. 重定向到 OAuth 提供商
    """
    # 生成随机 state
    state = str(uuid.uuid4())
    redis_key = f"oauth_state:{state}"
    # 将 state 存入 Redis，并设置 10 分钟（600 秒）的过期时间
    r.setex(redis_key, 600, "active")
    
    # 构造授权 URL
    params = {
        "client_id": settings.OAUTH_CLIENT_ID,
        "redirect_uri": settings.OAUTH_REDIRECT_URI,
        "response_type": "code",
        "scope": settings.OAUTH_SCOPE,
        "state": state,
    }
    auth_url = f"{settings.OAUTH_AUTHORIZE_URL}?{urlencode(params)}"
    logger.info("Redirecting to OAuth provider", extra={"auth_url": auth_url, "state": state})
    return RedirectResponse(auth_url)

@router.get("/callback", summary="OAuth 回调接口", description="处理 OAuth 提供商返回的授权信息")
async def oauth_callback(
    request: Request,
    code: str = None,
    state: str = None,
    error: str = None,
    db: AsyncSession = Depends(get_async_db)  # 注入数据库会话
):
    """
    1. 从 URL 参数中获取 state 和 code，并校验 state 在 Redis 中是否存在
    2. 如果 state 无效或过期，则返回 400
    3. 使用 code 与 OAuth 提供商交换 access token，并获取用户信息
    4. 根据用户信息在本地创建或更新用户，并生成 JWT 登录态
    """
    if error:
        logger.error("OAuth provider returned error", extra={"error": error, "state": state})
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"OAuth error: {error}"
        )
    
    if not state or not code:
        logger.error("Missing state or authorization code", extra={"state": state})
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="State and authorization code are required"
        )
    
    # 校验 state：从 Redis 中获取对应记录
    redis_key = f"oauth_state:{state}"
    stored_state = r.get(redis_key)
    if not stored_state:
        logger.error("Invalid or expired state", extra={"state": state})
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid or expired state")
    
    # 状态校验成功后，删除该记录以防重放攻击
    r.delete(redis_key)
    
    user_agent = request.headers.get("User-Agent", "unknown")
    logger.info("OAuth callback received", extra={"code": code, "state": state, "user_agent": user_agent})
    
    # 交换 code 得到 token 数据
    token_data = exchange_code_for_token(code)
    access_token = token_data.get("access_token")
    if not access_token:
        logger.error("Access token missing in token response", extra={"token_data": token_data, "state": state})
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Access token not provided"
        )
    
    try:
        # 获取 OAuth 提供商的用户信息
        oauth_user_info = get_user_info_from_provider(access_token)
    except Exception as e:
        logger.exception("Failed to fetch user info from OAuth provider", extra={"state": state})
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Failed to retrieve user information"
        )
    
    if not oauth_user_info:
        logger.error("OAuth user info is empty", extra={"state": state})
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User information retrieval failed"
        )
    
    try:
        # 根据用户信息在数据库中创建或更新用户
        user = await create_or_update_user_from_oauth(oauth_user_info, db)
        jwt_token = TokenService.create_access_token(user)
    except Exception as e:
        logger.exception("Error processing user data from OAuth", extra={"state": state})
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="User processing failed"
        )
    
    logger.info("OAuth login successful", extra={"username": user.username, "user_id": user.id, "state": state})
    
    # 构造符合 OAuthCallbackResponse 模型要求的用户数据字典
    user_data = {
        "id": str(user.id),
        "username": user.username,
        "email": user.email,
        "provider": "google"
    }
    
    response_data = OAuthCallbackResponse(
        message="OAuth login successful",
        token=jwt_token,
        user=user_data
    )
    return JSONResponse(content=response_data.dict())