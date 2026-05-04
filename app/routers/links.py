import os
from slowapi import Limiter
from slowapi.util import get_remote_address
from fastapi import APIRouter, Depends, HTTPException, Response, status, Request
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session
from sqlalchemy import func
import logging
from typing import List
from datetime import datetime, timezone, tzinfo

from app.database import get_db
from app.schemas.link import LinkCreate, LinkResponse, LinkStats, LinkUpdate, UserStatsResponse
from app.models.link import Link
from app.models.user import User
from app.services.shortcode import generate_unique_short_code
from app.dependencies import get_current_user
from app.cache.redis_client import redis_client


limiter = Limiter(key_func=get_remote_address)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/links", tags=["links"])

def rate_limit():
  if os.getenv("PYTEST_RUNNING") == "true":
    return lambda f: f
  return limiter.limit("5/minute")

@router.post("/shorten", response_model=LinkResponse)
@rate_limit()
def create_short_link(
  request: Request,
  link_data: LinkCreate, 
  db: Session = Depends(get_db),
  current_user: User = Depends(get_current_user)
):
  
  existing = db.query(Link).filter(
    Link.user_id == current_user.id,
    Link.original_url == link_data.original_url
    ).first()
  
  if existing:
    if existing.expires_at is None:
      return existing
    expires = existing.expires_at
    
    if expires.tzinfo is None:
      expires = expires.replace(tzinfo=timezone.utc)
    if expires >= datetime.now(timezone.utc):
      return existing
  
  logger.info(f"Создание ссылки пользователем {current_user.email}: {link_data.original_url}")
  short_code = generate_unique_short_code(db, length=6)
  db_link = Link(
    short_code=short_code, 
    original_url=link_data.original_url,
    user_id=current_user.id,
    expires_at=link_data.expires_at
  )
  
  db.add(db_link)
  db.commit()
  db.refresh(db_link)
  
  logger.info(f"Создана ссылка: {short_code} -> {link_data.original_url[:50]}...")
  return db_link


@router.get("/stats", response_model=UserStatsResponse, status_code=status.HTTP_200_OK)
def get_user_links_stats(
  db: Session = Depends(get_db),
  current_user: User = Depends(get_current_user)
):
  total_links = db.query(func.count(Link.id)).filter(Link.user_id == current_user.id).scalar()
  total_clicks = db.query(func.sum(Link.clicks)).filter(Link.user_id == current_user.id).scalar()
  most_popular = db.query(Link).filter(Link.user_id == current_user.id).order_by(Link.clicks.desc()).first()
  recently_created = db.query(Link).filter(Link.user_id == current_user.id).order_by(Link.created_at.desc()).first()
  expired_count = db.query(func.count(Link.id)).filter(
    Link.user_id == current_user.id,
    Link.expires_at != None,
    Link.expires_at < datetime.now(timezone.utc)
  ).scalar()
  
  return {
    "total_links": total_links,
    "total_clicks": total_clicks or 0,
    "most_popular": most_popular,
    "recently_created": recently_created,
    "expired_count": expired_count
  }


@router.get("/", response_model=List[LinkResponse])
def get_list_all_user_links(
  search: str | None = None,
  order_by: str = "created_at",
  order_dir: str = "desc",
  skip: int = 0,
  limit: int = 10,
  db: Session = Depends(get_db), 
  current_user: User = Depends(get_current_user)
):
  query = db.query(Link).filter(Link.user_id == current_user.id)
  allowed_fields = {"clicks", "created_at"}
  
  if search:
    query = query.filter(Link.original_url.contains(search))
  
  if order_by and order_by in allowed_fields:
    field = getattr(Link, order_by)
    
    if order_dir == "desc":
      query = query.order_by(field.desc())
    else:
      query = query.order_by(field.asc())
  
  links = query.offset(skip).limit(limit).all()
  
  return links


@router.get("/{short_code}/stats", response_model=LinkStats)
def get_link(short_code: str, db: Session = Depends(get_db)):
  link = db.query(Link).filter(Link.short_code == short_code).first()
  
  if link is None:
    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Ссылка не найдена")
  
  return link


@router.delete("/{short_code}", status_code=204)
def delete_url_user(
  short_code: str,
  db: Session = Depends(get_db),
  current_user: User = Depends(get_current_user)
):
  link = db.query(Link).filter(Link.short_code == short_code).first()
  
  if not link:
    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Ссылка не найдена")
  
  if link.user_id != current_user.id:
    raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Нет доступа к этой ссылке")
  
  db.delete(link)
  db.commit()
  
  logger.info(f"Удалена ссылка {short_code} пользователем {current_user.email}")
  return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.patch("/{short_code}", status_code=200)
def patch_updating_user_link(
  new_url: LinkUpdate,
  short_code: str,
  db: Session = Depends(get_db),
  current_user: User = Depends(get_current_user)
):
  link = db.query(Link).filter(Link.short_code == short_code).first()
  
  if link is None:
    logger.warning(f"Не найдена ссылка в базе: {short_code}")
    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Ссылка не найдена")
  
  if link.user_id != current_user.id:
    raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Нет доступа к этой ссылке")
  
  link.original_url = new_url.original_url
  
  db.commit()
  db.refresh(link)
  
  logger.info(f"Ссылка {short_code} успешно изменена на {new_url}.")
  return link


@router.get("/{short_code}")
def redirect_to_original(short_code: str, db: Session = Depends(get_db)):
  try:
    cached_url = redis_client.get(f"link:{short_code}")
  except Exception:
    cached_url = None
  
  if cached_url:
    logger.info(f"Ссылка найдена в redis: {short_code}")
    link = db.query(Link).filter(Link.short_code == short_code).first()
    if link:
      link.clicks += 1
      db.commit()
    return RedirectResponse(url=cached_url, status_code=status.HTTP_302_FOUND)
  
  link = db.query(Link).filter(Link.short_code == short_code).first()
  
  if link is None:
    logger.warning(f"Попытка перехода по несуществующей ссылке: {short_code}")
    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Ссылка не найдена")
  
  if link.expires_at is not None:
    expires_at = link.expires_at
    
    if expires_at.tzinfo is None:
      expires_at = expires_at.replace(tzinfo=timezone.utc)
    
    if expires_at < datetime.now(timezone.utc):
      logger.warning(f"Срок действия ссылки истёк: {short_code}")
      raise HTTPException(status_code=status.HTTP_410_GONE, detail="Срок действия ссылки истёк")
  
  logger.info(f"Ссылка добавлена в redis: {short_code}")
  redis_client.setex(f"link:{short_code}", 3600, link.original_url)
  
  link.clicks += 1
  
  db.commit()
  
  logger.info(f"Редирект: {short_code} -> {link.original_url[:50]}... (клик #{link.clicks})")
  return RedirectResponse(url=link.original_url, status_code=status.HTTP_302_FOUND)