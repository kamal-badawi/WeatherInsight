def get_city_and_forecast_days_for_weatherapi(question: str) -> dict:
    """
    Extract city, target date, and optional hour from the user question.
    Returns forecast_days as difference from today + 1 (so WeatherAPI includes the target day).
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
