# File: CheckEasyBackend/app/modules/auth/forgot_password/routes.py

from datetime import datetime, timedelta
import logging
from uuid import uuid4

from fastapi import APIRouter, HTTPException, Request, status, Depends
from fastapi.responses import JSONResponse
from fastapi.concurrency import run_in_threadpool
from sqlalchemy.future import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.db import get_async_db  
from app.modules.auth.forgot_password.schemas import (
    ForgotPasswordRequest,
    ForgotPasswordResponse,
    ResetPasswordRequest,
    ResetPasswordResponse,
)
from app.modules.auth.forgot_password.utils import (
    generate_reset_token,
    verify_reset_token,
    send_reset_email,
    hash_password,
    validate_password_complexity,
)
from app.modules.auth.register.models import User  # 用户 ORM 模型

router = APIRouter()
logger = logging.getLogger("CheckEasyBackend.auth.forgot_password.routes")


@router.post(
    "/forgot-password",
    response_model=ForgotPasswordResponse,
    summary="忘记密码请求接口",
    description="用户提交邮箱请求忘记密码，系统生成重置密码 Token 并发送到用户邮箱。"
)
async def forgot_password(
    request_data: ForgotPasswordRequest,
    request: Request,
    db: AsyncSession = Depends(get_async_db)
):
    """
    1. 根据提交的邮箱查询用户记录。
    2. 生成重置密码 Token（带唯一标识和过期时间）。
    3. 存储 Token 与过期时间到用户记录中（共用激活字段）。
    4. 异步发送重置密码邮件，将 Token 嵌入邮件中。
    5. 返回操作提示信息。
    """
    result = await db.execute(
        select(User).where(User.email == request_data.email)
    )
    user = result.scalars().first()
    if not user:
        logger.warning("User with email not found", extra={"email": request_data.email})
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User with this email not found")
    
    # 方案2：共用激活字段作为重置密码的 Token 存储
    reset_token = generate_reset_token(request_data.email)
    user.activation_token = reset_token
    user.token_expires = datetime.utcnow() + timedelta(hours=1)
    await db.commit()

    try:
        # 使用 run_in_threadpool 调用同步的 send_reset_email
        await run_in_threadpool(send_reset_email, email=request_data.email, reset_token=reset_token)
    except Exception as e:
        logger.error("Failed to send reset password email", extra={"email": request_data.email, "error": str(e)})
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to send reset email")

    logger.info("Reset password email sent", extra={"email": request_data.email})
    return ForgotPasswordResponse(message="Reset password email sent")


@router.post(
    "/reset-password",
    response_model=ResetPasswordResponse,
    summary="重置密码接口",
    description="用户通过重置密码 Token 提交新密码，系统验证 Token 并更新用户密码。"
)
async def reset_password(
    request_data: ResetPasswordRequest,
    request: Request,
    db: AsyncSession = Depends(get_async_db)
):
    # 先验证密码复杂性（加在此处✅）
    if not validate_password_complexity(request_data.new_password):
        logger.warning("Password complexity validation failed", extra={"email": request_data.email})
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Password must be at least 8 characters long and include at least one letter and one number."
        )
    
    # 修改查询条件，使用 activation_token 作为重置密码的 Token
    result = await db.execute(
        select(User).where(User.activation_token == request_data.token)
    )
    user = result.scalars().first()
    if not user:
        logger.warning("Invalid reset token", extra={"token": request_data.token})
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid or expired reset token")
    
    if user.token_expires is None or user.token_expires < datetime.utcnow():
        logger.warning("Reset token expired", extra={"token": request_data.token})
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Reset token has expired")
    
    if not verify_reset_token(request_data.token, user.email):
        logger.warning("Reset token verification failed", extra={"token": request_data.token})
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid reset token")
    
    new_hashed_password = hash_password(request_data.new_password)
    user.hashed_password = new_hashed_password
    # 重置激活字段
    user.activation_token = None
    user.token_expires = None
    await db.commit()

    logger.info("Password reset successful", extra={"user_id": user.id})
    return ResetPasswordResponse(message="Password reset successful.")