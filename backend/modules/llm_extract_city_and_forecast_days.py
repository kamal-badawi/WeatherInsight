def get_city_and_forecast_days_for_weatherapi(question: str) -> dict:
    """
    Extracts structured information from a user's natural language question to determine the city,
    target date, and optional hour for a weather forecast query.

    This function uses a Large Language Model (LLM) to parse relative and absolute dates, times,
    and city names from a text query, and computes the number of forecast days required for the
    WeatherAPI to include the target date.

    Key Features:
    -------------
    1. Extracts the city:
        - Converts names to a format compatible with WeatherAPI queries.
        - Defaults to "Berlin" if the city cannot be determined.
    2. Extracts the target date:
        - Handles absolute dates (e.g., "2025-11-23") and relative expressions
          like "today", "tomorrow", "day after tomorrow", "in 3 days".
        - Converts relative expressions to an actual date based on the current date.
    3. Extracts the hour:
        - If specified, returns the hour as an integer between 0–23.
        - Defaults to None if no hour is mentioned.
    4. Computes `forecast_days`:
        - Calculated as `(target_date - today) + 1` to ensure WeatherAPI includes the target date.
        - Defaults to 1 if the date cannot be determined.

    Parameters:
    -----------
    question : str
        A natural language string from the user containing information about the city, date,
        and optionally the hour for which the weather forecast is requested.

    Returns:
    --------
    dict
        A dictionary containing:
        - "city": str, the city formatted for WeatherAPI (fallback: "Berlin")
        - "forecast_date": str, the absolute date in "YYYY-MM-DD" format
        - "hour": int or None, the requested hour (0–23) or None if not specified
        - "forecast_days": int, number of days from today until the target date (used for WeatherAPI)

    Notes:
    ------
    - This function relies on an LLM (Gemini) for accurate extraction and interpretation
      of natural language date and time expressions.
    - Relative date expressions are automatically converted to absolute dates.
    - In case of an error with the LLM or JSON parsing, fallback defaults are provided:
      city = "Berlin", forecast_days = 1, hour = None, and an optional "error" message.
    """
    import google.generativeai as genai
    from decouple import config
    import json
    import re
    from datetime import datetime

    API_KEY = config("GOOGLE_GEMINI_API_KEY")
    genai.configure(api_key=API_KEY)
    model = genai.GenerativeModel("gemini-2.0-flash")

    today_str = datetime.now().date().strftime("%Y-%m-%d")

    prompt_text = f"""
You are an assistant specialized in extracting structured information from natural language.
Extract from the text:

1. The city mentioned, formatted exactly so it can be used as a query for api.weatherapi.com.
2. The date the user is referring to. 
   - If the user writes relative expressions like "tomorrow", "day after tomorrow", "in 3 days", compute the actual date based on today.
   - Today is {today_str}.
3. The hour (0-23) if specified; else null.

Return a JSON dictionary with exactly three keys:
{{
    "city": "<city_name_for_weatherapi>",
    "forecast_date": "<YYYY-MM-DD>",
    "hour": <0-23 or null>
}}

Text: "{question}"
"""

    try:
        # --- LLM call ---
        response = model.generate_content(prompt_text)
        result_text = response.text.strip()

        # --- Extract JSON ---
        match = re.search(r'{.*}', result_text, re.DOTALL)
        if match:
            result_dict = json.loads(match.group())
        else:
            result_dict = {"city": None, "forecast_date": None, "hour": None}

        # --- Defaults / fallback ---
        result_dict.setdefault("city", "Berlin")
        result_dict.setdefault("hour", None)

        # --- Calculate forecast_days ---
        today = datetime.now().date()
        target_date_str = result_dict.get("forecast_date")
        if target_date_str:
            target_date = datetime.strptime(target_date_str, "%Y-%m-%d").date()
            result_dict["forecast_days"] = (target_date - today).days + 1
        else:
            result_dict["forecast_days"] = 1  # fallback

        return result_dict

    except Exception as e:
        return {"city": "Berlin", "forecast_days": 1, "hour": None, "error": str(e)}
