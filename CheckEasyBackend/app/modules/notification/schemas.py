from pydantic import BaseModel, Field, EmailStr, constr, field_validator
from typing import Optional, List
from datetime import datetime
from enum import Enum

class NotificationPriority(str, Enum):
    low = "low"
    medium = "medium"
    high = "high"

class NotificationChannel(str, Enum):
    email = "email"
    # 其他渠道...

class NotificationRequest(BaseModel):
    title: constr(strip_whitespace=True, min_length=1, max_length=150) = Field(
        ...,
        description="通知标题",
        example="系统维护通知"
    )
    subject: constr(strip_whitespace=True, min_length=1, max_length=150) = Field(
        ...,
        description="通知主题",
        example="Test Notification Subject"
    )
    message: constr(strip_whitespace=True, min_length=1, max_length=2000) = Field(
        ...,
        description="通知消息内容",
        example="系统将在今晚12点进行维护..."
    )
    email: Optional[EmailStr] = Field(
        None,
        description="接收通知的邮箱地址",
        example="user@example.com",
        alias="to"
    )
    phone: Optional[constr(strip_whitespace=True, pattern=r'^\+?\d{10,15}$')] = Field(
        None,
        description="接收通知的手机号",
        example="+8613712345678"
    )
    
    @field_validator("email", mode='after')
    def validate_contact(cls, v, values):
        if not v and not values.get("phone"):
            raise ValueError("必须提供邮箱或手机号中的至少一项")
        return v

    channel: Optional[str] = Field(
        "email",
        description="通知发送渠道，默认为 email",
        example="email"
    )
    priority: Optional[NotificationPriority] = Field(
        NotificationPriority.medium,
        description="通知优先级",
        example="medium"
    )
    scheduled_time: Optional[datetime] = Field(
        None,
        description="通知计划发送时间",
        example="2025-03-06T12:00:00Z"
    )
    cc: Optional[List[EmailStr]] = Field(
        None,
        description="抄送邮箱列表",
        example=["manager@example.com"]
    )

class NotificationResponse(BaseModel):
    message: str = Field(
        ...,
        description="操作结果提示信息",
        example="Notification sent successfully"
    )
    status: str = Field(
        ...,
        description="发送状态",
        example="success"
    )
    task_id: Optional[str] = Field(
        None,
        description="通知发送任务标识",
        example="task-1234567890"
    )
    error_code: Optional[str] = Field(
        None,
        description="错误代码",
        example="ERR_INVALID_EMAIL"
    )
    timestamp: datetime = Field(
        default_factory=datetime.utcnow,
        description="响应生成时间"
    )

EmailNotificationRequest = NotificationRequest