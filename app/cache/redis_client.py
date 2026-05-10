import redis
from app.config import settings


try:
  redis_client = redis.Redis(
    host=settings.REDIS_HOST,
    port=settings.REDIS_PORT,
    decode_responses=True
  )
  redis_client.ping()
  REDIS_AVAILABLE = True
except Exception:
  redis_client = None
  REDIS_AVAILABLE = False