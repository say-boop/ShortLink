from app.database import Base
from sqlalchemy import Column, Integer, String, DateTime
from datetime import datetime, timezone


class Link(Base):
  __tablename__ = "links"
  
  id = Column(Integer, primary_key=True, index=True)
  short_code = Column(String, unique=True, index=True, nullable=False)
  original_url = Column(String, nullable=False)
  created_at = Column(DateTime, default=datetime.now(timezone.utc))
  clicks = Column(Integer, default=0)

link = Link()