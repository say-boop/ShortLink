from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
import logging

from app.database import get_db
from app.schemas.user import UserCreate, UserResponse, Token
from app.models.user import User
from app.services.auth import get_password_hash, verify_password, create_access_token


logger = logging.getLogger(__name__)

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register", response_model=UserResponse, status_code=201)
def register(user_data: UserCreate, db: Session = Depends(get_db)):
  logger.info(f"Попытка регистрации: {user_data.email}")
  existing_user = db.query(User).filter(User.email == user_data.email).first()
  
  if existing_user:
    logger.warning(f"Email уже занят: {user_data.email}")
    raise HTTPException(status_code=400, detail="Email уже зарегистрирован")
  
  hashed_password = get_password_hash(user_data.password)
  new_user = User(email=user_data.email, hashed_password=hashed_password)
  
  db.add(new_user)
  db.commit()
  db.refresh(new_user)
  
  logger.info(f"Успешная регистрация: {user_data.email} (ID: {new_user.id})")
  return new_user


@router.post("/login", response_model=Token)
def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
  logger.info(f"Попытка входа: {form_data.username}")
  user = db.query(User).filter(User.email == form_data.username).first()
  
  if not user or not verify_password(form_data.password, user.hashed_password):
    logger.warning(f"Неудачный вход: {form_data.username}")
    raise HTTPException(
      status_code=401,
      detail="Неверный email или пароль",
      headers={"WWW-Authenticate": "Bearer"}
    )
  
  access_token = create_access_token(data={"sub": user.email})
  
  logger.info(f"Успешный вход: {form_data.username}")
  return {"access_token": access_token, "token_type": "bearer"}


