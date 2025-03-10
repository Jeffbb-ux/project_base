# 代码路径: CheckEasyBackend/app/core/dependencies.py

import uuid
from fastapi import Depends, Request, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
import jwt
from jwt import InvalidTokenError
from fastapi.security import OAuth2PasswordBearer
import logging
import os

from app.core.config import settings
from app.core.db import get_async_db
from app.modules.auth.register.models import User

logger = logging.getLogger("CheckEasyBackend.core.dependencies")

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="api/v1/auth/login")

def get_correlation_id(request: Request) -> str:
    return request.headers.get("X-Correlation-ID", str(uuid.uuid4()))


async def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: AsyncSession = Depends(get_async_db)
):
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        email: str = payload.get("sub")
        if email is None:
            logger.error("JWT token decoded but email is missing")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token does not contain email",
                headers={"WWW-Authenticate": "Bearer"},
            )
    except jwt.PyJWTError as e:
        logger.error("JWT Decode Error: %s", str(e), exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Invalid authentication credentials: {str(e)}",
            headers={"WWW-Authenticate": "Bearer"},
        )

    result = await db.execute(select(User).where(User.email == payload.get("sub")))
    user = result.scalar_one_or_none()

    if user is None:
        logger.error("User with email '%s' not found", payload.get("sub"))
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return user