# 文件路径: CheckEasyBackend/app/modules/verification/manual/routes.py

import logging
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from app.core.db import get_async_db
from app.core.dependencies import get_current_user
from app.core.email import send_email  # <-- 引入send_email
from app.modules.auth.register.models import User
from app.modules.verification.manual.models import ManualReview, ReviewStatus
from app.modules.verification.manual.schemas import (
    ManualReviewCreate,
    ManualReviewResponse,
    ManualReviewListResponse
)
from app.modules.verification.ocr.models import OCRResult

router = APIRouter()
logger = logging.getLogger("CheckEasyBackend.verification.manual")


@router.post(
    "/review",
    response_model=ManualReviewResponse,
    summary="提交人工审核结果",
    description="管理员提交人工审核结果，更新OCR记录审核状态，并记录日志。"
)
async def submit_manual_review(
    review_request: ManualReviewCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_db)
):
    logger.info(
        f"Manual review requested: user_id={current_user.id}, ocr_result_id={review_request.ocr_result_id}"
    )

    # 仅限管理员
    if not current_user.is_admin:
        logger.warning(
            f"Unauthorized manual review attempt by user_id={current_user.id}"
        )
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient permissions"
        )

    # 获取OCR记录
    ocr_result = await db.get(OCRResult, review_request.ocr_result_id)
    if not ocr_result:
        logger.error(
            f"OCR record not found: ocr_result_id={review_request.ocr_result_id}"
        )
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="OCR record not found"
        )

    # 查询是否已有审核记录
    existing_review = await db.execute(
        select(ManualReview).where(ManualReview.ocr_result_id == review_request.ocr_result_id)
    )
    manual_review = existing_review.scalar_one_or_none()

    current_time = datetime.now(timezone.utc)

    if manual_review:
        # 更新已有审核记录
        manual_review.status = review_request.status
        manual_review.remarks = review_request.remarks
        manual_review.reviewer_id = current_user.id
        manual_review.reviewed_at = current_time
        logger.info(
            "Manual review updated",
            extra={
                "review_id": manual_review.id,
                "user_id": current_user.id,
                "status": review_request.status
            }
        )
    else:
        # 创建新审核记录
        manual_review = ManualReview(
            ocr_result_id=review_request.ocr_result_id,
            status=review_request.status,
            reviewer_id=current_user.id,
            reviewed_at=current_time,
            remarks=review_request.remarks
        )
        db.add(manual_review)
        logger.info(
            "Manual review created",
            extra={
                "ocr_result_id": review_request.ocr_result_id,
                "user_id": current_user.id,
                "status": review_request.status
            }
        )

    # 同步更新 OCRResult 状态
    ocr_result.status = review_request.status

    # 获取关联用户
    user = await db.get(User, ocr_result.user_id)
    if not user:
        logger.error(
            "Associated user not found for OCR result",
            extra={"user_id": ocr_result.user_id}
        )
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Associated user not found"
        )

    # 根据审核结果更新用户审核状态并发送邮件
    if review_request.status == ReviewStatus.rejected:
        user.verification_status = "none"
        ocr_result.status = "rejected"
        logger.info(
            f"User {user.id} must re-upload after rejection.",
            extra={"user_id": user.id, "ocr_result_id": ocr_result.id}
        )
        # 发送「审核未通过」邮件
        send_email(
            to=user.email,
            subject="证件审核未通过",
            body="您的证件审核未通过，请重新上传。"
        )
    elif review_request.status == ReviewStatus.approved:
        user.verification_status = "approved"
        # 发送「审核通过」邮件
        send_email(
            to=user.email,
            subject="证件审核通过",
            body="您的证件已成功通过审核。"
        )
    else:
        # 如果有其它状态（如 ReviewStatus.pending 等），可自行处理
        user.verification_status = review_request.status.value

    await db.commit()
    await db.refresh(manual_review)

    logger.info(
        f"Manual review completed: review_id={manual_review.id}, user_id={user.id}, final_status={manual_review.status}"
    )

    response = ManualReviewResponse(
        id=manual_review.id,
        ocr_result_id=review_request.ocr_result_id,
        status=manual_review.status,
        reviewer_id=current_user.id,
        reviewer_email=current_user.email,
        created_at=manual_review.created_at,
        reviewed_at=manual_review.reviewed_at,
        remarks=manual_review.remarks
    )

    logger.info(
        "OCR result and user verification status synchronized",
        extra={
            "ocr_result_id": ocr_result.id,
            "user_id": user.id,
            "new_status": review_request.status
        }
    )

    return response


@router.get("/me/verification-status", summary="获取当前用户审核状态", response_model=dict)
async def get_verification_status(current_user: User = Depends(get_current_user)):
    """
    获取当前用户的 `verification_status` 状态。
    """
    return {
        "user_id": current_user.id,
        "verification_status": current_user.verification_status
    }


@router.get("/reviews", response_model=ManualReviewListResponse, summary="获取所有人工审核记录")
async def list_manual_reviews(
    db: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(get_current_user),
    page: int = Query(1, alias="page", ge=1, description="页码"),
    page_size: int = Query(10, alias="page_size", le=100, description="每页记录数")
):
    """
    允许管理员查询所有人工审核记录，带分页功能。
    """
    if not current_user.is_admin:
        raise HTTPException(status_code=403, detail="无权限")
    
    offset = (page - 1) * page_size
    query = select(ManualReview).offset(offset).limit(page_size)
    result = await db.execute(query)
    reviews = result.scalars().all()
    
    return ManualReviewListResponse(reviews=reviews, total=len(reviews))