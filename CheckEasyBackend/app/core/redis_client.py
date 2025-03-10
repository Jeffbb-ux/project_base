# File: app/core/redis_client.py
import redis
from app.core.config import settings

# 根据你的配置来初始化 Redis 连接
r = redis.Redis(
    host=settings.REDIS_HOST, 
    port=settings.REDIS_PORT, 
    db=0
)