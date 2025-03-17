from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from app.services.chatbotService import chatbot
import datetime

class CalendarService:
    def __init__(self):
        pass
    
    def _get_calendar_service(self, access_token, refresh_token, client_id, client_secret, token_uri):
        """Helper method to create credentials and return a calendar service."""
        creds = Credentials(
            token=access_token,
            refresh_token=refresh_token,
            token_uri=token_uri,
            client_id=client_id,
            client_secret=client_secret
        )
        return build("calendar", "v3", credentials=creds)
    
    def _format_datetime(self, date_str, time_str=None, add_days=0):
        """Helper method to format date/time strings properly."""
        date_obj = datetime.datetime.strptime(date_str, "%Y-%m-%d")
        
        # Add days if specified
        if add_days > 0:
            date_obj = date_obj + datetime.timedelta(days=add_days)
        
        if time_str:
            # If time is provided, combine date and time
            return f"{date_obj.strftime('%Y-%m-%d')}T{time_str}"
        else:
            # Just return the ISO format with Z
            return date_obj.isoformat() + "Z"
    
    def _extract_minimal_event_info(self, events):
        """Extract only essential event information to minimize tokens."""
        if not events:
            return []
        
        minimal_events = []
        for event in events:
            # Get start info in a consistent format
            start = event.get("start", {})
            if "dateTime" in start:
                # Format: "2025-03-15T10:00:00Z" -> "Mar 15, 10:00 AM"
                start_dt = datetime.datetime.fromisoformat(start["dateTime"].replace('Z', '+00:00'))
                start_str = start_dt.strftime("%b %d, %I:%M %p")
            else:
                # All-day event
                start_str = f"{start.get('date', 'unknown')} (all-day)"
                
            # Create minimal event object
            minimal_events.append({
                "id": event.get("id"),
                "title": event.get("summary", "Untitled"),
                "time": start_str,
                "location": event.get("location", "")[:30]  # Truncate long locations
            })
        
        return minimal_events
    
    def _normalize_time_format(self, time_str):
        """Normalize time format to ensure it has seconds and Z suffix if needed."""
        if not time_str:
            return None
            
        if not time_str.endswith('Z') and ':' in time_str:
            parts = time_str.split(':')
            if len(parts) == 2:  # Only HH:MM format
                time_str = f"{time_str}:00"
                
        return time_str

    # ============================Core Functions============================

    async def get_event_by_date(self, time_range=None, id_only=False, **auth_params):
        """Get events for a specific date."""
        print("Calling get event by date")

        service = self._get_calendar_service(**auth_params)
        if not time_range or 'date' not in time_range:
            return "Missing or invalid time_range"
        
        time_min = self._format_datetime(time_range['date'])
        time_max = self._format_datetime(time_range['date'], add_days=1)
        print(f"Time min: {time_min}")
        print(f"Time max: {time_max}")

        params = {
            "calendarId": "primary",
            "timeMin": time_min,
            "timeMax": time_max,
            "singleEvents": True,
            "orderBy": "startTime"
        }
        events_result = service.events().list(**params).execute()
        events = events_result.get("items", [])
        if id_only:
            return [event.get("id") for event in events if event.get("id")]
  
        minimal_events = self._extract_minimal_event_info(events)
        return await chatbot.create_meaningful_response(minimal_events)

    async def get_event_custom_range(self, time_range=None, id_only=False, **auth_params):
        """Get events within a custom date range."""
        print("Calling get event by range")
        print(f'Time range: {time_range}')
        service = self._get_calendar_service(**auth_params)
        if not time_range or 'start_date' not in time_range or 'end_date' not in time_range:
            return "Missing or invalid time_range"
        
        time_min = self._format_datetime(time_range['start_date'])
        time_max = self._format_datetime(time_range['end_date'])

        params = {
            "calendarId": "primary",
            "timeMin": time_min,
            "timeMax": time_max,
            "singleEvents": True,
            "orderBy": "startTime"
        }
        events_result = service.events().list(**params).execute()
        events = events_result.get("items", [])

        if id_only:
            return [event.get("id") for event in events if event.get("id")]
        
        minimal_events = self._extract_minimal_event_info(events)
        return await chatbot.create_meaningful_response(minimal_events)

    async def get_event_by_name(self, query=None, time_range=None, minimal=True, id_only=False, **auth_params):
        """Get events by name match."""
        print("Calling get event by name")
        
        service = self._get_calendar_service(**auth_params)
        events = []
        if query and time_range:
            # Find events with that query on that custom range
            if 'date' in time_range:
                events = await self.get_event_by_date(time_range=time_range, **auth_params)
            else:
                events = await self.get_event_custom_range(time_range=time_range, **auth_params)
            return await chatbot.find_best_event_match(events, query)['message']
        elif query:
            # Find any events match that query, max_result=10
            max_results = 10
            time_min = self._format_datetime(datetime.datetime.utcnow().strftime("%Y-%m-%d"))

            params = {
                "calendarId": "primary",
                "timeMin": time_min,
                "maxResults": max_results,
                "singleEvents": True,
                "orderBy": "startTime",
                "q": query
            }
            events_result = service.events().list(**params).execute()
            events = events_result.get("items", [])
            return await chatbot.find_best_event_match(events, query)['message']
        else:
            return "Missing query and time_range"
        


calendar = CalendarService()