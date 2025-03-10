# File: CheckEasyBackend/app/modules/auth/register/schemas.py

from pydantic import BaseModel, Field, EmailStr, constr

class RegisterRequest(BaseModel):
    """
    注册请求的数据结构:
    - email: 用户邮箱
    - password: 明文密码（8-128 个字符）
    """
    email: EmailStr = Field(
        ...,
        description="合法的邮箱地址",
        example="john@example.com"
    )
    password: constr(min_length=8, max_length=128) = Field(
        ...,
        description="密码，8-128 个字符，建议包含字母和数字",
        example="Passw0rd!"
    )

class RegisterResponse(BaseModel):
    """
    注册成功后的响应结构:
    - message: 提示注册结果信息
    - user_id: 刚创建的用户 ID
    """
    message: str = Field(
        ...,
        description="提示注册结果信息",
        example="Registration successful, please check your email to activate your account"
    )
    user_id: int = Field(
        ...,
        description="新创建的用户ID",
        example=1001
    )