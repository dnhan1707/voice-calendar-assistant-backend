from fastapi import APIRouter, HTTPException, Request
from app.services.chatbotService import chatbot
from app.services.calendarService import calendar

import json
import os
import datetime

GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID")
GOOGLE_CLIENT_SECRET = os.getenv("GOOGLE_CLIENT_SECRET")
TOKEN_URI = "https://oauth2.googleapis.com/token"

router = APIRouter()

@router.post("/chatbot/")
async def talk_with_model(request: Request):
    try:
        body = await request.json()
        user_input = body["user_input"]
        access_token = body["access_token"]
        refresh_token = body["refresh_token"]
        
        result = await chatbot.get_response(user_input)
        
        try:
            # Clean up the GPT response - it might be wrapped in Markdown code blocks
            result_str = result.strip()
            
            # Check if the result is wrapped in markdown code blocks ```json ... ```
            if result_str.startswith("```") and "```" in result_str[3:]:
                # Extract just the JSON part
                json_start = result_str.find("\n", 3) + 1 if result_str.find("\n", 3) > 0 else 3
                json_end = result_str.rfind("```")
                result_str = result_str[json_start:json_end].strip()
            
            print(f"Cleaned JSON string: {result_str}")
            result = json.loads(result_str)
            print("Result after json: ", result)
        except json.JSONDecodeError:
            print(f"JSON decode error: {e}")
            print(f"Failed to parse: '{result_str}'")
            raise HTTPException(status_code=400, detail="Invalid response from chatbot")
        
        # Common parameters for all calendar service calls
        common_params = {
            "access_token": access_token,
            "refresh_token": refresh_token,
            "client_id": GOOGLE_CLIENT_ID,
            "client_secret": GOOGLE_CLIENT_SECRET,
            "token_uri": TOKEN_URI
        }

        endpoint = result.get("endpoint")
        query_type = result.get("query-type")

        print(f'Endpoint: {endpoint}')
        print(f'Query: {query_type}')

        # Handle different types of calendar queries
        if endpoint == "get":
            # Get events for a specific date
            if(query_type == 'date'):
                calendar_events = await calendar.get_event_by_date(
                    **common_params, 
                    time_range={"date": result["date"]},
                )
                return calendar_events
            elif(query_type == 'custom'):
                calendar_events = await calendar.get_event_custom_range(
                    **common_params, 
                    time_range={"start_date": result["start_date"], "end_date": result["end_date"]},
                )
                return calendar_events
            else:
                return "Unknown Query Type"
        else:
            return {"error": "Could not determine event query type"}
    
    except Exception as e:
        print(f"Error processing request: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error processing request: {str(e)}")


@router.post("/chatbot/test_calendar/")
async def test_calendar_connection(request: Request):
    """Test the calendar connection by retrieving a few upcoming events."""
    try:
        body = await request.json()
        access_token = body["access_token"]
        refresh_token = body["refresh_token"]
        
        # Common parameters for calendar service
        common_params = {
            "access_token": access_token,
            "refresh_token": refresh_token,
            "client_id": GOOGLE_CLIENT_ID,
            "client_secret": GOOGLE_CLIENT_SECRET,
            "token_uri": TOKEN_URI
        }

        # Use the unified get_events method directly
        return await calendar.get_events(
            **common_params,
            max_results=5
        )
    except Exception as e:
        print(f"Error testing calendar: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error connecting to calendar: {str(e)}")