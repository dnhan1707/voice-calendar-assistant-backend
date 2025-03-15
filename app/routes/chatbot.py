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

        query_type = result.get("query_type")
        
        # Handle different types of calendar queries
        if query_type == "date":
            # Get events for a specific date
            calendar_events = await calendar.get_events(
                **common_params, 
                time_range={"start": result["date"], "end": result["date"]},
                max_results=20
            )
            return await chatbot.discuss_about_calendar(calendar_events, user_input)
        
        elif query_type == "week":
            # Get events for a week
            calendar_events = await calendar.get_events(
                **common_params, 
                time_range={"start": result["start_date"]},
                max_results=50
            )
            return await chatbot.discuss_about_calendar(calendar_events, user_input)
        
        elif query_type == "range":
            # Get events for a custom date range
            calendar_events = await calendar.get_events(
                **common_params, 
                time_range={"start": result["start_date"], "end": result["end_date"]},
                max_results=50
            )
            return await chatbot.discuss_about_calendar(calendar_events, user_input)
        
        elif query_type == "find":
            # Find events matching a name/description
            events_data = await calendar.get_events(
                **common_params, 
                query=user_input,
                max_results=20,
                minimal=True
            )
            
            # Let GPT find the best matching event
            match_result = await chatbot.find_best_event_match(events_data, user_input)
            print("Match result: ", match_result)

            info = {
                "success": match_result.get("found", False),
                "message": (f"Found event: {match_result['event']['title']} at {match_result['event']['time']}" 
                          if match_result.get("found", False) else match_result.get("message", "No matching events found")),
                "event": match_result.get("event"),
                "explanation": match_result.get("explanation")
            }
            return await chatbot.create_meaningful_response(info)
        
        elif query_type == "delete":
            # Handle event deletion - determine if we're deleting by name or date
            if result.get("event_name"):
                # Delete by name/search term
                delete_result = await calendar.delete_events(
                    **common_params,
                    query=result.get("event_name")
                )
            elif result.get("date"):
                # Delete events on a specific date
                delete_result = await calendar.delete_events(
                    **common_params,
                    time_range={"start": result.get("date"), "end": result.get("date")}
                )
            else:
                return {"error": "Missing criteria for deletion. Need event_name or date."}
                
            # Format the response for the user
            if delete_result.get("success"):
                message = delete_result.get("message", f"Successfully deleted {delete_result.get('deleted_count', 0)} events")
                return {"success": True, "message": message, "details": delete_result.get("details", [])}
            else:
                return {"success": False, "message": delete_result.get("message", "Failed to delete events")}
        
        elif query_type == "talk":
            # Handle general conversation
            return await chatbot.normal_discussion(user_input)
        
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