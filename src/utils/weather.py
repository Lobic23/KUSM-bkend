import os
import requests
from pprint import pprint
from dotenv import load_dotenv

load_dotenv()

API_KEY = os.getenv("WEATHER_API")
BASE_URL = "https://api.openweathermap.org/data/2.5"

if not API_KEY:
    raise RuntimeError("OPENWEATHER_API environment variable not set")


def fetch_weather(endpoint: str, params: dict) -> dict:
    url = f"{BASE_URL}/{endpoint}"
    response = requests.get(url, params=params, timeout=10)
    response.raise_for_status()
    return response.json()


def get_current_and_forecast(lat: float, lon: float) -> dict:
    # --- Current weather ---
    current = fetch_weather(
        "weather",
        {
            "lat": lat,
            "lon": lon,
            "appid": API_KEY,
            "units": "metric"
        }
    )

    # --- 5-day / 3-hour forecast ---
    forecast = fetch_weather(
        "forecast",
        {
            "lat": lat,
            "lon": lon,
            "appid": API_KEY,
            "units": "metric"
        }
    )

    return {
        "location": {
            "city": current["name"],
            "lat": lat,
            "lon": lon
        },
        "current": {
            "temp": current["main"]["temp"],
            "feels_like": current["main"]["feels_like"],
            "humidity": current["main"]["humidity"],
            "weather": current["weather"][0]["description"],
            "wind_speed": current["wind"]["speed"]
        },
        "forecast": [
            {
                "datetime": item["dt_txt"],
                "temp": item["main"]["temp"],
                "weather": item["weather"][0]["description"],
                "humidity": item["main"]["humidity"]
            }
            for item in forecast["list"]
        ]
    }


if __name__ == "__main__":
    # Dhulikhel coordinates
    lat = 27.6194
    lon = 85.5386

    data = get_current_and_forecast(lat, lon)
    pprint(data)
