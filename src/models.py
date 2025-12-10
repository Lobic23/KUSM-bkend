from datetime import datetime
from typing import Optional
from sqlalchemy import Column, String, DateTime, Boolean, Enum, Float, Integer, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from pydantic import BaseModel, EmailStr
import enum
Base = declarative_base()

# SQLAlchemy ORM Model
class UserDB(Base):
    __tablename__ = "users"
    
    id = Column(String, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    name = Column(String, nullable=True)
    picture = Column(String, nullable=True)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

# Pydantic Models for API
class User(BaseModel):
    id: str
    email: EmailStr
    name: Optional[str] = None
    picture: Optional[str] = None
    is_active: bool
    created_at: datetime
    updated_at: datetime
    class Config:
        from_attributes=True
         # this thing just tells sqlalchemy User is deseializable from the table

class MeterDB(Base):
    __tablename__ = "meters"

    meter_id = Column(Integer, primary_key=True, autoincrement=True)
    name= Column(String)
    sn = Column(String)


class Phase(enum.Enum):
    PHASE_A = 'A'
    PHASE_B = 'B'
    PHASE_C = 'C'

class Meter(BaseModel):
    meter_id: int
    name: str
    sn: str
    class Config:
        from_attributes=True

class MeterDataDB(Base):
    __tablename__ = "meterdata"

    data_id = Column(Integer, primary_key=True, autoincrement=True)
    phase = Column(Enum(Phase, name = 'phase'), nullable=False)
    current = Column(Float, nullable=False)
    voltage = Column(Float, nullable=False)
    active_power = Column(Float, nullable=False)
    power_factor = Column(Float, nullable=False)
    grid_consumption= Column(Float, nullable=False)
    exported_power = Column(Float, nullable=False)
    timestamp = Column(DateTime, nullable=False)
    meter_id = Column(Integer, ForeignKey('meters.meter_id'))