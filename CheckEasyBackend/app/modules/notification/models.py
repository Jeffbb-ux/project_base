# File: CheckEasyBackend/app/modules/notification/models.py

from sqlalchemy import (
    Column, Integer, String, DateTime, Text, Enum, ForeignKey, Index, func
)
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime
import enum

# 全局 Base（若项目已有全局 Base，可直接导入使用）
Base = declarative_base()

class NotificationStatus(enum.Enum):
    pending = "pending"   # 待处理
    success = "success"   # 发送成功
    failed = "failed"     # 发送失败

class NotificationChannel(enum.Enum):
    email = "email"       # 邮件通知
    # 可扩展其他渠道，如 push、wechat 等

class Notification(Base):
    """
    通知记录模型：
    记录每一次通知请求的信息，包括通知标题、内容、发送状态、接收者信息、发送时间、
    失败原因、错误代码、重试次数、任务标识、操作人信息以及记录创建和更新时间。
    """
    __tablename__ = "notifications"

    id = Column(Integer, primary_key=True, index=True, comment="通知记录主键")
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True, comment="关联用户ID，可为空")
    title = Column(String(150), nullable=False, comment="通知标题")
    message = Column(Text, nullable=False, comment="通知内容")
    channel = Column(Enum(NotificationChannel), nullable=False, comment="通知发送渠道")
    recipient = Column(String(255), nullable=False, comment="接收者信息，如邮箱地址或手机号")
    status = Column(Enum(NotificationStatus), nullable=False, default=NotificationStatus.pending, comment="通知发送状态")
    sent_at = Column(DateTime, nullable=True, comment="通知发送成功的时间")
    error_reason = Column(Text, nullable=True, comment="通知发送失败时的错误原因")
    error_code = Column(String(50), nullable=True, comment="错误代码，用于标识失败原因")
    retry_count = Column(Integer, nullable=False, default=0, comment="通知发送的重试次数")
    task_id = Column(String(100), nullable=True, comment="异步任务标识，用于追踪通知发送任务")
    created_by = Column(String(100), nullable=True, comment="记录创建者（操作人或系统）")
    updated_by = Column(String(100), nullable=True, comment="记录最后更新者")
    created_at = Column(DateTime, nullable=False, server_default=func.now(), comment="记录创建时间")
    updated_at = Column(DateTime, nullable=False, server_default=func.now(), onupdate=func.now(), comment="记录更新时间")

    def __repr__(self):
        return (
            f"<Notification(id={self.id}, title={self.title}, recipient={self.recipient}, "
            f"status={self.status.value}, sent_at={self.sent_at}, retry_count={self.retry_count})>"
        )

# 添加索引，提升常用查询性能（例如按接收者和状态查询）
Index("idx_notifications_recipient", Notification.recipient)
Index("idx_notifications_status", Notification.status)