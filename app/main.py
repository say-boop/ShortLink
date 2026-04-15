from fastapi import FastAPI
from app.database import get_db


app = FastAPI()


@app.get("/")
async def check_get():
  return {
    "status": "ok"
  }

