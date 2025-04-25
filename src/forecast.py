import requests
from datetime import datetime, timedelta
from typing import Dict, Any

BASE_URL = "https://api.ipma.pt/open-data/forecast/oceanography/daily/hp-daily-sea-forecast-day{idDay}.json"
TARGET_LOCAL_ID = 1111026  # Lisbon coast

def fetch_forecast(idDay: int) -> Dict[str, Any]:
    """Fetch forecast for a specific day (1=Saturday, 2=Sunday)."""
    url = BASE_URL.format(idDay=idDay)
    response = requests.get(url)
    response.raise_for_status()
    return response.json()

def find_spot_data(forecast_data: Dict[str, Any]) -> Dict[str, Any]:
    """Find Lisbon coast entry."""
    for entry in forecast_data["data"]:
        if entry["globalIdLocal"] == TARGET_LOCAL_ID:
            return entry
    raise ValueError(f"No data for {TARGET_LOCAL_ID}")

def parse_forecast(raw_data: Dict[str, Any], entry: Dict[str, Any]) -> Dict[str, Any]:
    """Extract parameters with day names."""
    forecast_date = datetime.strptime(raw_data["forecastDate"], "%Y-%m-%d")
    return {
        "date": raw_data["forecastDate"],
        "day_name": forecast_date.strftime("%A").lower(),  # "saturday"/"sunday"
        "swell_height_min": float(entry["waveHighMin"]),
        "swell_height_max": float(entry["waveHighMax"]),
        "swell_period_min": float(entry["wavePeriodMin"]),
        "swell_period_max": float(entry["wavePeriodMax"]),
        "primary_wave_direction": entry["predWaveDir"],
        "sea_surface_temp_min": float(entry["sstMin"]),
        "sea_surface_temp_max": float(entry["sstMax"])
    }

def get_weekend_forecast() -> dict:
    """Return forecast with dynamic day names based on actual dates."""
    weekend_forecast = {}
    
    for idDay in [1, 2]:
        try:
            raw_data = fetch_forecast(idDay)
            spot_entry = find_spot_data(raw_data)
            parsed_data = parse_forecast(raw_data, spot_entry)
            
            # Use actual day name from the parsed data as the key
            day_name = parsed_data["day_name"]
            weekend_forecast[day_name] = parsed_data
            
        except Exception as e:
            print(f"Error for idDay {idDay}: {str(e)}")
    
    return weekend_forecast