# File: CheckEasyBackend/app/modules/auth/forgot_password/utils.py

import secrets
import logging
from datetime import datetime, timedelta
from typing import Any

from app.core.config import settings
from app.core.email import send_email
from app.core.security import hash_password  # 导入用于更新密码的哈希函数
import re

logger = logging.getLogger("CheckEasyBackend.auth.forgot_password.utils")


def generate_reset_token(email: str) -> str:
    """
    生成用于重置密码的 Token。
    使用 cryptographically secure 随机数生成器生成 URL 安全的随机字符串。

    Args:
        email (str): 用户邮箱

    Returns:
        str: 生成的重置 Token
    """
    token = secrets.token_urlsafe(32)
    logger.info("Generated reset token for email: %s", email)
    return token


def send_reset_email(email: str, reset_token: str) -> None:
    """
    发送重置密码邮件，将重置密码链接发送给用户。
    构造重置链接并调用邮件模块发送邮件。

    Args:
        email (str): 用户邮箱
        reset_token (str): 重置密码 Token（此处实际存储在激活字段中）
    """
    # 构造重置链接，确保 settings.APP_BASE_URL 配置正确，例如 "http://127.0.0.1:8000"
    reset_link = f"{settings.APP_BASE_URL}/api/v1/auth/reset-password?token={reset_token}"
    subject = "Reset Your Password"
    content = (
        f"Dear user,\n\n"
        f"Please click the link below to reset your password:\n{reset_link}\n\n"
        f"If you did not request a password reset, please ignore this email.\n\n"
        f"Best regards,\nYour Team"
    )
    try:
        # 直接调用同步的 send_email 函数
        send_email(
            to=email,
            subject=subject,
            body=content,
            from_email=settings.SMTP_USER
        )
        logger.info("Reset password email sent successfully to %s", email)
    except Exception as e:
        logger.error("Failed to send reset password email to %s: %s", email, str(e), exc_info=True)
        raise

def validate_password_complexity(password: str) -> bool:
    """
    验证密码复杂性，密码必须至少8位，包含至少一个字母和一个数字。
    """
    if len(password) < 8:
        return False
    if not re.search(r"[A-Za-z]", password):
        return False
    if not re.search(r"\d", password):
        return False
    return True

def verify_reset_token(provided_token: str, user_email: str) -> bool:
    """
    验证用户提交的重置密码 Token 是否有效。
    这里可以扩展实际的验证逻辑，本示例简单返回 True。

    Args:
        provided_token (str): 用户提交的 Token。
        user_email (str): 用户邮箱

    Returns:
        bool: 如果 token 有效返回 True，否则返回 False。
    """
    return True


def set_token_expiration(hours_valid: int = 1) -> datetime:
    """
    计算并返回重置密码 Token 的到期时间。

    Args:
        hours_valid (int): Token 有效时间（单位：小时），默认 1 小时。

    Returns:
        datetime: Token 到期时间。
    """
    expiration = datetime.utcnow() + timedelta(hours=hours_valid)
    logger.info("Set reset token expiration to %s", expiration.isoformat())
    return expiration

