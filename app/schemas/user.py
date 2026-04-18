from pydantic import BaseModel, EmailStr, field_validator
from datetime import datetime

class UserCreate(BaseModel):
  email: EmailStr
  password: str
  
  @field_validator('password')
  def validate_password(cls, v: str) -> str:
    if len(v) < 8:
      raise ValueError('Пароль должен быть не менее 8 символов')
    return v


class UserResponse(BaseModel):
  id: int
  email: str
  created_at: datetime
  
  model_config = {
    "from_attributes": True
  }


class UserLogin(BaseModel):
  email: EmailStr
  password: str


