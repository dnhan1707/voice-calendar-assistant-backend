from fastapi import APIRouter, HTTPException, Request
from app.services.chatbotService import chatbot
from app.services.calendarService import calendar
from app.models import ChatRequest
import json
import os


GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID")
GOOGLE_CLIENT_SECRET = os.getenv("GOOGLE_CLIENT_SECRET")
TOKEN_URI = "https://oauth2.googleapis.com/token"


router = APIRouter()


@router.post("/chatbot/")
async def talk_with_model(request: Request):
    body = await request.json()
    user_input = body["user_input"]
    access_token = body["access_token"]
    refresh_token = body["refresh_token"]
    result = await chatbot.get_response(user_input)
    print(result)
    try:
        result = json.loads(result)  # Ensure response is parsed as JSON
        print("Result after json: ", result)
    except json.JSONDecodeError:
        raise HTTPException(status_code=400, detail="Invalid response from chatbot")

    if result["query_type"] == "date":
        calendar_events =  await calendar.get_events_by_date(access_token, refresh_token, GOOGLE_CLIENT_ID, GOOGLE_CLIENT_SECRET, TOKEN_URI, result["date"])
        return await chatbot.discuss_about_calendar(calendar_events, user_input)
    elif result["query_type"] == "week":
        calendar_events = await calendar.get_events_by_week(access_token, refresh_token, GOOGLE_CLIENT_ID, GOOGLE_CLIENT_SECRET, TOKEN_URI, result["start_date"])
        return await chatbot.discuss_about_calendar(calendar_events, user_input)
    elif result["query_type"] == "range":
        calendar_events = await calendar.get_events_in_custom_range(access_token, refresh_token, GOOGLE_CLIENT_ID, GOOGLE_CLIENT_SECRET, TOKEN_URI, result["start_date"], result["end_date"])
        return await chatbot.discuss_about_calendar(calendar_events, user_input)
    elif result["query_type"] == "talk":
        return await chatbot.normal_discussion(user_input)
    else:
        return {"error": "Could not determine event query type"}

