from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.user import User
from app.services.auth import verify_token


oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")


async def get_current_user(
  token: str = Depends(oauth2_scheme),
  db: Session = Depends(get_db)
) -> User:
  payload = verify_token(token)
  
  if payload is None:
    raise HTTPException(
      status_code=status.HTTP_401_UNAUTHORIZED,
      detail="Невалидный токен",
      headers={"WWW-Authentication": "Bearer"}
    )
  
  email = payload.get("sub")
  
  if email is None:
    raise HTTPException(
      status_code=status.HTTP_401_UNAUTHORIZED,
      detail="Токен не содержит email",
      headers={"WWW-Authentication": "Bearer"}
    )
  
  user = db.query(User).filter(User.email == email).first()
  
  if user is None:
    raise HTTPException(
      status_code=status.HTTP_401_UNAUTHORIZED,
      detail="Пользователь не найден",
      headers={"WWW-Authentication": "Bearer"}
    )
  
  return user