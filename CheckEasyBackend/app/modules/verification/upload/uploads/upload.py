# 代码路径: CheckEasyBackend/app/modules/verification/upload/upload.py

from pathlib import Path
from datetime import datetime
import shutil

from fastapi import APIRouter, Depends, File, Form, HTTPException, Request, UploadFile, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.db import get_async_db
from app.core.dependencies import get_current_user
from app.modules.verification.ocr.routes import process_document, serialize_dates
from app.modules.verification.ocr.models import OCRResult, OCRStatus
from app.core.email import send_email  # 引入邮件发送功能
from app.modules.auth.register.models import User

router = APIRouter()

UPLOAD_DIR = Path("app/modules/verification/upload/uploaded_passport")
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

@router.post(
    "/upload_passport",
    summary="上传护照并储存图片与OCR结果"
)
async def upload_passport(
    request: Request,
    file: UploadFile = File(...),
    doc_type: str = Form(...),
    country: str = Form(...),
    side: str = Form("front"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_db),
):
    if file.content_type not in {"image/jpeg", "image/png"}:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid file type. Only JPEG and PNG are allowed."
        )

    # 保存上传的图片
    file_extension = Path(file.filename).suffix
    timestamp = datetime.utcnow().strftime("%Y%m%d%H%M%S%f")
    saved_filename = f"uploaded_passport_userid_{current_user.id}_{timestamp}{file_extension}"
    saved_filepath = UPLOAD_DIR / saved_filename

    with saved_filepath.open("wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    # 调用现有OCR逻辑
    file.file.seek(0)  # 重置文件指针以便OCR再次读取
    ocr_result = await process_document(file=file, doc_type=doc_type, country=country, side=side)

    if not ocr_result.get("success"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="OCR processing failed."
        )

    serialized_data = serialize_dates(ocr_result["data"])

    # 存入OCR结果及文件路径到数据库
    new_ocr_result = OCRResult(
        user_id=current_user.id,
        doc_type=doc_type,
        country=country,
        side=side,
        document_number=serialized_data.get("document_number"),
        name=serialized_data.get("name"),
        birth_date=datetime.strptime(serialized_data.get("birth_date"), '%Y-%m-%d').date(),
        expiry_date=datetime.strptime(serialized_data.get("expiry_date"), '%Y-%m-%d').date(),
        status=OCRStatus.success,
        confidence_score=serialized_data.get("confidence_score"),
        recognized_text=serialized_data.get("recognized_text"),
        extracted_data=serialized_data.get("extracted_data"),
        upload_time=datetime.utcnow(),
        process_time=datetime.utcnow(),
        review_required=False,
        uploader_ip=request.client.host,
        passport_image_path=str(saved_filepath)  # 保存文件路径
    )

    db.add(new_ocr_result)
    await db.commit()
    await db.refresh(new_ocr_result)

    # --- 更新用户的审核状态 ---
    try:
        current_user.verification_status = "pending"
        await db.commit()
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update user verification status."
        )

    # --- 发送邮件通知 ---
    try:
        subject = "护照上传成功"
        body = "您的护照已成功上传，请等待5-10分钟进行人工审核。"
        send_email(to=current_user.email, subject=subject, body=body, is_html=False)
    except Exception as e:
        # 记录错误，但不阻止上传成功
        print("Failed to send notification email:", e)

    return {
        "message": "Passport uploaded successfully. Please wait 5-10 minutes for manual verification.",
        "ocr_data": serialized_data,
        "image_saved_as": saved_filename,
        "verification_status": current_user.verification_status
    }