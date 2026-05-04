from slowapi import Limiter
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from fastapi import FastAPI, HTTPException, status
from app.database import get_db
from app.routers import links, auth
from app.logging_config import setup_logging
import logging


setup_logging()

logger = logging.getLogger(__name__)

limiter = Limiter(key_func=get_remote_address)

app = FastAPI(
  title="ShortLink",
  description="Сервис сокращения ссылок",
  version="1.0.0"
)

app.state.limiter = limiter

@app.exception_handler(RateLimitExceeded)
async def rate_limit_handler(request, exc):
  raise HTTPException(
    status_code=status.HTTP_429_TOO_MANY_REQUESTS,
  detail="Слишком много запросов. Попробуйте позже."
  )


app.include_router(links.router)
app.include_router(auth.router)


@app.get("/")
async def check_get():
  logger.info("Проверка статуса сервера")
  return {
    "status": "ok"
  }

