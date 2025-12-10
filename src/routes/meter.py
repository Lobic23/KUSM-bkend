from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy import desc
from sqlalchemy.orm import Session
from ..models import MeterDB, MeterDataDB
from ..database import get_db
from ..api.iammeter import fetch_meter_data

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

@router.get("/{meter_id}/latest")
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

    return {
        "meter_id": meter_id,
        "timestamp": data.timestamp,
        "phases": {
            "A": {
                "current": data.phase_A_current,
                "voltage": data.phase_A_voltage,
                "active_power": data.phase_A_active_power,
                "power_factor": data.phase_A_power_factor,
                "grid_consumption": data.phase_A_grid_consumption,
                "exported_power": data.phase_A_exported_power,
            },
            "B": {
                "current": data.phase_B_current,
                "voltage": data.phase_B_voltage,
                "active_power": data.phase_B_active_power,
                "power_factor": data.phase_B_power_factor,
                "grid_consumption": data.phase_B_grid_consumption,
                "exported_power": data.phase_B_exported_power,
            },
            "C": {
                "current": data.phase_C_current,
                "voltage": data.phase_C_voltage,
                "active_power": data.phase_C_active_power,
                "power_factor": data.phase_C_power_factor,
                "grid_consumption": data.phase_C_grid_consumption,
                "exported_power": data.phase_C_exported_power,
            },
        },
    }