# 文件路径: CheckEasyBackend/app/modules/auth/login/routes.py

import os
import jwt
import logging
from datetime import datetime, timedelta, timezone
from uuid import uuid4
from fastapi import APIRouter, HTTPException, Request, status, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from app.modules.auth.register.models import User

from app.core.db import get_async_db
from app.core.config import settings  # 🚩 修复：统一使用 settings 配置
from app.core.dependencies import get_correlation_id
from app.modules.auth.login.schemas import LoginRequest, LoginResponse
from app.modules.auth.login.utils import verify_credentials
from app.core.security import verify_password

router = APIRouter()
logger = logging.getLogger("CheckEasyBackend.auth.login")

class TokenService:
    @staticmethod
    def create_access_token(email: str) -> str:
        expire = datetime.now(timezone.utc) + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
        payload = {"sub": email, "exp": expire}
        token = jwt.encode(payload, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
        logger.debug("Token generated for %s with payload: %s", email, payload)
        return token

async def get_user_agent(request: Request) -> str:
    return request.headers.get("User-Agent", "unknown")

@router.post(
    "/login",
    response_model=LoginResponse,
    summary="用户登录接口",
    description="用户通过用户名和密码登录系统，验证成功后返回 JWT Token。"
)
async def login(
    login_request: LoginRequest,
    request: Request,
    db: AsyncSession = Depends(get_async_db),
):
    client_ip = request.client.host
    correlation_id = get_correlation_id(request)
    user_agent = request.headers.get("User-Agent", "unknown")

    logger.info(
        "Login attempt",
        extra={
            "email": login_request.email,
            "client_ip": client_ip,
            "correlation_id": correlation_id,
            "method": request.method,
            "url": request.url.path,
            "user_agent": user_agent
        }
    )

    # 详细查询用户记录，并记录调试日志
    try:
        result = await db.execute(select(User).filter(User.email == login_request.email))
        user = result.scalars().first()
        if user:
            logger.debug("Queried user record: %s", user)
            logger.debug("User details - email: %s, is_active: %s, verification_status: %s, hashed_password: %s",
                         user.email, user.is_active, user.verification_status, user.hashed_password)
        else:
            logger.warning("User not found for email: %s", login_request.email)
    except Exception as e:
        logger.exception("Exception querying user: %s", e)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Database query error")
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password"
        )

    # 调用验证函数前，直接使用 verify_password 进行测试（调试用）
    direct_verify = verify_password(login_request.password, user.hashed_password)
    logger.debug("Direct verify_password(%s, %s) returned: %s", login_request.password, user.hashed_password, direct_verify)

    # 使用登录模块中的 verify_credentials 进行验证
    credentials_valid = await verify_credentials(login_request.email, login_request.password, db)
    logger.debug("verify_credentials returned: %s", credentials_valid)

    if not credentials_valid:
        logger.warning(
            "Invalid email or password (post verify_credentials)",
            extra={
                "email": login_request.email,
                "client_ip": client_ip,
                "correlation_id": correlation_id
            }
        )
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password"
        )

    # 生成 JWT token 并记录调试日志
    try:
        access_token = TokenService.create_access_token(login_request.email)
    except Exception as e:
        logger.error(
            "Error generating token for %s: %s", login_request.email, str(e), exc_info=True
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Token generation failed"
        )

    logger.info(
        "User logged in successfully",
        extra={
            "email": login_request.email,
            "client_ip": client_ip,
            "correlation_id": correlation_id
        }
    )

    # 输出最终调试日志，对比直接验证和 verify_credentials
    logger.debug("Final debug - Direct verify: %s, verify_credentials: %s", direct_verify, credentials_valid)

    return LoginResponse(message="Login successful", token=access_token)