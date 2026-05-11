from pydantic import BaseModel, EmailStr, field_validator
from datetime import datetime

class UserCreate(BaseModel):
  email: EmailStr
  password: str
  username: str | None = None
  
  @field_validator('password')
  def validate_password(cls, v: str) -> str:
    if len(v) < 8:
      raise ValueError('Пароль должен быть не менее 8 символов')
    return v


class UserResponse(BaseModel):
  id: int
  email: str
  created_at: datetime
  username: str | None = None
  
  model_config = {
    "from_attributes": True
  }


class UserLogin(BaseModel):
  email: EmailStr
  password: str


class UserUpdate(BaseModel):
  username: str


class Token(BaseModel):
  access_token: str
  token_type: str = "bearer"


class TokenData(BaseModel):
  email: str | None = None


class ChangePassword(BaseModel):
  old_password: str
  new_password: str
  
  @field_validator('new_password')
  def validate_new_password(cls, passwd: str) -> str:
    if len(passwd) < 8:
      raise ValueError('Пароль должен быть не менее 8 символов')
    return passwd