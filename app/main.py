from fastapi import FastAPI
from app.database import get_db
from app.routers import links


app = FastAPI()
app.include_router(links.router)

@app.get("/")
async def check_get():
  return {
    "status": "ok"
  }

