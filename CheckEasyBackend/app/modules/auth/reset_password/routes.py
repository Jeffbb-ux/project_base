# 路径: app/modules/auth/reset_password/routes.py

from fastapi import APIRouter, Request, Form, Depends, HTTPException, status
from fastapi.responses import HTMLResponse
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.db import get_async_db
from app.modules.auth.reset_password.utils import verify_password_reset_token, update_user_password

router = APIRouter()

@router.get("/reset-password", response_class=HTMLResponse)
async def reset_password_form(token: str):
    html_content = f"""
    <html>
        <body>
            <form action="/api/v1/auth/reset-password?token={token}" method="post">
                <label>新密码：</label><input type="password" name="new_password">
                <button type="submit">重置密码</button>
            </form>
        </body>
    </html>
    """
    return HTMLResponse(content=html_content, status_code=200)

@router.post("/reset-password")
async def reset_password_submit(
    token: str,
    new_password: str = Form(...),
    db: AsyncSession = Depends(get_async_db)
):
    email = verify_password_reset_token(token)
    if not email:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Token无效或过期")
    
    success = await update_user_password(email, new_password, db)
    if not success:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="密码重置失败")

    return {"message": "密码已成功重置"}