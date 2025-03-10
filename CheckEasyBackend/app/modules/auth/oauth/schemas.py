# File: CheckEasyBackend/app/modules/auth/oauth/schemas.py

from pydantic import BaseModel, Field, EmailStr, HttpUrl, field_validator
from typing import Optional
from datetime import datetime

class OAuthUserInfo(BaseModel):
    """
    第三方 OAuth 返回的用户信息数据模型。
    包括用户在 OAuth 提供商处的唯一标识、邮箱、姓名、头像 URL、以及所属的 OAuth 提供商。
    """
    id: str = Field(..., description="第三方用户唯一标识", example="1234567890")
    provider: str = Field(..., description="OAuth 提供商名称", example="google")
    email: Optional[EmailStr] = Field(None, description="用户邮箱", example="user@example.com")
    name: Optional[str] = Field(None, description="用户姓名", example="John Doe")
    avatar: Optional[HttpUrl] = Field(None, description="用户头像 URL", example="https://example.com/avatar.jpg")
    # 可扩展：增加其他字段，如用户昵称、地区、语言等

class OAuthCallbackResponse(BaseModel):
    """
    OAuth 回调响应数据模型，用于返回 OAuth 登录或注册的结果。
    包含认证提示信息、JWT Token、刷新令牌、Token 到期时间以及用户基本信息。
    """
    message: str = Field(..., description="认证结果提示信息", example="OAuth login successful")
    token: str = Field(..., description="用于后续身份验证的 JWT Token", example="eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...")
    refresh_token: Optional[str] = Field(
        None, 
        description="刷新令牌，用于获取新的 JWT Token（如实现刷新机制）", 
        example="dGhpc0lzQVJlZnJlc2hUb2tlbg..."
    )
    token_expiration: Optional[datetime] = Field(
        None, 
        description="JWT Token 的过期时间，ISO 8601 格式", 
        example="2025-03-06T12:00:00Z"
    )
    user: OAuthUserInfo = Field(..., description="第三方认证返回的用户基本信息")
    
    @field_validator("token_expiration", mode='before')
    def parse_token_expiration(cls, v):
        """
        尝试将传入的 token_expiration 转换为 datetime 对象，如果已为 datetime 则直接返回，
        如果是字符串则按照 ISO 8601 格式转换，确保后续可以直接操作日期类型。
        """
        if not v:
            return v
        if isinstance(v, datetime):
            return v
        try:
            return datetime.fromisoformat(v.replace("Z", "+00:00"))
        except Exception as e:
            raise ValueError(f"token_expiration 格式错误：{v}") from e