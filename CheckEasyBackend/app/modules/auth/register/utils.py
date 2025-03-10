# File: CheckEasyBackend/app/modules/auth/register/utils.py

import random
import string
import logging
from datetime import datetime, timedelta
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update

from app.modules.auth.register.models import User
from app.core.config import settings
from app.core.email import send_email  # 引入真实邮件发送功能
from app.core.security import hash_password  # 使用安全的密码哈希函数

logger = logging.getLogger("CheckEasyBackend.auth.register")

async def store_token_in_db(db: AsyncSession, user_id: int, token: str):
    """
    存储用户激活 Token 到数据库，避免 FastAPI 重启后丢失。
    """
    try:
        await db.execute(
            update(User).where(User.id == user_id).values(
                activation_token=token,
                token_expires=datetime.utcnow() + timedelta(hours=24)
            )
        )
        await db.commit()
        logger.info(f"🔒 Token stored for user_id={user_id}, expires in 24h")
    except Exception as e:
        logger.error(f"❌ Failed to store token for user_id={user_id}: {e}", exc_info=True)

async def get_token_from_db(db: AsyncSession, token: str) -> User | None:
    """
    从数据库获取 Token 绑定的用户。
    """
    result = await db.execute(select(User).where(User.activation_token == token))
    user = result.scalar()
    if user:
        return user
    logger.warning(f"⚠️ No user found for token: {token}")
    return None

async def get_user_by_email(db: AsyncSession, email: str) -> User | None:
    """
    根据 email 查询用户，返回 User 对象或 None
    """
    result = await db.execute(select(User).where(User.email == email))
    user = result.scalar()
    return user

async def create_user(db: AsyncSession, username: str, password: str, email: str) -> User:
    """
    在数据库中创建用户，并返回 User 对象（异步）。
    is_active 默认为 False，需要后续验证激活。
    """
    # 使用安全的 bcrypt 算法生成密码哈希
    hashed_pw = hash_password(password)
    #--------  请在这里添加调试日志  --------
    #logger.debug("Generated hashed password: %s", hashed_pw)  # 在这里添加调试日志
    #---------------------------------------    
    new_user = User(
        username=username,
        hashed_password=hashed_pw,
        email=email,
        is_active=False,  # 默认未激活
        activation_token=None,
        token_expires=None
    )
    db.add(new_user)
    await db.commit()
    await db.refresh(new_user)
    logger.info(f"🆕 New user created: {email} (ID: {new_user.id})")
    return new_user

def generate_verify_token() -> str:
    """
    生成一个随机 token，避免存完整 URL。
    """
    return ''.join(random.choices(string.ascii_letters + string.digits, k=32))

async def verify_token_and_activate_user(db: AsyncSession, token: str) -> bool:
    """
    修复：
    - 先检查 Token 是否过期，过期就清除 Token 并返回失败
    - Token 验证成功后，激活用户并清除 Token
    """
    user = await get_token_from_db(db, token)
    if not user:
        logger.warning(f"❌ Invalid token: {token}")
        return False

    if user.token_expires and datetime.utcnow() > user.token_expires:
        logger.warning(f"❌ Expired token for user {user.email}, clearing token...")
        try:
            await db.execute(
                update(User).where(User.id == user.id).values(
                    activation_token=None,
                    token_expires=None
                )
            )
            await db.commit()
        except Exception as e:
            logger.error(f"⚠️ Failed to clear expired token for {user.email}: {e}", exc_info=True)
        return False
    
    # 激活用户并清除 Token
    try:
        await db.execute(
            update(User).where(User.id == user.id).values(
                is_active=True,
                activation_token=None,
                token_expires=None
            )
        )
        await db.commit()
        logger.info(f"✅ User {user.email} activated successfully")
        return True
    except Exception as e:
        logger.error(f"❌ Failed to activate user {user.email}: {e}", exc_info=True)
        return False

async def send_activation_email(db: AsyncSession, to_email: str, user_id: int):
    """
    发送真实的激活邮件，并存储 Token 到数据库
    """
    token = generate_verify_token()
    await store_token_in_db(db, user_id, token)  # 改用数据库存 Token

    base_url = f"{settings.APP_BASE_URL}/api/v1"
    verify_link = f"{base_url}/auth/register/confirm?token={token}"
    
    # 邮件内容
    subject = "CheckEasy - 账户激活"
    body = f"""
    <html>
        <body>
            <p>您好，</p>
            <p>感谢您注册 CheckEasy！请点击以下链接激活您的账户：</p>
            <p><a href="{verify_link}">{verify_link}</a></p>
            <p>如果您没有注册此账户，请忽略此邮件。</p>
            <br>
            <p>CheckEasy 团队</p>
        </body>
    </html>
    """

    try:
        logger.info(f"📩 Sending activation email to {to_email} with link: {verify_link}")
        send_email(to=to_email, subject=subject, body=body, is_html=True)  # 发送 HTML 邮件
        logger.info(f"✅ Activation email sent to {to_email}")
    except Exception as e:
        logger.error(f"❌ Failed to send activation email to {to_email}: {e}", exc_info=True)