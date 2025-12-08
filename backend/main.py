# 1. Imports
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Dict
from modules.llm_weather_answer import get_weather_llm_answer

# 2. FastAPI App instance and metadata
app = FastAPI(
    title="WeatherInsight",
    version="1.0.0",
    description=(
        """
**WeatherInsight** is a microservice that understands natural language questions from users
and provides weather forecasts for a specified city and date using WeatherAPI.

**Core Features:**\n
• ㅤㅤUnderstand user-friendly natural language questions about the weather\n
• ㅤㅤExtract city and forecast days automatically using LLM\n
• ㅤㅤRetrieve current weather and forecast data via WeatherAPI\n
• ㅤㅤGenerate a friendly, readable English text answer for the user\n
• ㅤㅤMicroservice-ready for integration into larger systems or chatbots\n
• ㅤㅤHandles absolute dates, relative dates, and natural expressions\n
• ㅤㅤRobust error handling for missing or invalid inputs\n
"""
    ),
    contact={
        "name": "Kamal Badawi",
        "email": "kamal.badawi@weatherinsight.com",
        "url": "https://www.weatherinsight.com/kamal-badawi"
    },
    license_info={
        "name": "MIT License",
        "url": "https://opensource.org/licenses/MIT"
    }
)

# 3. Middleware (CORS)
origins = [
    'http://localhost:5173', 'http://localhost:5174', 
    'http://localhost:4173', 'http://localhost:4174', 
    'http://localhost:4000', 'http://localhost:3000',
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=['*'],
    allow_headers=['*']
)

# 4. Pydantic models
class HandleQuestionRequest(BaseModel):
    """Data model for handling a user question."""
    question: str

# 5. Root endpoint
@app.get("/")
async def read_root():
    """
    Root Endpoint

    Checks if the API is up and running.

    Returns:
    - dict: A simple confirmation message.
    """
    return {"message": "FastAPI is up and running"}

# 6. Main endpoint to handle user questions
@app.post("/handle_question")
async def handle_question(request: HandleQuestionRequest) -> Dict:
    """
    Main endpoint to process a user question.

    Steps:
    1. Uses the LLM to extract city and forecast days from the question.
    2. Calls WeatherAPI to get weather forecast data.
    3. Uses the LLM to generate a friendly English text answer.
    """
    try:
        question = request.question

        # Generate a user-friendly English weather answer
        response = get_weather_llm_answer(question)
        answer = response.get("text")

        if not answer:
            answer = "Sorry, we could not generate a weather answer at this time."

        return {
            "answer": answer,
            "success": True
        }

    except HTTPException as he:
        raise he
    except Exception as e:
        print(f"Error in handle_question: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Internal server error: {str(e)}"
        )
