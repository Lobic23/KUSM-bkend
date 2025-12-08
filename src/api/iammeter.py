import requests
from ..settings import settings
URL = 'https://www.iammeter.com/api/v1/site/meterdata2/'

import requests

def fetch_meter_data(meter_sn):
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





