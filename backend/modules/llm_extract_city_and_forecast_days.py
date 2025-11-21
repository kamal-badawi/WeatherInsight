def get_city_and_forecast_days_for_weatherapi(question: str) -> dict:
    """
    Extracts the city, number of forecast days, and optionally the hour from a user question.
    The city is formatted so it can be used directly with api.weatherapi.com.
    Forecast days and hour are extracted automatically from absolute or relative dates and times.

    Returns:
        dict: {"city": <city_name>, "forecast_days": <number_of_days>, "hour": <0-23 or None>}
    """
    import google.generativeai as genai
    from decouple import config
    import json
    import re
    from datetime import datetime, timedelta

    # --- Configure API Key ---
    API_KEY = config("GOOGLE_GEMINI_API_KEY")
    genai.configure(api_key=API_KEY)
    model = genai.GenerativeModel("gemini-2.0-flash")

    # --- Prompt for structured extraction (escaped {{}} for f-string) ---
    prompt_text = f"""
You are an assistant specialized in extracting structured information from natural language.
Your task is to extract from the following text:

1. The city mentioned, formatted exactly so it can be used as a query for api.weatherapi.com.
   - Remove any unnecessary words or punctuation.
   - Use the standard English name if applicable (e.g., "München" → "Munich").
2. The number of forecast days (as an integer) until the date the user refers to.
   - The user may write absolute dates (like 23.11.2025), relative dates ("tomorrow", "in 3 days", "overmorgen") or other natural expressions.
3. The hour (0-23) if the user mentions a specific time.
   - If no hour is mentioned, return null.

Always return a JSON dictionary with exactly three keys:
{{
    "city": "<city_name_for_weatherapi>",
    "forecast_days": <number_of_days>,
    "hour": <0-23 or null>
}}

If a value cannot be determined, use null.

Text: "{question}"
"""

    try:
        # --- Call Gemini LLM ---
        response = model.generate_content(prompt_text)
        result_text = response.text.strip()

        # --- Debug log ---
        print("LLM raw response:", result_text)

        # --- Extract JSON using regex ---
        match = re.search(r'{.*}', result_text, re.DOTALL)
        if match:
            try:
                result_dict = json.loads(match.group())
            except json.JSONDecodeError:
                result_dict = {"city": None, "forecast_days": None, "hour": None}
        else:
            result_dict = {"city": None, "forecast_days": None, "hour": None}

        # --- Ensure all keys exist ---
        result_dict.setdefault("city", None)
        result_dict.setdefault("forecast_days", None)
        result_dict.setdefault("hour", None)

        # --- Fallback defaults ---
        if not result_dict["city"]:
            print("City extraction failed. Using default 'Berlin'.")
            result_dict["city"] = "Berlin"
        if not result_dict["forecast_days"]:
            print("Forecast days extraction failed. Using default 1 day.")
            result_dict["forecast_days"] = 1

        return result_dict

    except Exception as e:
        print(f"Error in get_city_and_forecast_days_for_weatherapi: {str(e)}")
        return {"city": "Berlin", "forecast_days": 1, "hour": None, "error": str(e)}
