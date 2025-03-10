# File: CheckEasyBackend/app/modules/checkin/routes.py

import logging
from fastapi import APIRouter, HTTPException, Request, status, Depends
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from app.core.db import get_async_db  # 使用异步数据库依赖
from app.modules.checkin.schemas import CheckinRequest, CheckinResponse
from app.modules.checkin.models import CheckinRecord
from app.modules.verification.ocr.utils import process_certificate_verification
from app.core.dependencies import get_current_user, get_correlation_id

router = APIRouter()
logger = logging.getLogger("CheckEasyBackend.checkin.routes")

@router.post(
    "/checkin",
    response_model=CheckinResponse,
    summary="用户入住接口",
    description=(
        "处理用户入住请求：\n"
        "1. 验证当前用户已登录；\n"
        "2. 调用证件验证逻辑验证上传的证件；\n"
        "3. 记录入住信息到数据库；\n"
        "4. 返回入住成功响应。"
    )
)
async def checkin(
    request_data: CheckinRequest,
    request: Request,
    db: AsyncSession = Depends(get_async_db),
    current_user = Depends(get_current_user),
    correlation_id: str = Depends(get_correlation_id)
):
    logger.info(
        "Received checkin request",
        extra={
            "user_id": current_user.id,
            "correlation_id": correlation_id,
            "room_number": request_data.room_number
        }
    )

    # 调用证件验证函数（同步函数，不使用 await）
    verification_result = process_certificate_verification(
        certificate_id=request_data.certificate_id,
        user_id=current_user.id
    )
    
    if not verification_result.get("valid", False):
        logger.warning(
            "Certificate verification failed",
            extra={
                "user_id": current_user.id,
                "correlation_id": correlation_id,
                "reason": verification_result.get("message")
            }
        )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Certificate verification failed: {verification_result.get('message')}"
        )

    try:
        # 如果传入的 checkin_time 包含时区信息，将其转换为天真的（naive）datetime对象
        naive_checkin_time = request_data.checkin_time.replace(tzinfo=None)
        new_checkin = CheckinRecord(
            user_id=current_user.id,
            certificate_id=request_data.certificate_id,
            checkin_time=naive_checkin_time,
            room_number=request_data.room_number,
            remarks=request_data.remarks,
            additional_info=request_data.additional_info
        )
        db.add(new_checkin)
        await db.commit()
        await db.refresh(new_checkin)
        logger.info(
            "Checkin record created successfully",
            extra={"checkin_id": new_checkin.id, "correlation_id": correlation_id}
        )
    except Exception as e:
        logger.error(
            "Failed to record checkin",
            extra={"error": str(e), "correlation_id": correlation_id},
            exc_info=True
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to record checkin information."
        )

    response = CheckinResponse(
        message="Check-in successful",
        checkin_id=new_checkin.id,
        user_id=current_user.id,
        user_name=current_user.username,
        certificate_id=request_data.certificate_id,
        checkin_time=new_checkin.checkin_time,  # 这里还是 datetime 类型
        room_number=new_checkin.room_number,
        remarks=new_checkin.remarks,
        additional_info=new_checkin.additional_info
    )
    
    # 将响应中的 datetime 转换为字符串
    response_data = response.dict()
    if response_data.get("checkin_time"):
        response_data["checkin_time"] = response_data["checkin_time"].isoformat()

    return JSONResponse(content=response_data)