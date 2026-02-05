from fastapi import APIRouter, HTTPException, Depends, Query, Request
from sqlalchemy.orm import Session

from src.api.iammeter import add_iammeter_station
from src.init_meter import remove_meter
from src.routes.meter import BulkLocationUpdate
from ..models import MeterDB
from ..database import get_db
from .auth.auth_utils import require_admin

router = APIRouter(
    prefix="/meter/edit",
    tags=["meter"],
    dependencies=[Depends(require_admin)],
)



@router.put("/locations")
def update_meter_locations(
    bulk_update: BulkLocationUpdate,
    db: Session = Depends(get_db)
):
    """Update map locations for multiple meters at once"""
    updated_count = 0
    errors = []
    
    try:
        for location_item in bulk_update.locations:
            meter = db.query(MeterDB).filter(
                MeterDB.meter_id == location_item.meter_id
            ).first()
            
            if meter:
                meter.x = location_item.x
                meter.y = location_item.y
                updated_count += 1
            else:
                errors.append(f"Meter ID {location_item.meter_id} not found")
        
        db.commit()
        
        return {
            "success": True,
            "message": f"Updated locations for {updated_count} meter(s)",
            "updated_count": updated_count,
            "errors": errors if errors else None
        }
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to update locations: {str(e)}")


@router.post("/addmeter")
async def add_meter(request: Request, db: Session = Depends(get_db)):
    payload = await request.json()

    payload.setdefault("CountryId", "44")
    payload.setdefault("TimeZone", "5.75")
    payload.setdefault("TimeZoneName", "(GMT +05:45) Kathmandu")
    payload.setdefault("Province", "")
    payload.setdefault("City", "")
    payload.setdefault("Address", "")
    payload.setdefault("Position", "27.619399267478876, 85.5388709190866")
    payload.setdefault("DZPriceUnit", "NPR")

    if "Name" not in payload or "sn" not in payload:
        raise HTTPException(
            status_code= 422, 
            detail="Missing required fields: Name or sn"
        )

    result = add_iammeter_station(payload)

    if result is None:
        raise HTTPException(
            status_code=502, 
            detail="Failed to create station in IAMMETER"
        )

    if not result.get("successful", True):
        raise HTTPException(
            status_code=502, 
            detail=f"IAMMETER API error: {result.get('message', 'Unknown error')}"
        )

    return {
        "success": True, 
        "data": result
    }
    
@router.delete("/{sn}")
def delete_meter(sn: str, force: bool = Query(default = False), db: Session = Depends(get_db)):
    try:
        removed = remove_meter(db,sn,force=force)
        return {
            "success": True, "message": f"Meter '{removed.name}' removed successfully"}
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))    
    except ValueError as e:
        raise HTTPException(status_code=400, detail=f"Cannot delete meter : {e}")


