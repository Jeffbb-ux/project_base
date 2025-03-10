import os
import shutil
import logging
from sqlalchemy import update
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.email import send_email

logger = logging.getLogger("CheckEasyBackend.verification.upload.utils")

async def process_passport_upload(user_id: int, file, upload_dir: str) -> str:
    """
    保存上传的护照文件到指定目录，并返回保存路径。
    """
    if not os.path.exists(upload_dir):
        os.makedirs(upload_dir, exist_ok=True)
    
    # 构造文件名：例如 "uploaded_passport_userid_{user_id}_{original_filename}"
    filename = f"uploaded_passport_userid_{user_id}_{file.filename}"
    save_path = os.path.join(upload_dir, filename)
    
    try:
        # 使用 shutil.copyfileobj 保存文件
        with open(save_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        logger.info(f"File saved to {save_path} for user_id {user_id}")
    except Exception as e:
        logger.error(f"Error saving file for user_id {user_id}: {e}", exc_info=True)
        raise e
    
    return save_path

async def update_verification_status_and_notify(db: AsyncSession, user, new_status: str = "pending"):
    """
    更新用户 verification_status 并发送通知邮件。
    """
    try:
        # 更新数据库中用户的审核状态为 new_status
        await db.execute(
            update(user.__class__)
            .where(user.__class__.id == user.id)
            .values(verification_status=new_status)
        )
        await db.commit()
        logger.info(f"Updated verification_status to {new_status} for user {user.email}")
    except Exception as e:
        logger.error(f"Error updating verification_status for user {user.email}: {e}", exc_info=True)
        raise e
    
    # 发送通知邮件
    try:
        subject = "证件上传成功"
        body = "您的证件已成功上传，请等待5-10分钟进行人工审核。"
        send_email(to=user.email, subject=subject, body=body, is_html=False)
        logger.info(f"Notification email sent to {user.email}")
    except Exception as e:
        logger.error(f"Failed to send notification email to {user.email}: {e}", exc_info=True)
        # 邮件发送失败不一定阻止流程，可视情况决定是否抛异常