# File: CheckEasyBackend/app/core/email.py

import smtplib
import ssl
import logging
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.application import MIMEApplication
from typing import List, Optional, Dict, Any

from app.core.config import settings

logger = logging.getLogger("CheckEasyBackend.core.email")


def send_email(
    to: str,
    subject: str,
    body: str,
    from_email: Optional[str] = None,
    attachments: Optional[List[Dict[str, Any]]] = None,
    is_html: bool = False
) -> None:
    """
    发送邮件服务函数，用于统一处理邮件发送需求。

    参数:
        to (str): 收件人邮箱地址。
        subject (str): 邮件主题。
        body (str): 邮件正文内容，可以为纯文本或 HTML 格式。
        from_email (Optional[str]): 发件人邮箱地址。默认为 settings.SMTP_USER。
        attachments (Optional[List[Dict[str, Any]]]): 附件列表，每个附件为字典格式，
            格式示例:
                {
                    "filename": "example.pdf",
                    "content": b"<binary data>",
                    "mime_type": "application/pdf"
                }
        is_html (bool): 如果为 True，则邮件正文作为 HTML 格式发送；否则发送纯文本。

    使用:
        此函数使用 Python 内置的 smtplib 和 email 库来构建和发送邮件，
        支持 MIME 格式以及多媒体附件。配置参数从 app/core/config.py 中读取，
        可根据不同环境配置不同的 SMTP 服务。

    异常:
        如果邮件发送失败，将记录错误日志并抛出异常供调用方捕获处理。
    """
    # 使用默认发件人邮箱
    if not from_email:
        from_email = settings.SMTP_USER

    # 构建多部分邮件对象
    message = MIMEMultipart()
    message["From"] = from_email
    message["To"] = to
    message["Subject"] = subject

    # 添加邮件正文，支持纯文本或 HTML 格式
    mime_subtype = "html" if is_html else "plain"
    message.attach(MIMEText(body, mime_subtype, "utf-8"))

    # 添加附件（如果有）
    if attachments:
        for attachment in attachments:
            # attachment 应包含 filename, content 和 mime_type 字段
            try:
                mime_main, mime_sub = attachment.get("mime_type", "application/octet-stream").split("/")
            except Exception:
                mime_main, mime_sub = "application", "octet-stream"
            part = MIMEApplication(attachment.get("content"), _subtype=mime_sub)
            part.add_header(
                "Content-Disposition",
                "attachment",
                filename=attachment.get("filename")
            )
            message.attach(part)

    try:
        # 建立安全连接并登录 SMTP 服务器
        context = ssl.create_default_context()
        with smtplib.SMTP(settings.SMTP_SERVER, settings.SMTP_PORT) as server:
            server.starttls(context=context)
            server.login(settings.SMTP_USER, settings.SMTP_PASSWORD)
            server.sendmail(from_email, to, message.as_string())
        logger.info("Email sent successfully to %s", to)
    except Exception as e:
        logger.error("Failed to send email to %s: %s", to, str(e), exc_info=True)
        raise