# 文件路径: app/modules/verification/ocr/save_ocr_result.py

from datetime import datetime
from app.core.db import AsyncSessionLocal
from app.modules.verification.ocr.models import OCRResult, OCRStatus
from typing import Dict, Any, Optional

def save_passport_ocr_result(
    extracted_data: Dict[str, Any],
    doc_type: str,
    country: str,
    side: Optional[str],
    user_id: Optional[int] = None,
    uploader_ip: Optional[str] = None,
    confidence_score: Optional[float] = None,
    status: OCRStatus = OCRStatus.success,
    error_message: Optional[str] = None,
):
    """
    保存护照OCR识别后的结果到数据库。

    :param extracted_data: OCR提取的数据信息（包括document_number、name等）
    :param doc_type: 证件类型（此处为passport）
    :param country: 证件国家
    :param side: 证件面向
    :param user_id: 上传的用户ID
    :param uploader_ip: 上传者IP
    :param confidence_score: OCR置信度评分
    :param status: OCR处理状态（success/failure）
    :param error_message: 错误信息（如果有）
    """
    db = SessionLocal()

    try:
        ocr_record = OCRResult(
            user_id=user_id,
            doc_type=doc_type,
            country=country,
            side=side,
            recognized_text=extracted_data.get('extracted_text'),
            extracted_data=extracted_data,
            confidence_score=confidence_score,
            status=status,
            error_message=error_message,
            upload_time=datetime.utcnow(),
            process_time=datetime.utcnow(),
            uploader_ip=uploader_ip,
        )

        db.add(ocr_record)
        db.commit()
        db.refresh(ocr_record)

        return ocr_record

    except Exception as e:
        db.rollback()
        raise e

    finally:
        db.close()