import requests
from modules.llm_extract_city_and_forecast_days import get_city_and_forecast_days_for_weatherapi
from decouple import config
from datetime import datetime

def get_weather_forecast(question: str, include_hours: bool, hours_before: int, hours_after: int) -> dict:
    """
    Queries WeatherAPI for exactly one target day based on the city, target date, and optional hour extracted from the user's question.
    
    Args:
        question (str): User input containing city, date, and optional hour information.
        include_hours (bool): Whether to include hourly forecast data.
        hours_before (int): Number of hours before the requested hour to include.
        hours_after (int): Number of hours after the requested hour to include.
    
    Returns:
        dict: Structured weather data for the target day.
    """
    api_key = config("WEATHERAPI_API_KEY")

    # --- LLM call to extract city, hour, and target date ---
    result = get_city_and_forecast_days_for_weatherapi(question)
    city = result.get("city")
    hour = result.get("hour")
    target_date_str = result.get("forecast_date")  # e.g., "2025-11-23"

    print("Extracted city:", city)
    print("Extracted hour:", hour)
    print("Target date:", target_date_str)

    if not city or not target_date_str:
        return {"error": "City or target date could not be extracted."}

    today = datetime.now().date()
    target_date = datetime.strptime(target_date_str, "%Y-%m-%d").date()
    forecast_days = (target_date - today).days + 1  # ensure the target day is included

    # --- Call WeatherAPI with the calculated number of days ---
    url = f"http://api.weatherapi.com/v1/forecast.json?key={api_key}&q={city}&days={forecast_days}&aqi=no&alerts=no"
    response = requests.get(url)
    if response.status_code != 200:
        return {"error": f"Failed to retrieve weather data, status code {response.status_code}."}

    data = response.json()

    # --- Filter exactly the target day ---
    forecast_day = None
    for day in data["forecast"]["forecastday"]:
        if day["date"] == target_date_str:
            forecast_day = day
            break

    if not forecast_day:
        return {"error": "Forecast for target date not found."}

    day_dict = {
        "date": forecast_day["date"],
        "max_temp_c": forecast_day["day"]["maxtemp_c"],
        "min_temp_c": forecast_day["day"]["mintemp_c"],
        "condition": forecast_day["day"]["condition"]["text"]
    }

    if include_hours:
        if hour is not None:
            start_hour = max(0, hour - hours_before)
            end_hour = min(23, hour + hours_after)
            day_dict["hours"] = [
                {
                    "time": h["time"],
                    "temp_c": h["temp_c"],
                    "condition": h["condition"]["text"]
                }
                for h in forecast_day["hour"]
                if start_hour <= datetime.strptime(h["time"], "%Y-%m-%d %H:%M").hour <= end_hour
            ]
        else:
            # include all hours if no specific hour requested
            day_dict["hours"] = [
                {
                    "time": h["time"],
                    "temp_c": h["temp_c"],
                    "condition": h["condition"]["text"]
                }
                for h in forecast_day["hour"]
            ]

    return {
        "city": city,
        "forecast_day": day_dict
    }
