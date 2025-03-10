# 文件路径: CheckEasyBackend/app/modules/verification/manual/schemas.py

from pydantic import BaseModel, Field
from enum import Enum
from datetime import datetime
from typing import List, Optional


class ReviewStatusEnum(str, Enum):
    pending = "pending"
    approved = "approved"
    rejected = "rejected"


class ManualReviewBase(BaseModel):
    status: ReviewStatusEnum = Field(
        default=ReviewStatusEnum.pending,
        description="审核状态"
    )
    remarks: Optional[str] = Field(None, description="审核备注信息")


class ManualReviewCreate(ManualReviewBase):
    ocr_result_id: int = Field(..., description="关联的OCR结果ID")


class ManualReviewResponse(BaseModel):
    id: int
    ocr_result_id: int
    status: ReviewStatusEnum
    reviewer_id: Optional[int]
    reviewer_email: Optional[str] = None
    created_at: datetime
    reviewed_at: Optional[datetime] = None
    remarks: Optional[str] = None

    class Config:
        from_attributes = True


class ManualReviewListResponse(BaseModel):
    reviews: List[ManualReviewResponse]
    total: int

    class Config:
        from_attributes = True