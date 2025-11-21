import requests
from modules.llm_extract_city_and_forecast_days import get_city_and_forecast_days_for_weatherapi
from decouple import config
from datetime import datetime, timedelta

def get_weather_forecast(question: str, include_hours: bool, hours_before: int, hours_after: int) -> dict:
    """
    Queries WeatherAPI based on the city, forecast days, and optional hour extracted from the user question.
    Returns a structured dictionary with current weather, forecast, and hourly data.
    
    Args:
        question (str): User question containing city, date, and optional hour info.
        include_hours (bool): Whether to include hourly forecast data.
        hours_before (int): Number of hours before the requested hour to include.
        hours_after (int): Number of hours after the requested hour to include.
    
    Returns:
        dict: Weather data structured for easy consumption.
    """
    api_key = config("WEATHERAPI_API_KEY")

    # --- LLM call to extract city, forecast_days, and optional hour ---
    result = get_city_and_forecast_days_for_weatherapi(question)
    city = result.get("city")
    forecast_days = result.get("forecast_days")
    hour = result.get("hour") 

    print("Extracted city:", city)
    print("Extracted forecast_days:", forecast_days)
    print("Extracted hour:", hour)

    if not city or not forecast_days:
        return {"error": "City or forecast_days could not be extracted."}

    # --- Build the WeatherAPI URL ---
    url = f"http://api.weatherapi.com/v1/forecast.json?key={api_key}&q={city}&days={forecast_days}&aqi=no&alerts=no"
    response = requests.get(url)

    if response.status_code != 200:
        return {"error": f"Failed to retrieve weather data, status code {response.status_code}."}

    data = response.json()

    # --- Build structured dictionary ---
    weather_result = {
        "city": data["location"]["name"],
        "current": {
            "temperature_c": data["current"]["temp_c"],
            "condition": data["current"]["condition"]["text"]
        },
        "forecast_days": []
    }

    for day in data["forecast"]["forecastday"]:
        day_dict = {
            "date": day["date"],
            "max_temp_c": day["day"]["maxtemp_c"],
            "min_temp_c": day["day"]["mintemp_c"],
            "condition": day["day"]["condition"]["text"]
        }

        if include_hours:
            if hour is not None:
                # --- Include hours in the range [hour - hours_before, hour + hours_after] ---
                start_hour = max(0, hour - hours_before)
                end_hour = min(23, hour + hours_after)
                matching_hours = [
                    {
                        "time": h["time"],
                        "temp_c": h["temp_c"],
                        "condition": h["condition"]["text"]
                    }
                    for h in day["hour"]
                    if start_hour <= datetime.strptime(h["time"], "%Y-%m-%d %H:%M").hour <= end_hour
                ]
                day_dict["hours"] = matching_hours
            else:
                # --- Include all hours if no specific hour requested ---
                day_dict["hours"] = [
                    {
                        "time": h["time"],
                        "temp_c": h["temp_c"],
                        "condition": h["condition"]["text"]
                    }
                    for h in day["hour"]
                ]

        weather_result["forecast_days"].append(day_dict)

    return weather_result
