from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy import desc
from sqlalchemy.orm import Session
from ..models import MeterDB, MeterData, MeterDataDB
from ..database import get_db

router = APIRouter(prefix="/meter", tags=["meter"])

@router.get("")
def get_all_meters(db: Session = Depends(get_db)):
    meters = db.query(MeterDB).all()

    return {
        "success": True,
        "count": len(meters),
        "data": [
            {
                "meter_id": m.meter_id,
                "name": m.name,
                "sn": m.sn	
            }
            for m in meters
        ]
    }

# @router.get("/{meter_sn}")
# def get_meter_data(meter_sn: str):
#     # TODO : @imp
#     # stash these things in the db
#     result = fetch_meter_data(meter_sn)

#     if result is None:
#         raise HTTPException(
#             status_code=500,
#             detail="Failed to fetch meter data"
#         )

#     return {
#         "success": True,
#         "data": result
#     }

@router.get("/{meter_id}/latest", response_model=MeterData)
def get_latest_meter_data(
    meter_id: int,
    db: Session = Depends(get_db)
):
    data = (
        db.query(MeterDataDB)
        .filter(MeterDataDB.meter_id == meter_id)
        .order_by(desc(MeterDataDB.timestamp))
        .first()
    )

    if not data:
        raise HTTPException(status_code=404, detail="No data found for this meter")

    return data
