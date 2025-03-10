# File: CheckEasyBackend/app/core/security.py

import jwt
import logging
from passlib.context import CryptContext
from datetime import datetime, timedelta
from typing import Optional, Union
from app.core.config import settings

logger = logging.getLogger("CheckEasyBackend.core.security")

# 初始化密码哈希上下文，使用 bcrypt 算法
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(password: str) -> str:
    """
    使用 bcrypt 算法生成密码哈希。

    Returns:
        str: 加密后的密码哈希。
    """
    try:
        hashed = pwd_context.hash(password)
        logger.debug("Password hashed successfully.")
        return hashed
    except Exception as e:
        logger.error("Error hashing password: %s", e, exc_info=True)
        raise


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    验证明文密码是否与数据库中存储的哈希密码一致。

    Args:
        plain_password (str): 用户输入的明文密码。
        hashed_password (str): 数据库中存储的密码哈希。

    Returns:
        bool: 如果匹配返回 True，否则返回 False。
    """
    try:
        valid = pwd_context.verify(plain_password, hashed_password)
        logger.debug("Password verification result: %s", valid)
        return valid
    except Exception as e:
        logger.error("Error verifying password: %s", e, exc_info=True)
        return False


def create_access_token(
    data: dict, 
    expires_delta: Optional[timedelta] = None
) -> str:
    """
    创建并返回一个 JWT access token。

    Args:
        data (dict): 令牌中携带的自定义信息（例如 user_id）。
        expires_delta (Optional[timedelta]): 令牌过期时间的 timedelta，默认15分钟。

    Returns:
        str: 编码后的 JWT access token 字符串。
    """
    try:
        to_encode = data.copy()
        if expires_delta:
            expire = datetime.utcnow() + expires_delta
        else:
            expire = datetime.utcnow() + timedelta(minutes=15)
        to_encode.update({"exp": expire})
        encoded_jwt = jwt.encode(
            to_encode, 
            settings.SECRET_KEY, 
            algorithm=settings.ALGORITHM
        )
        logger.info("Access token created successfully, expires at %s", expire.isoformat())
        return encoded_jwt
    except Exception as e:
        logger.error("Error creating access token: %s", e, exc_info=True)
        raise


def decode_access_token(token: str) -> Union[dict, None]:
    """
    解码并验证给定的 JWT token。

    Args:
        token (str): 待验证的 JWT token 字符串。

    Returns:
        Union[dict, None]: 成功时返回 payload 字典，否则返回 None。
    """
    try:
        payload = jwt.decode(
            token, 
            settings.SECRET_KEY, 
            algorithms=[settings.ALGORITHM]
        )
        logger.debug("Access token decoded successfully: %s", payload)
        return payload
    except jwt.PyJWTError as e:
        logger.error("Error decoding access token: %s", e, exc_info=True)
        return None


def create_refresh_token(
    data: dict, 
    expires_delta: Optional[timedelta] = None
) -> str:
    """
    创建并返回一个 JWT refresh token，用于在 access token 过期时生成新的 access token。

    Args:
        data (dict): 令牌中携带的自定义信息（例如 user_id）。
        expires_delta (Optional[timedelta]): 令牌过期时间的 timedelta，默认 1440 分钟（24小时）。

    Returns:
        str: 编码后的 JWT refresh token 字符串。
    """
    try:
        to_encode = data.copy()
        if expires_delta:
            expire = datetime.utcnow() + expires_delta
        else:
            expire = datetime.utcnow() + timedelta(minutes=1440)
        # 增加 token 类型区分
        to_encode.update({"exp": expire, "type": "refresh"})
        refresh_jwt = jwt.encode(
            to_encode,
            settings.SECRET_KEY,
            algorithm=settings.ALGORITHM
        )
        logger.info("Refresh token created successfully, expires at %s", expire.isoformat())
        return refresh_jwt
    except Exception as e:
        logger.error("Error creating refresh token: %s", e, exc_info=True)
        raise