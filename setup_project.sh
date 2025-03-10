#!/bin/bash
# 脚本：setup_project.sh
# 用于自动生成 CheckEasyBackend 项目的完整目录结构及所有基础文件

# 创建项目主目录
mkdir -p CheckEasyBackend

cd CheckEasyBackend || exit

# 1. app 目录结构及文件

## app/api/
mkdir -p app/api
echo "# File: CheckEasyBackend/app/api/__init__.py" > app/api/__init__.py
cat <<'EOF' > app/api/api_v1.py
# File: CheckEasyBackend/app/api/api_v1.py
from fastapi import APIRouter

router = APIRouter()

# 示例路由：状态检测接口
@router.get("/status")
def get_status():
    return {"status": "API is running"}
EOF

## app/core/
mkdir -p app/core
echo "# File: CheckEasyBackend/app/core/__init__.py" > app/core/__init__.py
cat <<'EOF' > app/core/config.py
# File: CheckEasyBackend/app/core/config.py
import os
from dotenv import load_dotenv

# 加载 .env 环境变量文件
load_dotenv()

class Settings:
    DATABASE_URL: str = os.getenv("DATABASE_URL", "sqlite:///./test.db")
    # 可扩展：OAuth、邮件服务等全局配置

settings = Settings()
EOF

# 生成其他常见核心文件（可按需扩展）
cat <<'EOF' > app/core/db.py
# File: CheckEasyBackend/app/core/db.py
# 数据库连接管理示例
from app.core.config import settings
import sqlalchemy

engine = sqlalchemy.create_engine(settings.DATABASE_URL)
EOF

cat <<'EOF' > app/core/security.py
# File: CheckEasyBackend/app/core/security.py
# 安全模块（JWT、密码加密等）的示例代码
def verify_password(plain_password: str, hashed_password: str) -> bool:
    # 密码验证逻辑
    return plain_password == hashed_password
EOF

cat <<'EOF' > app/core/oauth.py
# File: CheckEasyBackend/app/core/oauth.py
# OAuth 配置及工具函数示例
def oauth_config():
    return {"provider": "Google", "client_id": "YOUR_CLIENT_ID"}
EOF

cat <<'EOF' > app/core/email.py
# File: CheckEasyBackend/app/core/email.py
# 邮件发送工具示例
def send_email(recipient: str, subject: str, body: str):
    # 邮件发送逻辑
    print(f"Sending email to {recipient}")
EOF

## app/modules/
mkdir -p app/modules

### 1. modules/auth/
mkdir -p app/modules/auth

#### 1.1. auth/login/
mkdir -p app/modules/auth/login
echo "# File: CheckEasyBackend/app/modules/auth/login/__init__.py" > app/modules/auth/login/__init__.py
cat <<'EOF' > app/modules/auth/login/routes.py
# File: CheckEasyBackend/app/modules/auth/login/routes.py
from fastapi import APIRouter

router = APIRouter()

@router.post("/login")
def login():
    return {"message": "Login route"}
EOF
cat <<'EOF' > app/modules/auth/login/schemas.py
# File: CheckEasyBackend/app/modules/auth/login/schemas.py
from pydantic import BaseModel

class LoginRequest(BaseModel):
    username: str
    password: str
EOF
cat <<'EOF' > app/modules/auth/login/utils.py
# File: CheckEasyBackend/app/modules/auth/login/utils.py
def verify_credentials(username: str, password: str) -> bool:
    # 示例：简单验证
    return True
EOF

#### 1.2. auth/register/
mkdir -p app/modules/auth/register
echo "# File: CheckEasyBackend/app/modules/auth/register/__init__.py" > app/modules/auth/register/__init__.py
cat <<'EOF' > app/modules/auth/register/routes.py
# File: CheckEasyBackend/app/modules/auth/register/routes.py
from fastapi import APIRouter

router = APIRouter()

@router.post("/register")
def register():
    return {"message": "Register route"}
EOF
cat <<'EOF' > app/modules/auth/register/schemas.py
# File: CheckEasyBackend/app/modules/auth/register/schemas.py
from pydantic import BaseModel

class RegisterRequest(BaseModel):
    username: str
    password: str
    email: str
    verification_code: str
EOF
cat <<'EOF' > app/modules/auth/register/utils.py
# File: CheckEasyBackend/app/modules/auth/register/utils.py
def generate_verification_code() -> str:
    return "123456"
EOF
cat <<'EOF' > app/modules/auth/register/models.py
# File: CheckEasyBackend/app/modules/auth/register/models.py
# 用户模型示例
class User:
    def __init__(self, username: str, email: str):
        self.username = username
        self.email = email
EOF

#### 1.3. auth/forgot_password/
mkdir -p app/modules/auth/forgot_password
echo "# File: CheckEasyBackend/app/modules/auth/forgot_password/__init__.py" > app/modules/auth/forgot_password/__init__.py
cat <<'EOF' > app/modules/auth/forgot_password/routes.py
# File: CheckEasyBackend/app/modules/auth/forgot_password/routes.py
from fastapi import APIRouter

router = APIRouter()

@router.post("/forgot-password")
def forgot_password():
    return {"message": "Forgot password route"}
EOF
cat <<'EOF' > app/modules/auth/forgot_password/schemas.py
# File: CheckEasyBackend/app/modules/auth/forgot_password/schemas.py
from pydantic import BaseModel

class ForgotPasswordRequest(BaseModel):
    email: str
    verification_code: str
EOF
cat <<'EOF' > app/modules/auth/forgot_password/utils.py
# File: CheckEasyBackend/app/modules/auth/forgot_password/utils.py
def generate_token():
    return "token"
EOF

#### 1.4. auth/oauth/
mkdir -p app/modules/auth/oauth
echo "# File: CheckEasyBackend/app/modules/auth/oauth/__init__.py" > app/modules/auth/oauth/__init__.py
cat <<'EOF' > app/modules/auth/oauth/routes.py
# File: CheckEasyBackend/app/modules/auth/oauth/routes.py
from fastapi import APIRouter

router = APIRouter()

@router.get("/oauth")
def oauth():
    return {"message": "OAuth route"}
EOF
cat <<'EOF' > app/modules/auth/oauth/schemas.py
# File: CheckEasyBackend/app/modules/auth/oauth/schemas.py
from pydantic import BaseModel

class OAuthResponse(BaseModel):
    token: str
EOF
cat <<'EOF' > app/modules/auth/oauth/utils.py
# File: CheckEasyBackend/app/modules/auth/oauth/utils.py
def process_oauth():
    return {"token": "oauth_token"}
EOF

### 2. modules/verification/
mkdir -p app/modules/verification

#### 2.1. verification/ocr/
mkdir -p app/modules/verification/ocr
echo "# File: CheckEasyBackend/app/modules/verification/ocr/__init__.py" > app/modules/verification/ocr/__init__.py
cat <<'EOF' > app/modules/verification/ocr/routes.py
# File: CheckEasyBackend/app/modules/verification/ocr/routes.py
from fastapi import APIRouter

router = APIRouter()

@router.post("/ocr")
def ocr():
    return {"message": "OCR route"}
EOF
cat <<'EOF' > app/modules/verification/ocr/schemas.py
# File: CheckEasyBackend/app/modules/verification/ocr/schemas.py
from pydantic import BaseModel

class OCRRequest(BaseModel):
    image_path: str
EOF
cat <<'EOF' > app/modules/verification/ocr/models.py
# File: CheckEasyBackend/app/modules/verification/ocr/models.py
class OCRRecord:
    def __init__(self, record_id: int):
        self.record_id = record_id
EOF
cat <<'EOF' > app/modules/verification/ocr/utils.py
# File: CheckEasyBackend/app/modules/verification/ocr/utils.py
def perform_ocr(image_path: str) -> str:
    return "识别结果"
EOF

#### 2.2. verification/manual/
mkdir -p app/modules/verification/manual
echo "# File: CheckEasyBackend/app/modules/verification/manual/__init__.py" > app/modules/verification/manual/__init__.py
cat <<'EOF' > app/modules/verification/manual/routes.py
# File: CheckEasyBackend/app/modules/verification/manual/routes.py
from fastapi import APIRouter

router = APIRouter()

@router.post("/manual-review")
def manual_review():
    return {"message": "Manual review route"}
EOF
cat <<'EOF' > app/modules/verification/manual/schemas.py
# File: CheckEasyBackend/app/modules/verification/manual/schemas.py
from pydantic import BaseModel

class ManualReviewRequest(BaseModel):
    record_id: int
    approve: bool
EOF
cat <<'EOF' > app/modules/verification/manual/models.py
# File: CheckEasyBackend/app/modules/verification/manual/models.py
class ManualReviewRecord:
    def __init__(self, record_id: int):
        self.record_id = record_id
EOF
cat <<'EOF' > app/modules/verification/manual/utils.py
# File: CheckEasyBackend/app/modules/verification/manual/utils.py
def review_record(record_id: int, approve: bool) -> bool:
    return approve
EOF

### 3. modules/checkin/
mkdir -p app/modules/checkin
echo "# File: CheckEasyBackend/app/modules/checkin/__init__.py" > app/modules/checkin/__init__.py
cat <<'EOF' > app/modules/checkin/routes.py
# File: CheckEasyBackend/app/modules/checkin/routes.py
from fastapi import APIRouter

router = APIRouter()

@router.post("/checkin")
def checkin():
    return {"message": "Check-in route"}
EOF
cat <<'EOF' > app/modules/checkin/schemas.py
# File: CheckEasyBackend/app/modules/checkin/schemas.py
from pydantic import BaseModel

class CheckinRequest(BaseModel):
    user_id: int
    document_id: str
EOF
cat <<'EOF' > app/modules/checkin/models.py
# File: CheckEasyBackend/app/modules/checkin/models.py
class CheckinRecord:
    def __init__(self, user_id: int):
        self.user_id = user_id
EOF
cat <<'EOF' > app/modules/checkin/utils.py
# File: CheckEasyBackend/app/modules/checkin/utils.py
def process_checkin(user_id: int) -> bool:
    return True
EOF

### 4. modules/notification/
mkdir -p app/modules/notification
echo "# File: CheckEasyBackend/app/modules/notification/__init__.py" > app/modules/notification/__init__.py
cat <<'EOF' > app/modules/notification/routes.py
# File: CheckEasyBackend/app/modules/notification/routes.py
from fastapi import APIRouter

router = APIRouter()

@router.get("/notification")
def notification():
    return {"message": "Notification route"}
EOF
cat <<'EOF' > app/modules/notification/schemas.py
# File: CheckEasyBackend/app/modules/notification/schemas.py
from pydantic import BaseModel

class Notification(BaseModel):
    title: str
    message: str
EOF
cat <<'EOF' > app/modules/notification/models.py
# File: CheckEasyBackend/app/modules/notification/models.py
class NotificationRecord:
    def __init__(self, notification_id: int):
        self.notification_id = notification_id
EOF
cat <<'EOF' > app/modules/notification/tasks.py
# File: CheckEasyBackend/app/modules/notification/tasks.py
def send_async_notification(notification):
    print("Sending async notification")
EOF

## app/uploads/ （用于存放上传文件）
mkdir -p app/uploads

## app/main.py
cat <<'EOF' > app/main.py
# File: CheckEasyBackend/app/main.py
from fastapi import FastAPI
from app.api.api_v1 import router as api_v1_router

app = FastAPI(
    title="CheckEasyBackend",
    description="企业级后端服务",
    version="1.0.0"
)

# 集成 API 路由
app.include_router(api_v1_router, prefix="/api/v1", tags=["API v1"])

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
EOF

# 2. database 目录及文件
mkdir -p database
echo "-- File: CheckEasyBackend/database/init.sql" > database/init.sql
echo "-- 数据库初始化脚本" >> database/init.sql

# 3. scripts 目录及文件
mkdir -p scripts
cat <<'EOF' > scripts/deploy.sh
#!/bin/bash
# File: CheckEasyBackend/scripts/deploy.sh
# 部署脚本示例
echo "部署项目..."
EOF
chmod +x scripts/deploy.sh

cat <<'EOF' > scripts/backup.sh
#!/bin/bash
# File: CheckEasyBackend/scripts/backup.sh
# 数据库备份脚本示例
echo "备份数据库..."
EOF
chmod +x scripts/backup.sh

# 4. tests 目录及文件
mkdir -p tests
echo "# File: CheckEasyBackend/tests/__init__.py" > tests/__init__.py
cat <<'EOF' > tests/test_auth.py
# File: CheckEasyBackend/tests/test_auth.py
def test_login():
    assert True, "测试登录逻辑"
EOF

# 5. 根目录下其他文件

## requirements.txt
cat <<'EOF' > requirements.txt
fastapi==0.95.0
uvicorn==0.21.1
python-dotenv==1.0.0
pydantic==1.10.2
EOF

## Dockerfile
cat <<'EOF' > Dockerfile
# File: CheckEasyBackend/Dockerfile
FROM python:3.10-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
EOF

## docker-compose.yml
cat <<'EOF' > docker-compose.yml
# File: CheckEasyBackend/docker-compose.yml
version: '3.8'

services:
  web:
    build: .
    ports:
      - "8000:8000"
    volumes:
      - .:/app
    environment:
      - DATABASE_URL=sqlite:///./test.db
EOF

## .env
cat <<'EOF' > .env
# File: CheckEasyBackend/.env
DATABASE_URL=sqlite:///./test.db
EOF

## README.md
cat <<'EOF' > README.md
# CheckEasyBackend

企业级后端服务项目
EOF

echo "项目完整目录结构和所有文件已创建完成！"