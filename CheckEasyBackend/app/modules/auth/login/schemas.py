# File: CheckEasyBackend/app/modules/auth/login/schemas.py

from pydantic import BaseModel, Field, constr, field_validator, EmailStr
from typing import Optional, List
from datetime import datetime

class UserInfo(BaseModel):
    user_id: int = Field(..., description="用户的唯一标识", example=1234)
    email: str = Field(..., description="用户的邮箱", example="john@example.com")
    roles: Optional[List[str]] = Field(None, description="用户角色列表", example=["user", "admin"])

class LoginRequest(BaseModel):
    email: EmailStr = Field(
        ..., description="用户登录邮箱", example="john_doe@example.com"
    )
    password: constr(min_length=8, max_length=128) = Field(
        ..., description="用户密码，8-128个字符，建议包含字母和数字", example="Passw0rd!"
    )
    # 可选字段：用于多因素认证（MFA），如短信或邮件验证码
    mfa_code: Optional[constr(strip_whitespace=True, min_length=4, max_length=10)] = Field(
        None, description="多因素认证验证码（如需要）", example="123456"
    )
    
    # 示例：可添加密码复杂度验证等自定义校验器
    @field_validator("password")
    def validate_password(cls, v):
        # 可在此处添加正则表达式等复杂度校验逻辑
        if not any(char.isdigit() for char in v):
            raise ValueError("密码必须包含至少一个数字")
        if not any(char.isalpha() for char in v):
            raise ValueError("密码必须包含至少一个字母")
        return v

class LoginResponse(BaseModel):
    message: str = Field(
        ..., description="登录结果提示信息", example="Login successful"
    )
    token: str = Field(
        ..., description="用于后续身份验证的 JWT Token", example="eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
    )
    refresh_token: Optional[str] = Field(
        None, description="刷新令牌，用于获取新的访问令牌（如实现刷新机制）", example="dGhpc0lzQVJlZnJlc2hUb2tlbg..."
    )
    token_expiration: Optional[datetime] = Field(
        None, description="JWT Token 的过期时间", example="2025-03-06T12:00:00Z"
    )
    mfa_required: Optional[bool] = Field(
        False, description="指示是否需要多因素认证", example=False
    )
    user: Optional[UserInfo] = Field(
        None, description="登录成功后返回的用户信息"
    )