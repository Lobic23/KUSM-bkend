from fastapi import APIRouter, Depends
from sqlalchemy import func, desc
from sqlalchemy.orm import Session
from ..models import EnergyDB, MeterDB, PowerDB, VoltageDB, CurrentDB
from ..database import get_db
from ..api.iammeter import voltage_status, calculate_unbalance, current_status
from ..api.iammeter import get_meter_id_by_name
from datetime import datetime

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
    return result
    
MONTHS = {
    1: "jan", 2: "feb", 3: "mar", 4: "apr",
    5: "may", 6: "jun", 7: "jul", 8: "aug",
    9: "sep", 10: "oct", 11: "nov", 12: "dec"
}
@router.get("/monthly_average/{year}/{meter_name}")
def monthly_average(meter_name: str, year: int, db:Session = Depends(get_db)):
    data = {}
    meter_id = get_meter_id_by_name(meter_name)
    for month in range(1, 13):
        start_date = datetime(year, month, 1)
        end_date = (
            datetime(year + 1, 1, 1)
            if month == 12
            else datetime(year, month + 1, 1)
        )

        avg_current = db.query(
            (
                func.coalesce(func.avg(CurrentDB.phase_A_current), 0) +
                func.coalesce(func.avg(CurrentDB.phase_B_current), 0) +
                func.coalesce(func.avg(CurrentDB.phase_C_current), 0)
            )
        ).filter(
            CurrentDB.meter_id == meter_id,
            CurrentDB.timestamp >= start_date,
            CurrentDB.timestamp < end_date
        ).scalar()
        
        avg_voltage = db.query(
            (
                func.coalesce(func.avg(VoltageDB.phase_A_voltage), 0) +
                func.coalesce(func.avg(VoltageDB.phase_B_voltage), 0) +
                func.coalesce(func.avg(VoltageDB.phase_C_voltage), 0)
            )
        ).filter(
            VoltageDB.meter_id == meter_id,
            VoltageDB.timestamp >= start_date,
            VoltageDB.timestamp < end_date
        ).scalar()       

        avg_power = db.query(
            (
                func.coalesce(func.avg(PowerDB.phase_A_active_power), 0) +
                func.coalesce(func.avg(PowerDB.phase_B_active_power), 0) +
                func.coalesce(func.avg(PowerDB.phase_C_active_power), 0)
            )
        ).filter(
            PowerDB.meter_id == meter_id,
            PowerDB.timestamp >= start_date,
            PowerDB.timestamp < end_date
        ).scalar()

        avg_energy = db.query(
            (
                func.coalesce(func.avg(EnergyDB.phase_A_grid_consumption), 0) +
                func.coalesce(func.avg(EnergyDB.phase_B_grid_consumption), 0) +
                func.coalesce(func.avg(EnergyDB.phase_C_grid_consumption), 0)
            )
        ).filter(
            EnergyDB.meter_id == meter_id,
            EnergyDB.timestamp >= start_date,
            EnergyDB.timestamp < end_date
        ).scalar()

        data[MONTHS[month]] = {
            "average_current": avg_current,
            "average_voltage":avg_voltage,
            "average_power": avg_power,
            "average_energy": avg_energy
        }

    return {
        "success": True,
        "year": year,
        "data": data
    }
@router.get("/voltage")
def get_voltage_analysis(db: Session = Depends(get_db)):
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
            result.append({
                "meter_name": m.name,
                "status": "NO_DATA"
            })
            continue

        unbalance = calculate_unbalance(
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
            "status": voltage_status(unbalance)      
        })

    return {
        "success": True,
        "data": result
    }

@router.get("/current")
def get_current_analysis(db: Session = Depends(get_db)):
    meters = db.query(MeterDB).all()
    result = []
    for m in meters:
        latest_current = (
            db.query(CurrentDB)
            .filter(CurrentDB.meter_id == m.meter_id)
            .order_by(desc(CurrentDB.timestamp))
            .first()
        )   

        if not latest_current:
            result.append({
                "meter_name": m.name,
                "status": "NO_DATA"
            })
            continue

        unbalance = calculate_unbalance(
            latest_current.phase_A_current,
            latest_current.phase_B_current,
            latest_current.phase_C_current
        )

        result.append({
            "meter_name": m.name,
            "timestamp": latest_current.timestamp,
            "phase_A_current": latest_current.phase_A_current,
            "phase_B_current": latest_current.phase_B_current,
            "phase_C_current": latest_current.phase_C_current,
            "current_unbalance_percent": unbalance,
            "status": current_status(unbalance)      
        })

    return {
        "success": True,
        "data": result
    }

