# File: CheckEasyBackend/app/modules/checkin/utils.py

import logging
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from app.modules.checkin.models import CheckinRecord, CheckinStatus
from app.modules.user.models import User  # 假设用户模型在这里
# 若有证件模块，可从相应模块导入相关验证函数，如：verify_certificate()

logger = logging.getLogger("CheckEasyBackend.checkin.utils")


# ---------------------------
# 定义自定义异常
# ---------------------------
class CheckinException(Exception):
    """基础入住流程异常"""
    pass

class CertificateInvalidException(CheckinException):
    """证件无效或已过期异常"""
    pass

class UserBlacklistedException(CheckinException):
    """用户黑名单异常"""
    pass

class RoomOccupiedException(CheckinException):
    """房间已被占用异常"""
    pass

class ActiveCheckinExistsException(CheckinException):
    """用户已有活跃入住记录异常"""
    pass


# ---------------------------
# 业务规则验证函数
# ---------------------------
async def check_existing_active_checkin(user_id: int, db: AsyncSession) -> None:
    """
    检查用户是否已有活跃入住记录（状态为 'checked_in'）。
    若发现，则抛出 ActiveCheckinExistsException 异常。
    """
    try:
        query = select(CheckinRecord).where(
            CheckinRecord.user_id == user_id,
            CheckinRecord.status == CheckinStatus.checked_in
        )
        result = await db.execute(query)
        active_record = result.scalars().first()
        if active_record:
            raise ActiveCheckinExistsException(
                f"User {user_id} already has an active checkin (Checkin ID: {active_record.id})."
            )
    except Exception as e:
        logger.error("Error checking active checkin for user_id %s: %s", user_id, str(e), exc_info=True)
        raise


async def is_room_available(room_number: str, db: AsyncSession) -> None:
    """
    检查指定房间是否可用：即是否存在状态为 'checked_in' 的入住记录。
    若房间已被占用，则抛出 RoomOccupiedException 异常。
    """
    try:
        query = select(CheckinRecord).where(
            CheckinRecord.room_number == room_number,
            CheckinRecord.status == CheckinStatus.checked_in
        )
        result = await db.execute(query)
        occupied_record = result.scalars().first()
        if occupied_record:
            raise RoomOccupiedException(
                f"Room {room_number} is already occupied (Checkin ID: {occupied_record.id})."
            )
    except Exception as e:
        logger.error("Error checking room availability for room %s: %s", room_number, str(e), exc_info=True)
        raise


async def verify_user_eligibility(user_id: int, db: AsyncSession) -> None:
    """
    验证用户是否符合入住资格（例如：是否在黑名单中）。
    假设 User 模型有 'blacklisted' 字段表示用户是否被禁止入住。
    若用户不合格，则抛出 UserBlacklistedException 异常。
    """
    try:
        query = select(User).where(User.id == user_id)
        result = await db.execute(query)
        user = result.scalars().first()
        if user and getattr(user, "blacklisted", False):
            raise UserBlacklistedException(f"User {user_id} is blacklisted and cannot check in.")
    except Exception as e:
        logger.error("Error verifying eligibility for user_id %s: %s", user_id, str(e), exc_info=True)
        raise


async def validate_checkin(user_id: int, room_number: str, certificate_id: str, db: AsyncSession) -> None:
    """
    综合验证入住请求的业务规则：
      1. 检查用户是否已有活跃入住记录；
      2. 检查指定房间是否可用；
      3. 验证用户证件有效性（此处预留调用 Verification 模块逻辑）；
      4. 检查用户是否具备入住资格（例如不在黑名单中）。
    若任何一项验证失败，则抛出相应异常。
    """
    # 验证用户资格
    await verify_user_eligibility(user_id, db)
    # 检查用户是否已有活跃入住记录
    await check_existing_active_checkin(user_id, db)
    # 检查房间是否可用
    await is_room_available(room_number, db)
    # 预留：调用证件验证逻辑（例如，verify_certificate(certificate_id, user_id, db)）
    # 如果验证不通过，抛出 CertificateInvalidException
    logger.info("Checkin validation passed for user_id: %s, room: %s", user_id, room_number)


async def validate_checkin_request(user_id: int, room_number: str, certificate_id: str, db: AsyncSession) -> None:
    """
    综合入口函数，用于验证入住请求：
      - 验证用户资格（黑名单检查）；
      - 验证用户是否已有活跃入住；
      - 验证房间是否可用；
      - 预留证件有效性检查。
    若验证通过，则函数正常返回；否则，抛出相应异常。
    """
    await verify_user_eligibility(user_id, db)
    await check_existing_active_checkin(user_id, db)
    await is_room_available(room_number, db)
    # 调用证件有效性验证逻辑（如果有），例如：
    # certificate_valid = await verify_certificate(certificate_id, user_id, db)
    # if not certificate_valid:
    #     raise CertificateInvalidException("The provided certificate is invalid or expired.")
    logger.info("All checkin business rules validated for user_id: %s", user_id)