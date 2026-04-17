from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database import get_db
from app.schemas.link import LinkCreate, LinkResponse
from app.models.link import Link
from app.services.shortcode import generate_unique_short_code


router = APIRouter(prefix="/links", tags=["links"])

@router.post("/shorten", response_model=LinkResponse, status_code=201)
def create_short_link(link_data: LinkCreate, db: Session = Depends(get_db)):
  short_code = generate_unique_short_code(db, length=6)
  db_link = Link(short_code=short_code, original_url=link_data.original_url)
  
  db.add(db_link)
  
  db.commit()
  db.refresh(db_link)
  return db_link

