# File: CheckEasyBackend/tests/test_integration.py
import pytest
from fastapi.testclient import TestClient
from datetime import datetime

from app.main import app

client = TestClient(app)

def test_auth_register_success():
    payload = {
        "username": "jane_doe",  # 虽然 RegisterRequest 模型不需要 username，但这里保留测试字段
        "password": "Password123!",
        "email": "jane@example.com",
        "captcha": "1234"  # 添加必需的 captcha 字段
    }
    response = client.post("/api/v1/auth/register", json=payload)
    assert response.status_code == 200
    data = response.json()
    expected_message = "Registration successful, please check your email to activate your account"
    assert data["message"] == expected_message

# 测试登录接口
def test_auth_login_success():
    payload = {"username": "john_doe", "password": "Passw0rd!"}
    response = client.post("/api/v1/auth/login", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert "token" in data
    assert data["message"] == "Login successful"

# 测试忘记密码接口
def test_forgot_password_email():
    payload = {"email": "john@example.com"}
    response = client.post("/api/v1/auth/forgot-password", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert "Reset password email sent" in data["message"]

# 测试 Google OAuth 登录接口
def test_google_oauth_login_redirect():
    response = client.get("/api/v1/auth/oauth/login")
    assert response.status_code in (302, 307)
    assert "accounts.google.com" in response.headers.get("location", "")

# 测试入住接口
def test_checkin_success():
    payload = {
        "user_id": 1,
        "certificate_id": "CERT123456789",
        "checkin_time": "2025-03-05T14:30:00Z",
        "room_number": "101",
        "remarks": "Test checkin",
        "additional_info": {"source": "unit test"}
    }
    response = client.post("/api/v1/checkin/checkin", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert "Check-in successful" in data["message"]
    assert "checkin_id" in data
    datetime.fromisoformat(data["checkin_time"].replace("Z", "+00:00"))

# 测试通知邮件发送接口
def test_notification_email():
    payload = {
        "to": "recipient@example.com",
        "subject": "Test Notification",
        "message": "This is a test notification message.",
        "from_email": "noreply@example.com"
    }
    response = client.post("/api/v1/notification/email", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "success"

# 测试 OCR 上传无效文件
def test_ocr_upload_invalid_file():
    data = {"doc_type": "身份证", "country": "中国", "side": "front"}
    files = {"file": ("test.txt", b"Not an image", "text/plain")}
    response = client.post("/api/v1/verification/ocr/upload", data=data, files=files)
    assert response.status_code == 400
    assert "Invalid file type" in response.json()["detail"]

# 测试 OCR 上传有效图像文件（使用 monkeypatch 模拟）
def test_ocr_upload_valid_image(monkeypatch):
    async def fake_process_document(file, doc_type, country, side):
        return {
            "success": True,
            "data": {"name": "张三", "document_number": "123456789012345678"},
            "message": "OCR processing succeeded"
        }

    monkeypatch.setattr("app.modules.verification.ocr.utils.process_document", fake_process_document)

    data = {"doc_type": "身份证", "country": "中国", "side": "front"}
    files = {"file": ("test.jpg", b"\xff\xd8\xff\xe0", "image/jpeg")}
    response = client.post("/api/v1/verification/ocr/upload", data=data, files=files)
    assert response.status_code == 200
    resp_data = response.json()
    assert "OCR processing succeeded" in resp_data["message"]
    assert resp_data["data"]["name"] == "张三"