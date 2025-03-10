# 文件路径: CheckEasyBackend/app/core/config.py

import os
from dotenv import load_dotenv

# 加载 .env 文件
load_dotenv()

class Settings:
    DATABASE_URL: str = os.getenv("DATABASE_URL", "sqlite:///./test.db")
    
    SECRET_KEY: str = os.getenv("SECRET_KEY", "change_me")
    ALGORITHM: str = os.getenv("ALGORITHM", "HS256")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", 30))
    
    SMTP_SERVER: str = os.getenv("SMTP_SERVER", "smtp.example.com")
    SMTP_PORT: int = int(os.getenv("SMTP_PORT", 587))
    SMTP_USER: str = os.getenv("SMTP_USER", "user@example.com")
    SMTP_PASSWORD: str = os.getenv("SMTP_PASSWORD", "password")
    
    ENV: str = os.getenv("ENV", "development")
    
    HOST: str = os.getenv("HOST", "0.0.0.0")
    PORT: int = int(os.getenv("PORT", 8000))
    PROJECT_NAME: str = os.getenv("PROJECT_NAME", "CheckEasyBackend")
    
    # Google OAuth 配置，优先使用 GOOGLE_* 变量，其次使用旧的 OAUTH_* 默认值
    OAUTH_CLIENT_ID: str = os.getenv("GOOGLE_CLIENT_ID", os.getenv("OAUTH_CLIENT_ID", "your-google-client-id"))
    OAUTH_CLIENT_SECRET: str = os.getenv("GOOGLE_CLIENT_SECRET", os.getenv("OAUTH_CLIENT_SECRET", "your-google-client-secret"))
    OAUTH_REDIRECT_URI: str = os.getenv("GOOGLE_REDIRECT_URI", os.getenv("OAUTH_REDIRECT_URI", "http://localhost:8000/api/v1/auth/oauth/callback"))
    OAUTH_SCOPE: str = os.getenv("OAUTH_SCOPE", "openid email profile")
    OAUTH_AUTHORIZE_URL: str = os.getenv("OAUTH_AUTHORIZE_URL", "https://accounts.google.com/o/oauth2/v2/auth")
    
    # ✅ 确保 `APP_BASE_URL` 默认指向 `127.0.0.1:8000`
    APP_BASE_URL: str = os.getenv("APP_BASE_URL", "http://127.0.0.1:8000")
    
    # ...
    REDIS_HOST: str = os.getenv("REDIS_HOST", "localhost")
    REDIS_PORT: int = int(os.getenv("REDIS_PORT", 6379))
    # ...


settings = Settings()