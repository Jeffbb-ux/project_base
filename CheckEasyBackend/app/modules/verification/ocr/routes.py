# 代码路径: app/modules/verification/ocr/routes.py

import io
import logging
from typing import Optional
from fastapi import APIRouter, HTTPException, UploadFile, File, Form, Depends, status, Request
from fastapi.responses import JSONResponse
from datetime import date, datetime

from app.modules.verification.ocr.schemas import OCRResponse
from app.modules.verification.ocr.utils import process_document
from app.core.dependencies import get_correlation_id, get_current_user
from app.modules.verification.ocr.models import OCRResult, OCRStatus
from app.core.db import get_async_db
from sqlalchemy.ext.asyncio import AsyncSession

router = APIRouter()
logger = logging.getLogger("CheckEasyBackend.verification.ocr.routes")

MAX_FILE_SIZE = 5 * 1024 * 1024  # 5MB
ALLOWED_CONTENT_TYPES = ["image/jpeg", "image/png", "image/jpg"]

def serialize_dates(data: dict) -> dict:
    """将data中的所有date类型转换为ISO格式的字符串"""
    for key, value in data.items():
        if isinstance(value, (date, datetime)):
            data[key] = value.isoformat()
    return data

@router.post(
    "/upload",
    summary="上传护照图片",
    description=(
        "接收用户上传的护照图片及相关信息，调用 OCR 工具识别护照内容，"
        "使用 PassportEye 提取 MRZ 信息。"
    )
)
async def upload_document(
    request: Request,  # 无默认值，必须放在最前面
    file: UploadFile = File(..., description="用户上传的护照图片文件"),
    doc_type: str = Form(..., description="证件类型，目前仅支持 'passport'"),
    country: str = Form(..., description="证件所属国家"),
    side: Optional[str] = Form(None, description="证件面向，目前仅支持 'front'"),
    correlation_id: str = Depends(get_correlation_id),
    current_user=Depends(get_current_user),  # ✅ 获取当前用户信息
    db: AsyncSession = Depends(get_async_db),  # ✅ 获取数据库连接
):
    logger.info(
        "Received document upload request",
        extra={"doc_type": doc_type, "country": country, "side": side, "correlation_id": correlation_id}
    )

    if file.content_type not in ALLOWED_CONTENT_TYPES:
        logger.warning("Invalid file type", extra={"file_content_type": file.content_type, "correlation_id": correlation_id})
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid file type: {file.content_type}. Allowed types: {', '.join(ALLOWED_CONTENT_TYPES)}."
        )

    file_contents = await file.read()
    file_size = len(file_contents)
    if file_size > MAX_FILE_SIZE:
        logger.warning("File too large", extra={"file_size": file_size, "max_allowed": MAX_FILE_SIZE, "correlation_id": correlation_id})
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"File size exceeds the maximum allowed limit of {MAX_FILE_SIZE} bytes."
        )

    logger.info(
        "File validated",
        extra={"file_name": file.filename, "content_type": file.content_type, "size": file_size, "correlation_id": correlation_id}
    )
    file.file.seek(0)

    try:
        ocr_result = await process_document(file=file, doc_type=doc_type, country=country, side=side)
        if not ocr_result.get("success", False):
            logger.warning("OCR processing failed", extra={"correlation_id": correlation_id, "detail": ocr_result.get("message")})
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=ocr_result.get("message", "OCR processing failed")
            )

        logger.info("OCR processing succeeded", extra={"correlation_id": correlation_id, "data": ocr_result.get("data")})

        serialized_data = serialize_dates(ocr_result.get("data", {}))

        response_payload = OCRResponse(
            message=ocr_result.get("message", "OCR processing succeeded"),
            status="success",
            data=serialized_data,
            next_action=ocr_result.get("next_action")
        )

        # ✅ 将OCR结果异步保存到数据库
        try:
            new_ocr_result = OCRResult(
                user_id=current_user.id,
                doc_type=doc_type,
                country=country,
                side=side,
                document_number=serialized_data.get("document_number"),
                name=serialized_data.get("name"),
                birth_date=datetime.strptime(serialized_data.get("birth_date"), '%Y-%m-%d').date() if serialized_data.get("birth_date") else None,
                expiry_date=datetime.strptime(serialized_data.get("expiry_date"), '%Y-%m-%d').date() if serialized_data.get("expiry_date") else None,
                sex=serialized_data.get("additional_info", {}).get("sex"),  # 直接提取sex
                status=OCRStatus.success,
                confidence_score=serialized_data.get("confidence_score"),
                recognized_text=serialized_data.get("recognized_text"),
                extracted_data=serialized_data.get("extracted_data"),
                upload_time=datetime.utcnow(),
                process_time=datetime.utcnow(),
                review_required=False,
                passport_image_path=str(saved_filepath),
                uploader_ip=request.client.host
            )
            
            
            db.add(new_ocr_result)
            await db.commit()
            await db.refresh(new_ocr_result)

            logger.info("OCR data successfully saved to database.", extra={"record_id": new_ocr_result.id})
        except Exception as e:
            logger.error("Failed to save OCR data: %s", str(e), exc_info=True)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to save OCR result to database"
            )

        return JSONResponse(content=response_payload.dict())

    except HTTPException:
        raise
    except Exception as e:
        logger.error("Error during OCR processing", extra={"correlation_id": correlation_id, "error": str(e)}, exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error during OCR processing"
        )