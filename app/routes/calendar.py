from fastapi import APIRouter, HTTPException
from app.services.calendarService import calendar
from app.models import ChatRequest

router = APIRouter()

@router.get("/calendar/")
async def get_events(access_token: str, refresh_token: str):
    events = await calendar.get_event_test_connection(access_token, refresh_token)
    return events

@router.post("/calendar/date")
async def get_events_by_date(request: ChatRequest):
    try:
        events = await calendar.get_events_by_date(
            request.access_token, request.refresh_token, request.date
        )
        return events
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/calendar/week")
async def get_events_by_week(request: ChatRequest):
    try:
        events = await calendar.get_events_by_week(
            request.access_token, request.refresh_token, request.start_date
        )
        return events
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/calendar/range")
async def get_events_in_custom_range(request: ChatRequest):
    try:
        events = await calendar.get_events_in_custom_range(
            request.access_token, request.refresh_token, request.start_date, request.end_date
        )
        return events
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))