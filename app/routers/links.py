from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session

from app.database import get_db
from app.schemas.link import LinkCreate, LinkResponse, LinkStats
from app.models.link import Link
from app.models.user import User
from app.services.shortcode import generate_unique_short_code
from app.dependencies import get_current_user


router = APIRouter(prefix="/links", tags=["links"])

@router.post("/shorten", response_model=LinkResponse, status_code=201)
def create_short_link(
  link_data: LinkCreate, 
  db: Session = Depends(get_db),
  current_user: User = Depends(get_current_user)
):
  short_code = generate_unique_short_code(db, length=6)
  db_link = Link(
    short_code=short_code, 
    original_url=link_data.original_url,
    user_id=current_user.id
  )
  
  db.add(db_link)
  db.commit()
  db.refresh(db_link)
  return db_link


@router.get("/{short_code}/stats", response_model=LinkStats)
def get_link(short_code: str, db: Session = Depends(get_db)):
  link = db.query(Link).filter(Link.short_code == short_code).first()
  
  if link is None:
    raise HTTPException(status_code=404, detail="Ссылка не найдена")
  
  return link


@router.get("/{short_code}")
def redirect_to_original(short_code: str, db: Session = Depends(get_db)):
  link = db.query(Link).filter(Link.short_code == short_code).first()
  
  if link is None:
    raise HTTPException(status_code=404, detail="Ссылка не найдена")
  
  link.clicks += 1
  
  db.commit()
  
  return RedirectResponse(url=link.original_url, status_code=302)