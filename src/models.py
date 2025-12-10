from datetime import datetime
from typing import Optional
from sqlalchemy import Column, Index, String, DateTime, Boolean, Enum, Float, Integer, ForeignKey, desc
from sqlalchemy.ext.declarative import declarative_base
from pydantic import BaseModel, EmailStr
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


class Meter(BaseModel):
    meter_id: int
    name: str
    sn: str
    class Config:
        from_attributes=True

class MeterDataDB(Base):
    __tablename__ = "meterdata"

    data_id = Column(Integer, primary_key=True, autoincrement=True)
    timestamp = Column(DateTime, nullable=False)
    meter_id = Column(Integer, ForeignKey('meters.meter_id'))

    phase_A_current = Column(Float, nullable=False)
    phase_A_voltage = Column(Float, nullable=False)
    phase_A_active_power = Column(Float, nullable=False)
    phase_A_power_factor = Column(Float, nullable=False)
    phase_A_grid_consumption= Column(Float, nullable=False)
    phase_A_exported_power = Column(Float, nullable=False)

    phase_B_current = Column(Float, nullable=False)
    phase_B_voltage = Column(Float, nullable=False)
    phase_B_active_power = Column(Float, nullable=False)
    phase_B_power_factor = Column(Float, nullable=False)
    phase_B_grid_consumption= Column(Float, nullable=False)
    phase_B_exported_power = Column(Float, nullable=False)

    phase_C_current = Column(Float, nullable=False)
    phase_C_voltage = Column(Float, nullable=False)
    phase_C_active_power = Column(Float, nullable=False)
    phase_C_power_factor = Column(Float, nullable=False)
    phase_C_grid_consumption= Column(Float, nullable=False)
    phase_C_exported_power = Column(Float, nullable=False)

    __table_args__ = (
        Index("idx_meter_timestamp", "meter_id", desc("timestamp")),
    )

class MeterData(BaseModel):
    data_id: int
    meter_id: int
    timestamp: datetime

    phase_A_current: float
    phase_A_voltage: float
    phase_A_active_power: float
    phase_A_power_factor: float
    phase_A_grid_consumption: float
    phase_A_exported_power: float

    phase_B_current: float
    phase_B_voltage: float
    phase_B_active_power: float
    phase_B_power_factor: float
    phase_B_grid_consumption: float
    phase_B_exported_power: float

    phase_C_current: float
    phase_C_voltage: float
    phase_C_active_power: float
    phase_C_power_factor: float
    phase_C_grid_consumption: float
    phase_C_exported_power: float

    class Config:
        from_attributes=True

