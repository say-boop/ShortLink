from pydantic import BaseModel, field_validator
import re
import datetime


class LinkCreate(BaseModel):
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

class LinkResponse(BaseModel):
  id: int
  short_code: str
  original_url: str
  clicks: int
  created_at: datetime.datetime
  user_id: int | None = None
  
  model_config = {
    "from_attributes": True
  }

class LinkStats(BaseModel):
  short_code: str
  original_url: str
  clicks: int
  created_at: datetime.datetime
  user_id: int | None = None
  
  model_config = {
    "from_attributes": True
  }