from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database import get_db
from app.schemas.user import UserCreate, UserResponse
from app.models.user import User
from app.services.auth import get_password_hash


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


