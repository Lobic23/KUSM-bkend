from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from src.database import get_db
from src.models import MeterStatusDB

router = APIRouter(prefix="/meter_status", tags=["meter_status"])

@router.get("/")
def get_all_status(db: Session = Depends(get_db)):
    return db.query(MeterStatusDB).all()

@router.get("/down")
def get_down(db: Session = Depends(get_db)):
    return db.query(MeterStatusDB).filter(MeterStatusDB.is_flatline == True).all()

@router.get("/{meter_id}")
def get_one(meter_id: int, db: Session = Depends(get_db)):
    return db.get(MeterStatusDB, meter_id)
