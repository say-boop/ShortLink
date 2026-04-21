from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session
import logging
from typing import List

from app.database import get_db
from app.schemas.link import LinkCreate, LinkResponse, LinkStats
from app.models.link import Link
from app.models.user import User
from app.services.shortcode import generate_unique_short_code
from app.dependencies import get_current_user


logger = logging.getLogger(__name__)

router = APIRouter(prefix="/links", tags=["links"])


@router.post("/shorten", response_model=LinkResponse, status_code=201)
def create_short_link(
  link_data: LinkCreate, 
  db: Session = Depends(get_db),
  current_user: User = Depends(get_current_user)
):
  logger.info(f"Создание ссылки пользователем {current_user.email}: {link_data.original_url}")
  
  short_code = generate_unique_short_code(db, length=6)
  db_link = Link(
    short_code=short_code, 
    original_url=link_data.original_url,
    user_id=current_user.id
  )
  
  db.add(db_link)
  db.commit()
  db.refresh(db_link)
  
  logger.info(f"Создана ссылка: {short_code} -> {link_data.original_url[:50]}...")
  return db_link


@router.get("/", response_model=List[LinkResponse])
def get_list_all_user_links(
  skip: int = 0,
  limit: int = 10,
  db: Session = Depends(get_db), 
  current_user: User = Depends(get_current_user)
):
  links = db.query(Link).filter(Link.user_id == current_user.id).order_by(Link.created_at.desc()).offset(skip).limit(limit).all()
  
  if links is None:
    raise HTTPException(status_code=404, detail="Ссылки не найдены")
  
  return links


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
    logger.warning(f"Попытка перехода по несуществующей ссылке: {short_code}")
    raise HTTPException(status_code=404, detail="Ссылка не найдена")
  
  link.clicks += 1
  
  db.commit()
  
  logger.info(f"Редирект: {short_code} -> {link.original_url[:50]}... (клик #{link.clicks})")
  return RedirectResponse(url=link.original_url, status_code=302)