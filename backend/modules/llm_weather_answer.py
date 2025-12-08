def get_weather_llm_answer(question: str) -> dict:
    """
    Generates a user-friendly, natural language weather forecast response using an LLM (Large Language Model)
    based on a user's question. The output language matches the detected language of the user's input.

    This function performs the following steps:
    1. Detects the language of the user's question using a language detection library.
       - If detection fails, defaults to English.
    2. Calls `get_weather_forecast` to retrieve structured weather data for the target city and date.
       - Includes hourly forecasts within a configurable time window around the requested hour.
       - Handles fallback cases if the city, date, or hour are missing.
    3. Prompts the Gemini LLM to convert the structured weather data into a short, clear, and natural text
       response that is readable and user-friendly.
    4. Returns the generated text.

    Features:
    ---------
    - Automatically summarizes current weather, daily forecast, and optionally hourly details.
    - Adjusts the description to focus on a time window from `hours_before` hours before to `hours_after` hours
      after the requested hour.
    - Produces text in the same language as the user's question for better user experience.
    - Handles errors gracefully, providing fallback messages if the LLM or API fails.

    Parameters:
    -----------
    question : str
        A natural language question or statement from the user that includes information about the desired
        city, date, and optionally the hour for which weather information is requested.

    Returns:
    --------
    dict
        A dictionary with a single key:
        - "text": A human-readable weather forecast string. Example:
          "Hello! The weather in Cologne on 2025-11-22 will be partly cloudy with temperatures between 4°C and 12°C.
           Around 22:00, it will be clear with 6°C."

    Notes:
    ------
    - The function uses the `get_weather_forecast` function internally to retrieve structured weather data.
    - The LLM prompt ensures that no JSON, code, or structured data is returned—only natural language text.
    - The hourly forecast is included only if requested and within the defined time window.
    - If the weather data cannot be retrieved, a default error message is returned.
    """
    import google.generativeai as genai
    from decouple import config
    from modules.weatherapi_forecast_data import get_weather_forecast
    from langdetect import detect

    # --- Detect language of the user's question ---
    try:
        user_language = detect(question)
    except:
        user_language = "en"  # fallback to English

    # --- Get weather data (including hourly forecast) ---
    hours_before = 2
    hours_after = 3
    weather_data = get_weather_forecast(
        question, include_hours=True, hours_before=hours_before, hours_after=hours_after
    )
    print("weather_data:", weather_data)  # Debugging

    if not weather_data or "error" in weather_data:
        return {"text": "Sorry, the weather data could not be retrieved."}

    # --- Prepare prompt for Gemini LLM ---
    prompt_text = f"""
You are a friendly AI assistant. Using the following weather data,
create a short, clear, and user-friendly text for the user.

Weather data: {weather_data}

Guidelines:
- Respond in the language of the user's question (detected language: {user_language}).
- Summarize the most important information: current weather, temperature, and forecast.
- Focus the description on the time window from {hours_before} hours before to {hours_after} hours after the requested hour.
- Make the text friendly, readable, and natural.
- Do not return JSON, code, or structured data — only plain text.
"""

    # --- Configure Gemini API ---
    API_KEY = config("GOOGLE_GEMINI_API_KEY")
    genai.configure(api_key=API_KEY)
    model = genai.GenerativeModel("gemini-2.0-flash")

    try:
        # --- Call the LLM ---
        response = model.generate_content(prompt_text)
        result_text = response.text.strip()

        return {"text": result_text}

    except Exception as e:
        return {"text": f"Error generating the answer: {str(e)}"}
