import requests
from modules.llm_extract_city_and_forecast_days import get_city_and_forecast_days_for_weatherapi
from decouple import config
from datetime import datetime, timedelta

def get_weather_forecast(question: str, include_hours: bool, hours_before: int, hours_after: int) -> dict:
    """
    Retrieves the weather forecast for a specific day and city based on a user's natural language query.
    
    This function integrates with an LLM (Large Language Model) to extract structured information from
    the user's question, such as the target city, the desired date, and an optional hour. It then queries
    WeatherAPI to obtain the forecast for exactly the specified day and optionally includes a range of
    hourly forecasts around the requested hour.

    Features:
    ----------
    1. Automatic extraction of:
        - City (e.g., "Cologne", "Berlin")
        - Target date (absolute or relative, e.g., "tomorrow", "in 3 days")
        - Hour (0–23) if specified

    2. Fallback mechanisms if the LLM does not provide certain information:
        - target_date_str is None → uses today's date
        - city is None → attempts to detect the user's current city via IP geolocation; defaults to "Berlin" if detection fails
        - hour is None → sets the hour to current hour + 2 (wraps around 24)

    3. Forecast retrieval:
        - Calculates the number of days (`forecast_days`) needed to include the target date in the WeatherAPI response
        - Calls WeatherAPI with `days=forecast_days` to ensure the target day is included
        - Filters the response to return exactly the target day only

    4. Hourly forecast handling:
        - If `include_hours=True` and a specific hour is provided, only hours in the range [hour - hours_before, hour + hours_after] are returned
        - If no hour is specified, all hours of the day are included

    Parameters:
    -----------
    question : str
        A natural language question or statement from the user that includes information about the desired city,
        date, and optionally the hour for which weather information is requested.
    
    include_hours : bool
        If True, includes hourly forecast data in the output; otherwise, only daily summary is returned.

    hours_before : int
        The number of hours before the requested hour to include in the hourly forecast (ignored if include_hours=False or hour is None).

    hours_after : int
        The number of hours after the requested hour to include in the hourly forecast (ignored if include_hours=False or hour is None).

    Returns:
    --------
    dict
        A structured dictionary containing:
        - "city": The city for which the forecast was retrieved
        - "forecast_day": A dictionary with:
            - "date": The target date of the forecast (YYYY-MM-DD)
            - "max_temp_c": Maximum temperature in Celsius
            - "min_temp_c": Minimum temperature in Celsius
            - "condition": Text description of the weather
            - "hours" (optional): A list of hourly forecasts, each with:
                - "time": Timestamp of the hour (YYYY-MM-DD HH:MM)
                - "temp_c": Temperature in Celsius
                - "condition": Text description of the weather

    Notes:
    ------
    - This function ensures that the forecast corresponds exactly to the day the user requested,
      even if the WeatherAPI response includes multiple days.
    - Hourly data is optional and will only be returned if requested.
    - The function handles relative dates such as "tomorrow" or "in 3 days" automatically.
    - Fallbacks are in place for missing city, date, or hour to provide robust behavior.
    """
    api_key = config("WEATHERAPI_API_KEY")

    # --- LLM call ---
    result = get_city_and_forecast_days_for_weatherapi(question)
    city = result.get("city")
    hour = result.get("hour")
    target_date_str = result.get("forecast_date")  # e.g., "2025-11-23"

    today = datetime.now().date()

    # --- Fallback target date ---
    if not target_date_str:
        target_date = today
        target_date_str = target_date.strftime("%Y-%m-%d")
    else:
        target_date = datetime.strptime(target_date_str, "%Y-%m-%d").date()

    # --- Fallback city via IP ---
    if not city:
        try:
            ip_data = requests.get("https://ipinfo.io/json").json()
            city = ip_data.get("city", "Berlin")
        except:
            city = "Berlin"

    # --- Fallback hour ---
    if hour is None:
        hour = (datetime.now().hour + 2) % 24

    forecast_days = (target_date - today).days + 1

    print(city, hour, target_date_str)
    # --- WeatherAPI request ---
    url = f"http://api.weatherapi.com/v1/forecast.json?key={api_key}&q={city}&days={forecast_days}&aqi=no&alerts=no"
    response = requests.get(url)
    if response.status_code != 200:
        return {"error": f"Failed to retrieve weather data, status code {response.status_code}."}

    data = response.json()

    # --- Filter exactly the target day ---
    forecast_day = next((d for d in data["forecast"]["forecastday"] if d["date"] == target_date_str), None)
    if not forecast_day:
        return {"error": "Forecast for target date not found."}

    day_dict = {
        "date": forecast_day["date"],
        "max_temp_c": forecast_day["day"]["maxtemp_c"],
        "min_temp_c": forecast_day["day"]["mintemp_c"],
        "condition": forecast_day["day"]["condition"]["text"]
    }

    # --- Include hourly data if requested ---
    if include_hours:
        start_hour = max(0, hour - hours_before)
        end_hour = min(23, hour + hours_after)
        day_dict["hours"] = [
            {"time": h["time"], "temp_c": h["temp_c"], "condition": h["condition"]["text"]}
            for h in forecast_day["hour"]
            if start_hour <= datetime.strptime(h["time"], "%Y-%m-%d %H:%M").hour <= end_hour
        ]

    return {"city": city, "forecast_day": day_dict}
