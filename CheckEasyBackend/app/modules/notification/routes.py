# File: CheckEasyBackend/app/modules/notification/routes.py

import logging
from fastapi import APIRouter, HTTPException, Request, status, Depends
from fastapi.responses import JSONResponse

from app.modules.notification.schemas import EmailNotificationRequest, NotificationResponse
from app.modules.notification.tasks import send_email_notification  # 企业级邮件任务
from app.core.dependencies import get_correlation_id  # 自定义依赖，用于获取或生成 correlation_id

router = APIRouter()
logger = logging.getLogger("CheckEasyBackend.notification.routes")

@router.post(
    "/email",
    response_model=NotificationResponse,
    summary="发送邮件通知",
    description="接收邮件通知请求并通过邮件服务发送通知。"
)
async def email_notification(
    request_data: EmailNotificationRequest,
    request: Request,
    correlation_id: str = Depends(get_correlation_id)
):
    """
    邮件通知接口：
    1. 接收邮件通知请求数据（包括收件人地址、主题、内容等）。
    2. 调用 Celery 任务发送邮件通知（使用 .delay() 异步调度）。
    3. 返回操作状态，成功时返回成功提示，失败时返回详细错误信息。
    """
    try:
        logger.info(
            "Received email notification request",
            extra={"to": request_data.email, "subject": request_data.subject, "correlation_id": correlation_id}
        )
        # 使用 Celery 的 .delay() 方法调度任务，传入字典数据（by_alias=True 保证使用别名 "to"）
        send_email_notification.delay(request_data.dict(by_alias=True))
        logger.info("Email notification task scheduled successfully", extra={"to": request_data.email, "correlation_id": correlation_id})
        return NotificationResponse(message="Email notification sent successfully", status="success")
    except Exception as e:
        logger.error("Failed to send email notification", extra={"error": str(e), "correlation_id": correlation_id}, exc_info=True)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to send email notification")