# File: CheckEasyBackend/app/modules/auth/forgot_password/schemas.py

from pydantic import BaseModel, Field, EmailStr, constr
from typing import Optional

class ForgotPasswordRequest(BaseModel):
    """
    忘记密码请求模型：
    用户提交邮箱请求重置密码，验证码为可选字段（例如用于防止暴力请求）。
    """
    email: EmailStr = Field(
        ..., 
        description="用户注册时使用的邮箱地址", 
        example="john@example.com"
    )
    captcha: Optional[constr(strip_whitespace=True, min_length=4, max_length=10)] = Field(
        None, 
        description="验证码（如果启用验证码防护时必填）", 
        example="1234"
    )

class ForgotPasswordResponse(BaseModel):
    """
    忘记密码响应模型：
    返回处理结果的提示信息，通常表示重置密码邮件已发送。
    """
    message: str = Field(
        ..., 
        description="操作结果提示信息", 
        example="Reset password email sent"
    )

class ResetPasswordRequest(BaseModel):
    """
    重置密码请求模型：
    用户通过重置密码链接或验证码提交新密码。包含邮箱、重置 Token 和新密码字段。
    """
    email: EmailStr = Field(
        ..., 
        description="用户注册时使用的邮箱地址", 
        example="john@example.com"
    )
    token: constr(strip_whitespace=True, min_length=10, max_length=256) = Field(
        ..., 
        description="用于验证重置密码请求的 Token", 
        example="abc123resetToken"
    )
    new_password: constr(min_length=8, max_length=128) = Field(
        ..., 
        description="新密码，建议包含大小写字母、数字和特殊字符", 
        example="NewPassw0rd!"
    )

class ResetPasswordResponse(BaseModel):
    """
    重置密码响应模型：
    返回重置密码的处理结果提示信息。
    """
    message: str = Field(
        ..., 
        description="操作结果提示信息", 
        example="Password reset successful"
    )