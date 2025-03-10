import uvicorn
import logging
import time
from fastapi import FastAPI, Request
from contextlib import asynccontextmanager
app = FastAPI()
from app.core.config import settings
from app.api.api_v1 import api_router  # 导入 api_v1 的路由
from dotenv import load_dotenv
load_dotenv()  # 🚩 强制明确加载 .env 文件

print(">>> DEBUG: This is the main.py I am currently running! <<<")
print("Runtime SECRET_KEY:", settings.SECRET_KEY)
print("Runtime ALGORITHM:", settings.ALGORITHM)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger("CheckEasyBackend.main")

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup事件逻辑
    logger.info("Starting up CheckEasyBackend application...")
    yield
    # Shutdown事件逻辑
    logger.info("Shutting down CheckEasyBackend application...")

app = FastAPI(
    title=getattr(settings, "PROJECT_NAME", "CheckEasyBackend"),
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan  # 正确添加 lifespan 事件处理器
)

# 注册全局中间件
@app.middleware("http")
async def add_process_time_header(request: Request, call_next):
    start_time = time.time()
    response = await call_next(request)
    process_time = time.time() - start_time
    response.headers["X-Process-Time"] = f"{process_time:.4f}"
    return response

# 正确注册路由
app.include_router(api_router, prefix="/api/v1")

if __name__ == "__main__":
    uvicorn.run(
        "app.main:app",
        host=getattr(settings, "HOST", "0.0.0.0"),
        port=getattr(settings, "PORT", 8000),
        reload=True
    )