from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from app.database import get_db
from app.schemas.user import UserCreate, UserResponse, Token
from app.models.user import User
from app.services.auth import get_password_hash, verify_password, create_access_token


router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register", response_model=UserResponse, status_code=201)
def register(user_data: UserCreate, db: Session = Depends(get_db)):
  existing_user = db.query(User).filter(User.email == user_data.email).first()
  
  if existing_user:
    raise HTTPException(status_code=400, detail="Email уже зарегистрирован")
  
  hashed_password = get_password_hash(user_data.password)
  new_user = User(email=user_data.email, hashed_password=hashed_password)
  
  db.add(new_user)
  db.commit()
  db.refresh(new_user)
  
  return new_user


@router.post("/login", response_model=Token)
def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
  user = db.query(User).filter(User.email == form_data.username).first()
  
  if not user or not verify_password(form_data.password, user.hashed_password):
    raise HTTPException(
      status_code=401,
      detail="Неверный email или пароль",
      headers={"WWW-Authenticate": "Bearer"}
    )
  
  access_token = create_access_token(data={"sub": user.email})
  
  return {"access_token": access_token, "token_type": "bearer"}


