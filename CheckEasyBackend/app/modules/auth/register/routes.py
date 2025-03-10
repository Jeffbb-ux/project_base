# 代码路径: CheckEasyBackend/app/modules/auth/register/routes.py

import logging
from uuid import uuid4
from fastapi import APIRouter, HTTPException, Request, status, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.auth.register.schemas import RegisterRequest, RegisterResponse
from app.modules.auth.register.utils import (
    get_user_by_email,
    create_user,
    hash_password,
    send_activation_email,
    verify_token_and_activate_user,
)
from app.core.db import get_async_db

router = APIRouter()
logger = logging.getLogger("CheckEasyBackend.auth.register")

@router.post(
    "/register",
    response_model=RegisterResponse,
    summary="用户注册接口",
    description=(
        "1. 如果邮箱已存在且已激活 -> 返回 409\n"
        "2. 如果邮箱已存在但未激活 -> 重发激活邮件\n"
        "3. 如果邮箱不存在 -> 创建用户并发送激活邮件"
    )
)
async def register(
    register_request: RegisterRequest,
    request: Request,
    db: AsyncSession = Depends(get_async_db)
):
    client_ip = request.client.host
    correlation_id = request.headers.get("X-Correlation-ID", str(uuid4()))

    logger.info(
        "Register attempt",
        extra={"email": register_request.email, "client_ip": client_ip, "correlation_id": correlation_id}
    )
    
    existing_user = await get_user_by_email(db, register_request.email)
    if existing_user:
        if existing_user.is_active:
            logger.warning(
                "User already exists and is active",
                extra={"email": register_request.email, "client_ip": client_ip, "correlation_id": correlation_id}
            )
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="User with given email already exists and is active"
            )
        else:
            logger.info(
                "User exists but not active, re-sending activation email",
                extra={"email": register_request.email, "client_ip": client_ip, "correlation_id": correlation_id}
            )

            logger.info(f"🔄 Calling send_activation_email() for {existing_user.email}")

            await send_activation_email(db, existing_user.email, existing_user.id)

            logger.info(f"📩 Activation email function called successfully for {existing_user.email}")

            return RegisterResponse(
                message="User already registered but not activated. We have resent the activation email. Please check your inbox.",
                user_id=existing_user.id,  # ✅ 修复：确保返回 user_id
            )
    
    #hashed_pw = hash_password(register_request.password)

    try:
        user = await create_user(
            db,
            username=register_request.email,
            password=register_request.password,
            email=register_request.email
        )
    except Exception as e:
        logger.error(
            "User creation failed",
            extra={"email": register_request.email, "error": str(e), "correlation_id": correlation_id},
            exc_info=True
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="User creation failed"
        )
    
    try:
        logger.info(f"🔄 Calling send_activation_email() for newly registered user {user.email}")

        await send_activation_email(db, user.email, user.id)

        logger.info(f"📩 Activation email function called successfully for newly registered user {user.email}")

    except Exception as e:
        logger.error(
            "Failed to send activation email",
            extra={"email": register_request.email, "error": str(e), "correlation_id": correlation_id},
            exc_info=True
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to send activation email"
        )
    
    logger.info(
        "User registered successfully",
        extra={"email": register_request.email, "client_ip": client_ip, "correlation_id": correlation_id}
    )
    
    return RegisterResponse(
        message="Registration successful, please check your email to activate your account",
        user_id=user.id
    )


@router.get("/register/confirm", summary="邮箱激活接口")
async def confirm_email(
    token: str,
    request: Request,
    db: AsyncSession = Depends(get_async_db)
):
    correlation_id = request.headers.get("X-Correlation-ID", str(uuid4()))
    logger.info("Email confirmation attempt", extra={"token": token, "correlation_id": correlation_id})
    
    success = await verify_token_and_activate_user(db, token)
    if not success:
        logger.warning("Invalid or expired token", extra={"token": token, "correlation_id": correlation_id})
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired token"
        )
    
    logger.info("Email confirmed", extra={"token": token, "correlation_id": correlation_id})
    return {"message": "Email verified successfully. You can now log in."}