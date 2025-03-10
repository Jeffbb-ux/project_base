# File: CheckEasyBackend/app/modules/auth/register/models.py

from sqlalchemy import Column, Integer, String, DateTime, Boolean
from datetime import datetime
from app.models.base import Base  # 请确保这个导入指向正确的数据库基类
from sqlalchemy.orm import relationship  # 新增导入
from app.modules.verification.upload.uploads.models import UploadedPassport


class User(Base):
    """
    用户数据模型：
    - username: 系统根据上传的证件信息自动生成的用户名，初始注册时为空，后续更新后用于登录等业务。
    - email: 用户邮箱，唯一且必须合法，用于登录和激活验证。
    - hashed_password: 加密存储的密码，确保安全性。
    - registered_at: 用户注册时间，默认使用 UTC 时间。
    - is_active: 用户激活状态，默认为 False，注册后需通过邮箱验证激活。
    - activation_token: 用于存储邮箱激活的 token，用户点击邮件中的链接时使用。
    - token_expires: 记录 token 何时过期，避免旧 token 被滥用。
    - verification_status: 用户证件审核状态，none: 未上传证件, pending: 待人工审核, approved: 审核通过, rejected: 审核拒绝。
    """
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), nullable=True, comment="系统根据证件信息生成的用户名，初始为空")
    email = Column(String(255), unique=True, index=True, nullable=False, comment="用户邮箱")
    hashed_password = Column(String(255), nullable=False, comment="加密后的密码")
    registered_at = Column(DateTime, default=datetime.utcnow, comment="注册时间")
    is_active = Column(Boolean, default=False, comment="激活状态，注册后需通过邮箱验证激活")

    activation_token = Column(String(64), nullable=True, index=True, comment="邮箱激活 token")
    token_expires = Column(DateTime, nullable=True, comment="激活 token 过期时间")

    # ✅ 新增字段: 证件审核状态
    verification_status = Column(String(20), default="none", nullable=False,
                                 comment="用户审核状态：none, pending, approved, rejected")

    def __repr__(self):
        return f"<User(username='{self.username}', email='{self.email}', active={self.is_active})>"
    
    #新增：与 ManualReview 模型的双向关系
    #manual_reviews = relationship(
    #    "ManualReview",
    #    back_populates="reviewer",
    #    cascade="all, delete-orphan"
    #)

    def __repr__(self):
        return f"<User(username='{self.username}', email='{self.email}', active={self.is_active})>"
    
    # 使用全限定名称定义上传护照的关系
    uploaded_passports = relationship(
        "app.modules.verification.upload.uploads.models.UploadedPassport",
        back_populates="user"
    )

    def __repr__(self):
        return f"<User(username='{self.username}', email='{self.email}', active={self.is_active})>"