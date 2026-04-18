from fastapi import FastAPI
from app.database import get_db
from app.routers import links, auth


app = FastAPI(
  title="ShortLink",
  description="Сервис сокращения ссылок",
  version="1.0.0"
)


app.include_router(links.router)
app.include_router(auth.router)


@app.get("/")
async def check_get():
  return {
    "status": "ok"
  }

