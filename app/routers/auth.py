from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, Response
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
import logging
import uuid
import os

from app.database import get_db
from app.schemas.user import UserCreate, UserResponse, Token, ChangePassword, UserUpdate
from app.models.user import User
from app.services.auth import get_password_hash, verify_password, create_access_token
from app.dependencies import get_current_user


logger = logging.getLogger(__name__)

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register", response_model=UserResponse, status_code=201)
def register(user_data: UserCreate, db: Session = Depends(get_db)):
  logger.info(f"Попытка регистрации: {user_data.email}")
  existing_user = db.query(User).filter(User.email == user_data.email).first()
  
  if existing_user:
    logger.warning(f"Email уже занят: {user_data.email}")
    raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Email уже зарегистрирован")
  
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
      status_code=status.HTTP_401_UNAUTHORIZED,
      detail="Неверный email или пароль",
      headers={"WWW-Authenticate": "Bearer"}
    )
  
  access_token = create_access_token(data={"sub": user.email})
  
  logger.info(f"Успешный вход: {form_data.username}")
  return {"access_token": access_token, "token_type": "bearer"}


@router.patch("/change-password")
def change_password(
  data: ChangePassword,
  db: Session = Depends(get_db), 
  current_user: User = Depends(get_current_user)
):
  logger.info(f"Попытка смены пароля: {current_user.email}")
  
  if not verify_password(data.old_password, current_user.hashed_password):
    raise HTTPException(
      status_code=status.HTTP_400_BAD_REQUEST,
      detail="Неверный старый пароль"
    )
  
  current_user.hashed_password = get_password_hash(data.new_password)
  db.commit()
  
  return {"detail": "Пароль успешно изменён"}


@router.get("/me", response_model=UserResponse)
def get_my_profile(
  db: Session = Depends(get_db),
  current_user: User = Depends(get_current_user)
):
  return current_user


@router.patch("/me", response_model=UserResponse)
def patch_user_profile(
  user_data: UserUpdate,
  db: Session = Depends(get_db),
  current_user: User = Depends(get_current_user)
):
  current_user.username = user_data.username
  db.commit()
  db.refresh(current_user)
  
  return current_user


@router.post("/me/avatar")
async def add_avatar(
  file: UploadFile,
  db: Session = Depends(get_db),
  current_user: User = Depends(get_current_user)
):
  unique_file_name = f"{current_user.id}_{uuid.uuid4()}.jpg"
  file_path = os.path.join("app", "static", "avatars", unique_file_name)
  
  content = await file.read()
  
  with open(file_path, "wb") as f:
    f.write(content)
  
  current_user.avatar_url = f"/app/static/avatars/{unique_file_name}"
  db.commit()
  db.refresh(current_user)
  
  return current_user


@router.delete("/me")
def delete_user_profile(
  db: Session = Depends(get_db),
  current_user: User = Depends(get_current_user)
):
  db.delete(current_user)
  db.commit()
  
  return Response(status_code=status.HTTP_204_NO_CONTENT)