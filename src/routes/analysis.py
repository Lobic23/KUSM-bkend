from fastapi import APIRouter, Depends
from sqlalchemy import func, desc
from sqlalchemy.orm import Session
from ..models import EnergyDB, MeterDB, PowerDB, VoltageDB
from ..database import get_db
from ..api.iammeter import voltage_unbalance_status, calculate_voltage_unbalance

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

@router.get("/voltage")
def get_voltage_unbalance(db: Session = Depends(get_db)):
    meters = db.query(MeterDB).all()
    result = []
    for m in meters:
        latest_voltage = (
            db.query(VoltageDB)
            .filter(VoltageDB.meter_id == m.meter_id)
            .order_by(desc(VoltageDB.timestamp))
            .first()
        )

        if not latest_voltage:
            continue

        unbalance = calculate_voltage_unbalance(
            latest_voltage.phase_A_voltage,
            latest_voltage.phase_B_voltage,
            latest_voltage.phase_C_voltage
        )

        result.append({
            "meter_name": m.name,
            "timestamp": latest_voltage.timestamp,
            "phase_A_voltage": latest_voltage.phase_A_voltage,
            "phase_B_voltage": latest_voltage.phase_B_voltage,
            "phase_C_voltage": latest_voltage.phase_C_voltage,
            "voltage_unbalance_percent": unbalance,
            "status": voltage_unbalance_status(unbalance)      
        })

    return {
        "success": True,
        "data": result
    }

