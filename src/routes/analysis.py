from fastapi import APIRouter, Depends
from sqlalchemy import func
from sqlalchemy.orm import Session
from ..models import EnergyDB, MeterDB, PowerDB
from ..database import get_db

router = APIRouter(prefix="/analysis", tags=["analysis"])

@router.get("/avg_consumption")
def get_consumption_and_power(db: Session = Depends(get_db)):
    meters = db.query(MeterDB).all()
    result = []
    for m in meters:
        power_data = db.query(func.avg(PowerDB.phase_A_active_power),func.avg(PowerDB.phase_B_active_power),func.avg(PowerDB.phase_C_active_power)).filter(PowerDB.meter_id == m.meter_id).one()
        energy_data = db.query(func.avg(EnergyDB.phase_A_grid_consumption),func.avg(EnergyDB.phase_B_grid_consumption),func.avg(EnergyDB.phase_C_grid_consumption)).filter(EnergyDB.meter_id == m.meter_id).one()
        total_avg_power = 0
        total_avg_energy = 0
        
        total_avg_power = sum(d or 0 for d in power_data)
        total_avg_energy = sum(d or 0 for d in energy_data)

        result.append({
            "meter_name": m.name,
            "average_power": total_avg_power,
            "average_energy": total_avg_energy
        })
    return{
        "success": True,
        "result": result
    }
