import requests
from datetime import datetime
import pytz
def get_live_weather_risk(lat, lon):
    """
    Fetches exact ML features (1d, 3d, 7d, 14d rolling sums) 
    by dynamically matching the current IST timestamp.
    """
    url = "https://api.open-meteo.com/v1/forecast"
    
    # 1. FIXED: past_days increased to 14 to cover the max ML feature window
    params = {
        "latitude": lat,
        "longitude": lon,
        "hourly": "precipitation",
        "past_days": 14,
        "forecast_days": 1,
        "timezone": "Asia/Kolkata" 
    }
    
    try:
        response = requests.get(url, params=params)
        response.raise_for_status()
        data = response.json()
        
        # 2. FIXED: Dynamic Timestamp Matching (No hardcoded offset)
        # Format current time exactly how Open-Meteo returns it (YYYY-MM-DDTHH:00)
        ist = pytz.timezone('Asia/Kolkata')
        current_time_str = datetime.now(ist).strftime("%Y-%m-%dT%H:00")
        
        time_array = data['hourly']['time']
        precip_array = data['hourly']['precipitation']
        
        # Find exact index of the current hour
        current_index = time_array.index(current_time_str)
        
        # 3. FIXED: Exact ML Feature Calculation (Rolling backwards from NOW)
        # 1d = 24h, 3d = 72h, 7d = 168h, 14d = 336h
        rainfall_1d = sum(precip_array[current_index - 24 : current_index])
        rainfall_3d = sum(precip_array[current_index - 72 : current_index])
        rainfall_7d = sum(precip_array[current_index - 168 : current_index])
        rainfall_14d = sum(precip_array[current_index - 336 : current_index])
        
        # Calculate max_rainfall_7d: Divide the last 168 hours into 7 daily chunks
        last_7_days_hourly = precip_array[current_index - 168 : current_index]
        daily_totals = [sum(last_7_days_hourly[i:i+24]) for i in range(0, 168, 24)]
        max_rainfall_7d = max(daily_totals)
        
        return {
            "status": "success",
            "latitude": lat,
            "longitude": lon,
            "rainfall_1d": round(rainfall_1d, 2),
            "rainfall_3d": round(rainfall_3d, 2),
            "rainfall_7d": round(rainfall_7d, 2),
            "rainfall_14d": round(rainfall_14d, 2),
            "max_rainfall_7d": round(max_rainfall_7d, 2)
        }
        
    except Exception as e:
        print(f"API Error at {lat}, {lon}: {e}")
        # Failsafe output MUST also match ML features to prevent total system crash
        return {
            "status": "error",
            "rainfall_1d": 0.0, "rainfall_3d": 0.0,
            "rainfall_7d": 0.0, "rainfall_14d": 0.0,
            "max_rainfall_7d": 0.0
        }