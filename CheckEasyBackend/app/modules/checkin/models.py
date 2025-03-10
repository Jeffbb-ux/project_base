# 代码路径: CheckEasyBackend/app/modules/checkin/models.py

from sqlalchemy import (
    Column, Integer, String, DateTime, Text, ForeignKey, Enum, JSON, func
)
from datetime import datetime
import enum
from app.models.base import Base  # Base 已在 core/db.py 中定义


class CheckinStatus(enum.Enum):
    checked_in = "checked_in"
    checked_out = "checked_out"
    cancelled = "cancelled"


class CheckinRecord(Base):
    __tablename__ = "checkin_records"

    id = Column(Integer, primary_key=True, index=True, comment="入住记录主键")
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, comment="用户ID，关联到用户表")
    certificate_id = Column(String(100), nullable=True, comment="证件记录ID")
    checkin_time = Column(DateTime, nullable=False, default=datetime.utcnow, comment="入住时间")
    status = Column(Enum(CheckinStatus), nullable=False, default=CheckinStatus.checked_in, comment="入住状态")
    room_number = Column(String(50), nullable=True, comment="房间号")
    remarks = Column(Text, nullable=True, comment="备注信息")
    additional_info = Column(JSON, nullable=True, comment="其他附加信息")
    created_at = Column(DateTime, nullable=False, server_default=func.now(), comment="记录创建时间")
    updated_at = Column(DateTime, nullable=False, server_default=func.now(), onupdate=func.now(), comment="记录最后更新时间")

    def __repr__(self):
        return (
            f"<CheckinRecord(id={self.id}, user_id={self.user_id}, checkin_time={self.checkin_time}, "
            f"status={self.status.value}, room_number={self.room_number})>"
        )