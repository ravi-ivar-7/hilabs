from sqlalchemy import Column, String, DateTime
from sqlalchemy.ext.declarative import declared_attr
from datetime import datetime
import uuid

from ..core.database import Base


class BaseModel(Base):
    """Base model with common fields"""
    __abstract__ = True
    
    @declared_attr
    def __tablename__(cls):
        return cls.__name__.lower()
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
