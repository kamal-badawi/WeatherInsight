def get_weather_llm_answer(question: str) -> dict:
    """
    Uses an LLM to generate a user-friendly weather forecast text.
    The output language matches the user's question language.
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
