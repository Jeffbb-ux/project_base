from fastapi import APIRouter

from app.modules.auth.login.routes import router as login_router
from app.modules.auth.forgot_password.routes import router as forgot_password_router
from app.modules.auth.oauth.routes import router as oauth_router
# 导入注册路由
from app.modules.auth.register.routes import router as register_router
from app.modules.checkin.routes import router as checkin_router
from app.modules.notification.routes import router as notification_router
from app.modules.verification.ocr.routes import router as ocr_router
from app.modules.verification.upload.uploads.upload import router as upload_router
#from app.modules.verification.manual.routes import router as manual_router



api_router = APIRouter()

# 注册各模块的路由
api_router.include_router(login_router, prefix="/auth", tags=["Auth Login"])
api_router.include_router(forgot_password_router, prefix="/auth", tags=["Forgot Password"])
api_router.include_router(oauth_router, prefix="/auth/oauth", tags=["OAuth"])
# 注册注册模块的路由
api_router.include_router(register_router, prefix="/auth", tags=["Register"])
api_router.include_router(checkin_router, prefix="/checkin", tags=["Checkin"])
api_router.include_router(notification_router, prefix="/notification", tags=["Notification"])
api_router.include_router(ocr_router, prefix="/verification/ocr", tags=["OCR Verification"])
api_router.include_router(upload_router, prefix="/verification/upload", tags=["Passport Upload"])  # <-- 新增路由注册

#api_router.include_router(manual_router, prefix="/verification/manual", tags=["Manual Verification"])  # <-- 新增路由注册