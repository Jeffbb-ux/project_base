# File: CheckEasyBackend/app/modules/notification/tasks.py

import os
import logging
from celery import Celery, Task
from celery.utils.log import get_task_logger
from app.core.email import send_email  # 企业级邮件发送函数

# 从环境变量或全局配置中加载 Celery 配置
CELERY_BROKER_URL = os.getenv("CELERY_BROKER_URL", "redis://localhost:6379/0")
CELERY_RESULT_BACKEND = os.getenv("CELERY_RESULT_BACKEND", "redis://localhost:6379/0")

# 初始化 Celery 应用
celery_app = Celery("notification_tasks", broker=CELERY_BROKER_URL, backend=CELERY_RESULT_BACKEND)
celery_app.conf.task_routes = {
    "app.modules.notification.tasks.send_email_notification": {"queue": "notification"}
}

# 使用 Celery 内置日志记录器
logger = get_task_logger(__name__)

class BaseTaskWithRetry(Task):
    """
    自定义 Task 基类，实现自动重试机制：
    - 自动捕获异常并重试，最大重试次数及间隔可通过 retry_kwargs 配置。
    - retry_backoff 与 retry_jitter 可使重试时间间隔呈指数增长并随机抖动，避免大量任务同时重试。
    """
    autoretry_for = (Exception,)
    retry_kwargs = {"max_retries": 5, "countdown": 60}  # 重试 5 次，每次等待 60 秒
    retry_backoff = True
    retry_jitter = True

@celery_app.task(bind=True, base=BaseTaskWithRetry, name="app.modules.notification.tasks.send_email_notification")
def send_email_notification(self, notification_data):
    """
    异步任务函数：发送邮件通知
    
    Args:
        notification_data: 包含邮件通知必要信息的数据，既可以是字典，也可以是 pydantic 模型（如 EmailNotificationRequest）。

    任务流程：
      1. 记录任务开始日志。
      2. 如果 notification_data 不是 dict，则调用 .dict() 转换为字典。
      3. 调用企业级邮件发送函数 send_email。
      4. 记录成功日志或在发生异常时记录错误，并自动触发重试机制。
    """
    try:
        # 如果传入的 notification_data 是 pydantic 模型，则转换为字典
        if not isinstance(notification_data, dict):
            notification_data = notification_data.dict()
        logger.info("Starting email notification task", extra={"notification_data": notification_data})
        send_email(
            to=notification_data.get("email"),  # 使用字段名称 email 而非别名 "to"
            subject=notification_data.get("subject"),
            body=notification_data.get("message"),
            from_email=notification_data.get("from_email")
        )
        logger.info("Email notification sent successfully", extra={"to": notification_data.get("email")})
    except Exception as exc:
        logger.error(
            "Error sending email notification",
            extra={"notification_data": notification_data, "error": str(exc)},
            exc_info=True
        )
        raise self.retry(exc=exc)