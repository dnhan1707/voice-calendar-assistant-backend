from fastapi import APIRouter, HTTPException
from app.services.chatbotService import chatbot
from app.services.calendarService import calendar
from app.models import ChatRequest
import json

router = APIRouter()

@router.post("/chatbot/")
async def talk_with_model(request: ChatRequest):
    user_input = request.user_input  # Extract user_input correctly
    access_token = request.access_token
    refresh_token = request.refresh_token
    result = await chatbot.get_response(user_input)
    print(result)
    try:
        result = json.loads(result)  # Ensure response is parsed as JSON
        print("Result after json: ", result)
    except json.JSONDecodeError:
        raise HTTPException(status_code=400, detail="Invalid response from chatbot")

    if result["query_type"] == "date":
        calendar_events = await calendar.get_events_by_date(
            access_token, refresh_token, result["date"]
        )
        return await chatbot.discuss_about_calendar(calendar_events, user_input)
    elif result["query_type"] == "week":
        calendar_events = await calendar.get_events_by_week(
            access_token, refresh_token, result["start_date"]
        )
        return await chatbot.discuss_about_calendar(calendar_events, user_input)
    elif result["query_type"] == "range":
        calendar_events = await calendar.get_events_in_custom_range(
            access_token, refresh_token, result["start_date"], result["end_date"]
        )
        return await chatbot.discuss_about_calendar(calendar_events, user_input)
    elif result["query_type"] == "talk":
        return await chatbot.normal_discussion(user_input)
    else:
        return {"error": "Could not determine event query type"}