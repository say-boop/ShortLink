from pydantic import BaseModel, field_validator
import re
from datetime import datetime, timezone


class LinkCreate(BaseModel):
  original_url: str
  expires_at: datetime | None = None
  
  @field_validator('original_url')
  @classmethod
  def validate_url(cls, v: str) -> str:
    if v is None:
      return v
    
    pattern = r"^https?://[^\s/$.?#].[^\s]*$"
    
    if not re.match(pattern, v):
      raise ValueError('Некорректный URL')
    return v
  
  @field_validator('expires_at')
  @classmethod
  def validate_expires_at(cls, exp: datetime | None) -> datetime | None:
    if exp is None:
      return exp
    
    if exp.tzinfo is None:
      exp = exp.replace(tzinfo=timezone.utc)
    
    now = datetime.now(timezone.utc)
    
    if exp < now:
      raise ValueError('Дата истечения должна быть в будущем')
    return exp

class LinkResponse(BaseModel):
  id: int
  short_code: str
  original_url: str
  clicks: int
  created_at: datetime
  user_id: int | None = None
  expires_at: datetime | None = None
  
  model_config = {
    "from_attributes": True
  }

class LinkStats(BaseModel):
  short_code: str
  original_url: str
  clicks: int
  created_at: datetime
  user_id: int | None = None
  
  model_config = {
    "from_attributes": True
  }

class LinkUpdate(BaseModel):
  original_url: str
  
  @field_validator('original_url')
  @classmethod
  def validate_url(cls, v: str) -> str:
    if v is None:
      return v
    
    pattern = r"^https?://[^\s/$.?#].[^\s]*$"
    
    if not re.match(pattern, v):
      raise ValueError('Некорректный URL')
    return v

class UserStatsResponse(BaseModel):
  total_links: int
  total_clicks: int
  most_popular: LinkResponse | None = None
  recently_created: LinkResponse | None = None
  expired_count: int