from fastapi import FastAPI
from app.database import get_db
from app.routers import links, auth
from app.logging_config import setup_logging
import logging


setup_logging()

logger = logging.getLogger(__name__)

app = FastAPI(
  title="ShortLink",
  description="Сервис сокращения ссылок",
  version="1.0.0"
)


app.include_router(links.router)
app.include_router(auth.router)


@app.get("/")
async def check_get():
  logger.info("Проверка статуса сервера")
  return {
    "status": "ok"
  }

