from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, func
from sqlalchemy.orm import relationship
from app.models.base import Base

class UploadedPassport(Base):
    __tablename__ = "uploaded_passport"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, comment="上传该证件的用户ID")
    file_path = Column(String, nullable=False, comment="护照图片存储路径")
    uploaded_at = Column(DateTime, server_default=func.now(), comment="上传时间")
    
    # 建立与用户的反向关系（在 User 模型中对应配置）
    user = relationship("User", back_populates="uploaded_passports")