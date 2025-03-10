# File: test_email.py

import asyncio
from fastapi.concurrency import run_in_threadpool
from app.core.email import send_email
from app.core.config import settings

async def test_send():
    try:
        await run_in_threadpool(
            send_email,
            to="your_test_email@example.com",  # 请替换成你希望测试的目标邮箱
            subject="Test Email",
            body="<p>This is a test email.</p>",
            from_email=settings.SMTP_USER,
            is_html=True
        )
        print("Email sent successfully")
    except Exception as e:
        print("Failed to send email:", e)

if __name__ == "__main__":
    asyncio.run(test_send())