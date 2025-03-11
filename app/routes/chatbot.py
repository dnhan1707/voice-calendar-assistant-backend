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
        result = json.loads(result)
        print("Result after json: ", result)
    except json.JSONDecodeError:
        raise HTTPException(status_code=400, detail="Invalid response from chatbot")

    # Common parameters for all calendar service calls
    common_params = {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "client_id": GOOGLE_CLIENT_ID,
        "client_secret": GOOGLE_CLIENT_SECRET,
        "token_uri": TOKEN_URI
    }

    query_type = result.get("query_type")
    
    if query_type == "date":
        calendar_events = await calendar.get_events_by_date(
            **common_params, date=result["date"])
        return await chatbot.discuss_about_calendar(calendar_events, user_input)
    
    elif query_type == "week":
        calendar_events = await calendar.get_events_by_week(
            **common_params, start_date=result["start_date"])
        return await chatbot.discuss_about_calendar(calendar_events, user_input)
    
    elif query_type == "range":
        calendar_events = await calendar.get_events_in_custom_range(
            **common_params, 
            start_date=result["start_date"], 
            end_date=result["end_date"])
        return await chatbot.discuss_about_calendar(calendar_events, user_input)
    
    elif query_type == "find":
        # Get events with minimal information
        events_data = await calendar.find_events_by_name_match(
            **common_params, 
            query=user_input
        )
        
        # Use GPT to find the best match
        match_result = await chatbot.find_best_event_match(events_data, user_input)
        print("Match result: ", match_result)
        # If a match was found, get the full event details
            # Optionally: Get full event details if needed
            # full_event = await calendar.get_event_by_id(**common_params, event_id=match_result["event"]["id"])
            # match_result["full_event"] = full_event
        info = {
            "success": True,
            "message": f"Found event: {match_result['event']['title']} at {match_result['event']['time']}",
            "event": match_result["event"],
            "explanation": match_result.get("explanation")
        }
        return await chatbot.create_meaningful_response(info)
    
    elif query_type == "create":
        # Validate required fields
        if not result.get("summary") or not result.get("start_date") or not result.get("end_date"):
            return {"error": "Missing required event information. Need at least summary, start_date, and end_date."}
        
        # For non-all-day events, ensure times are provided
        if not result.get("all_day") and (not result.get("start_time") or not result.get("end_time")):
            # Default to current time if not specified
            current_time = datetime.datetime.now().strftime("%H:%M")
            if not result.get("start_time"):
                result["start_time"] = current_time
            if not result.get("end_time"):
                # Default to 1 hour later if not specified
                result["end_time"] = (datetime.datetime.strptime(current_time, "%H:%M") + 
                                    datetime.timedelta(hours=1)).strftime("%H:%M")
        
        # Extract all the possible parameters for event creation
        create_params = {
            **common_params,
            "summary": result.get("summary"),
            "location": result.get("location"),
            "description": result.get("description"),
            "start_date": result.get("start_date"),
            "start_time": result.get("start_time"),
            "end_date": result.get("end_date"),
            "end_time": result.get("end_time"),
            "timezone": result.get("timezone", "UTC"),
            "all_day": result.get("all_day", False),
            "attendees": result.get("attendees")
        }
        
        # Remove None values
        create_params = {k: v for k, v in create_params.items() if v is not None}
        
        created_event = await calendar.create_event(**create_params)
        return f"Successfully created event: {result.get('summary')}",
        
    
    elif query_type == "talk":
        return await chatbot.normal_discussion(user_input)
    
    else:
        return {"error": "Could not determine event query type"}
    

@router.post("/chatbot/test_calendar/")
async def talk_with_model(request: Request):
    body = await request.json()
    user_input = body["user_input"]
    access_token = body["access_token"]
    refresh_token = body["refresh_token"]
    
    result = await chatbot.get_response(user_input)
    print(result)
    
    try:
        result = json.loads(result)
        print("Result after json: ", result)
    except json.JSONDecodeError:
        raise HTTPException(status_code=400, detail="Invalid response from chatbot")

    # Common parameters for all calendar service calls
    common_params = {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "client_id": GOOGLE_CLIENT_ID,
        "client_secret": GOOGLE_CLIENT_SECRET,
        "token_uri": TOKEN_URI
    }

    return await calendar.get_event_test_connection(**common_params)


# @router.post("/chatbot/find_event/")
# async def find_event_by_name(request: Request):
#     body = await request.json()
#     user_input = body["user_input"]
#     access_token = body["access_token"]
#     refresh_token = body["refresh_token"]
    
#     # Common parameters for all calendar service calls
#     common_params = {
#         "access_token": access_token,
#         "refresh_token": refresh_token,
#         "client_id": GOOGLE_CLIENT_ID,
#         "client_secret": GOOGLE_CLIENT_SECRET,
#         "token_uri": TOKEN_URI
#     }
    
#     # Get events with minimal information
#     events_data = await calendar.find_events_by_name_match(
#         **common_params, 
#         query=user_input
#     )
    
#     # Use GPT to find the best match
#     match_result = await chatbot.find_best_event_match(events_data, user_input)
#     print("Match result: ", match_result)
#     # If a match was found, get the full event details
#         # Optionally: Get full event details if needed
#         # full_event = await calendar.get_event_by_id(**common_params, event_id=match_result["event"]["id"])
#         # match_result["full_event"] = full_event
#     info = {
#         "success": True,
#         "message": f"Found event: {match_result['event']['title']} at {match_result['event']['time']}",
#         "event": match_result["event"],
#         "explanation": match_result.get("explanation")
#     }
#     return await chatbot.create_meaningful_response(info)