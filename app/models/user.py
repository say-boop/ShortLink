from app.database import Base
from sqlalchemy import Column, Integer, String, DateTime, Boolean
from sqlalchemy.orm import relationship
from datetime import datetime, timezone


class User(Base):
  __tablename__ = "users"
  
  id = Column(Integer, primary_key=True, index=True)
  username = Column(String, unique=True, index=True, nullable=True)
  avatar_url = Column(String, nullable=True)
  email = Column(String, unique=True, index=True, nullable=False)
  hashed_password = Column(String, nullable=False)
  created_at = Column(DateTime, default=datetime.now(timezone.utc))
  is_active = Column(Boolean, default=True)
  links = relationship("Link", back_populates="user")


