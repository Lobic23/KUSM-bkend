import requests
from ..settings import settings
from sqlalchemy.orm import Session
from ..models import MeterDB, MeterDataDB, Phase
from ..database import get_db
from datetime import datetime

db: Session = next(get_db())
URL = 'https://www.iammeter.com/api/v1/site/meterdata2/'

import requests

def fetch_meter_data(meter_sn:str):
    params = {
        "token": settings.IAMMETER_TOKEN
    }
    try:
        r = requests.get(URL+meter_sn, timeout=10, params=params)
        r.raise_for_status()
        payload = r.json()

        if not payload.get("successful"):
            print("API error:", payload.get("message"))
            return None

        data = payload["data"]

        fields = [
            "voltage",
            "current",
            "active_power",
            "power_factor",
            "grid_consumption",
            "exported_power",
        ]

        readings = {}

        for phase, values in zip(["A","B","C"], data["values"]):
            readings[phase] = dict(zip(fields, values))

        return {
            "times": {
                "local": data["localTime"],
                "gmt": data["gmtTime"]
            },
            "phases": readings
        }

    except Exception as e:
        print("Fetch failed:", e)
        return None

async def store_all_meter_data():
    meters = db.query(MeterDB).all()
    for meter in meters:
        meter_data = fetch_meter_data(meter.sn)
        phase_a = meter_data['phases']['A']
        phase_b = meter_data['phases']['B']
        phase_c = meter_data['phases']['C']
        await insert_meterdata(phase_a, meter_data['times']['local'],Phase.PHASE_A, meter.meter_id)
        await insert_meterdata(phase_b, meter_data['times']['local'],Phase.PHASE_B, meter.meter_id)
        await insert_meterdata(phase_c, meter_data['times']['local'],Phase.PHASE_C, meter.meter_id)
        print('data stored')

async def insert_meterdata(readings, time, phase, meter_id):
    data = MeterDataDB(
        phase = phase,
        current = readings['current'],
        voltage = readings['voltage'],
        active_power= readings['active_power'],
        power_factor = readings['power_factor'],
        grid_consumption = readings['grid_consumption'],
        exported_power = readings['exported_power'],
        timestamp = datetime.strptime(time, "%Y/%m/%d %H:%M:%S"),
        meter_id = meter_id
    )
    db.add(data)
    db.commit()
    db.refresh(data)
    print('works')
    
    
