# 文件路径: CheckEasyBackend/app/modules/verification/manual/utils.py

import logging
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from datetime import datetime, timezone

from app.modules.verification.manual.models import ManualReview, ReviewStatusEnum

logger = logging.getLogger("CheckEasyBackend.verification.manual")

async def review_record(
    db: AsyncSession,
    review_id: int,
    reviewer_id: int,
    approve: bool,
    remarks: str = None
) -> bool:
    """
    更新人工审核记录的状态和相关信息

    Args:
        review_record_id (int): 人工审核记录的ID
        approve (bool): 审核结果（True 为批准，False 为拒绝）
        reviewer_id (int): 审核员的用户ID
        remarks (Optional[str]): 审核备注信息

    Returns:
        bool: 更新成功返回True，否则返回False
    """

    try:
        # 查询审核记录
        result = await db.execute(
            select(ManualReview).where(ManualReview.id == review_record_id)
        )
        review = result.scalar_one_or_none()

        if not review_record:
            logger.warning(f"Manual review record not found: id={review_record_id}")
            return False

        # 设置审核状态
        review.status = ReviewStatusEnum.approved if approve else ReviewStatusEnum.rejected
        review.reviewer_id = reviewer_id
        review.reviewed_at = datetime.now(timezone.utc)

        await db.commit()
        await db.refresh(review)

        logger.info(
            "Manual review updated successfully",
            extra={
                "review_id": review.id,
                "previous_status": review.status,
                "new_status": review.status,
                "reviewer_id": reviewer_id,
                "reviewed_at": review.reviewed_at.isoformat(),
            }
        )
        return True

    except Exception as e:
        await db.rollback()
        logger.error(f"Error during manual review process: {str(e)}", exc_info=True)
        return False