# File: app/modules/verification/ocr/models.py

# 路径: app/modules/verification/ocr/models.py
from sqlalchemy import Column, Integer, String, Date, DateTime, ForeignKey, Float, JSON, Boolean, Text, Enum as SQLEnum, func, Index
from app.models.base import Base
from datetime import datetime
from enum import Enum
from sqlalchemy.orm import relationship

# 定义 OCR 状态枚举
class OCRStatus(str, Enum):
    pending = "pending"
    success = "success"
    failed = "failed"

class OCRResult(Base):
    """
    OCR 识别结果记录模型：
    用于记录每一次 OCR 识别请求的详细信息及相关元数据，
    便于后续人工审核、日志追踪和数据统计。
    """
    __tablename__ = "ocr_results"
    __table_args__ = {'extend_existing': True}

    id = Column(Integer, primary_key=True, index=True, comment="OCR 记录主键")

    user_id = Column(Integer, ForeignKey("users.id"), nullable=True, comment="上传该证件的用户ID")

    doc_type = Column(String(50), nullable=False, comment="证件类型，例如 '身份证'、'驾照'、'护照'")
    country = Column(String(50), nullable=False, comment="证件所属国家")
    side = Column(String(10), nullable=True, comment="证件面向，例如 'front' 或 'back'")

    document_number = Column(String(100), nullable=True, comment="证件号码")
    name = Column(String(200), nullable=True, comment="证件上的姓名")
    birth_date = Column(Date, nullable=True, comment="出生日期")
    expiry_date = Column(Date, nullable=True, comment="证件有效期")
    sex = Column(String(10), nullable=True, comment="性别，例如 'M' 或 'F'")
    recognized_text = Column(Text, nullable=True, comment="OCR 识别出的完整文本")
    extracted_data = Column(JSON, nullable=True, comment="提取的关键信息，存储为 JSON 格式")

    confidence_score = Column(Float, nullable=True, comment="OCR 识别置信度评分（0~1之间）")
    status = Column(SQLEnum(OCRStatus), nullable=False, default=OCRStatus.pending, comment="OCR 处理状态")
    error_message = Column(Text, nullable=True, comment="OCR 识别失败时的错误描述")
    review_required = Column(Boolean, nullable=False, default=False, comment="是否需要人工审核")

    upload_time = Column(DateTime, nullable=False, default=datetime.utcnow, comment="证件上传时间")
    process_time = Column(DateTime, nullable=True, comment="OCR 处理完成时间")

    created_at = Column(DateTime, nullable=False, server_default=func.now(), comment="记录创建时间")
    updated_at = Column(DateTime, nullable=False, server_default=func.now(), onupdate=func.now(), comment="记录更新时间")

    uploader_ip = Column(String(45), nullable=True, comment="上传者IP地址")
    
    # ✅ 新增这一行来保存护照图片的路径
    passport_image_path = Column(String, nullable=True, comment="护照图片路径")
    
    def __repr__(self):
        return (
            f"<OCRResult(id={self.id}, doc_type='{self.doc_type}', country='{self.country}', "
            f"status='{self.status.value}', user_id={self.user_id}, upload_time='{self.upload_time}')>"
        )

    # 新增：与 ManualReview 模型的反向关系
    #manual_reviews = relationship(
    #    "ManualReview",
    #    back_populates="ocr_result",
    #    cascade="all, delete-orphan"
    #)

    def __repr__(self):
        return (
            f"<OCRResult(id={self.id}, doc_type='{self.doc_type}', country='{self.country}', "
            f"status='{self.status.value}', user_id={self.user_id}, upload_time='{self.upload_time}')>"
        )
    
# 添加索引以提升常用查询的性能
Index("idx_ocr_doc_type", OCRResult.doc_type)
Index("idx_ocr_country", OCRResult.country)
Index("idx_ocr_status", OCRResult.status)