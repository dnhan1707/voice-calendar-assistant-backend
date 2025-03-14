from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
import datetime
from typing import List, Dict, Any, Optional, Union

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
        if add_days:
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
    
    async def _get_events(self, 
                         service, 
                         time_min=None, 
                         time_max=None, 
                         max_results=10, 
                         q=None,
                         calendar_id="primary"):
        """Core method to get events with various filters."""
        # Default to current time if not specified
        if time_min is None:
            time_min = datetime.datetime.utcnow().isoformat() + "Z"
            
        # Build params dictionary, excluding None values
        params = {
            "calendarId": calendar_id,
            "timeMin": time_min,
            "maxResults": max_results,
            "singleEvents": True,
            "orderBy": "startTime"
        }
        
        if time_max:
            params["timeMax"] = time_max
            
        if q:
            params["q"] = q
            
        events_result = service.events().list(**params).execute()
        return events_result.get("items", [])

    # ===== PUBLIC API METHODS =====
    
    async def get_event_test_connection(self, access_token, refresh_token, client_id, client_secret, token_uri):
        """Test connection by getting a few upcoming events."""
        service = self._get_calendar_service(access_token, refresh_token, client_id, client_secret, token_uri)
        return await self._get_events(service)

    async def get_events_by_date(self, access_token, refresh_token, client_id, client_secret, token_uri, date):
        """Get events for a specific date."""
        service = self._get_calendar_service(access_token, refresh_token, client_id, client_secret, token_uri)
        start_of_day = self._format_datetime(date)
        end_of_day = self._format_datetime(date, add_days=1)
        return await self._get_events(service, time_min=start_of_day, time_max=end_of_day)

    async def get_events_by_week(self, access_token, refresh_token, client_id, client_secret, token_uri, start_date):
        """Get events for a week starting from the given date."""
        service = self._get_calendar_service(access_token, refresh_token, client_id, client_secret, token_uri)
        start_of_week = self._format_datetime(start_date)
        end_of_week = self._format_datetime(start_date, add_days=7)
        return await self._get_events(service, time_min=start_of_week, time_max=end_of_week)

    async def get_events_in_custom_range(self, access_token, refresh_token, client_id, client_secret, token_uri, 
                                         start_date, end_date):
        """Get events within a custom date range."""
        service = self._get_calendar_service(access_token, refresh_token, client_id, client_secret, token_uri)
        start_time = self._format_datetime(start_date)
        end_time = self._format_datetime(end_date)
        return await self._get_events(service, time_min=start_time, time_max=end_time)
    
    async def get_event_by_name(self, access_token, refresh_token, client_id, client_secret, token_uri, 
                               name, max_results=10, time_min=None, exact_match=False):
        """Search for events by name/summary."""
        service = self._get_calendar_service(access_token, refresh_token, client_id, client_secret, token_uri)
        items = await self._get_events(service, time_min=time_min, max_results=max_results, q=name)
        
        # Filter for exact matches if requested
        if exact_match and items:
            items = [event for event in items if event.get("summary", "").lower() == name.lower()]
        
        return items
    
    async def find_events_by_name_match(self, access_token, refresh_token, client_id, client_secret, token_uri, 
                                      query, max_results=20):
        """Get events and return minimal info to use with GPT for matching."""
        service = self._get_calendar_service(access_token, refresh_token, client_id, client_secret, token_uri)
        
        # Look at upcoming events (next 30 days)
        now = datetime.datetime.utcnow()
        time_min = now.isoformat() + "Z"
        time_max = (now + datetime.timedelta(days=30)).isoformat() + "Z"
        
        # Get calendar events
        events = await self._get_events(
            service, 
            time_min=time_min, 
            time_max=time_max, 
            max_results=max_results
        )
        
        # Extract minimal info for each event
        minimal_events = self._extract_minimal_event_info(events)
        
        return {
            "original_query": query,
            "events": minimal_events
        }

    async def find_event_id(self, access_token, refresh_token, client_id, client_secret, token_uri, 
                          query=None, max_results=20):
        """Find event IDs matching the query or all upcoming events."""
        service = self._get_calendar_service(access_token, refresh_token, client_id, client_secret, token_uri)
        
        # Look at upcoming events (next 30 days)
        now = datetime.datetime.utcnow()
        time_min = now.isoformat() + "Z"
        time_max = (now + datetime.timedelta(days=30)).isoformat() + "Z"
        
        # Get calendar events
        events = await self._get_events(
            service, 
            time_min=time_min, 
            time_max=time_max, 
            max_results=max_results,
            q=query
        )
        
        # Extract just the IDs
        return [event.get("id") for event in events if event.get("id")]
    
    async def get_event_by_id(self, access_token, refresh_token, client_id, client_secret, token_uri, event_id):
        """Get a specific event by ID."""
        service = self._get_calendar_service(access_token, refresh_token, client_id, client_secret, token_uri)
        try:
            return service.events().get(calendarId="primary", eventId=event_id).execute()
        except Exception as e:
            print(f"Error getting event by ID: {e}")
            return None
    
    async def create_event(self, access_token, refresh_token, client_id, client_secret, token_uri, 
                         summary, location=None, description=None, start_date=None, start_time=None,
                         end_date=None, end_time=None, timezone="UTC", all_day=False, 
                         recurrence_rule=None, attendees=None, reminders=None):
        """Create a new calendar event."""
        service = self._get_calendar_service(access_token, refresh_token, client_id, client_secret, token_uri)
        
        # Create event dictionary
        event = {'summary': summary}
        
        # Handle optional fields
        if location:
            event['location'] = location
        if description:
            event['description'] = description
            
        # Handle date/time
        if all_day:
            event['start'] = {'date': start_date}
            event['end'] = {'date': end_date}
        else:
            # Format time strings
            start_time = self._normalize_time_format(start_time)
            end_time = self._normalize_time_format(end_time)
                
            start_datetime = f"{start_date}T{start_time}"
            end_datetime = f"{end_date}T{end_time}"
            
            # Ensure timezone information is included
            if not start_datetime.endswith('Z'):
                start_datetime = f"{start_datetime}Z"
            if not end_datetime.endswith('Z'):
                end_datetime = f"{end_datetime}Z"
                
            event['start'] = {'dateTime': start_datetime, 'timeZone': timezone}
            event['end'] = {'dateTime': end_datetime, 'timeZone': timezone}
        
        # Handle additional options
        if recurrence_rule:
            event['recurrence'] = [f'RRULE:{recurrence_rule}']
        
        if attendees:
            event['attendees'] = [{'email': email} for email in attendees]
        
        event['reminders'] = reminders or {'useDefault': True}
        
        # Create the event
        created_event = service.events().insert(
            calendarId='primary',
            body=event,
            sendUpdates='all'
        ).execute()

        print(f"Event created: {created_event.get('htmlLink')}")
        return created_event
    
    async def delete_event(self, access_token, refresh_token, client_id, client_secret, token_uri, event_id):
        """Delete an event by ID."""
        service = self._get_calendar_service(access_token, refresh_token, client_id, client_secret, token_uri)
        try:
            # Try simple delete first
            service.events().delete(calendarId='primary', eventId=event_id).execute()
            return {"success": True, "message": "Event deleted successfully"}
        except Exception as e:
            try:
                # If simple delete fails, try handling it as a recurring event
                event = service.events().get(calendarId='primary', eventId=event_id).execute()
                event['status'] = 'cancelled'
                service.events().update(calendarId='primary', eventId=event_id, body=event).execute()
                return {"success": True, "message": "Recurring event cancelled successfully"}
            except Exception as nested_e:
                return {"success": False, "message": f"Failed to delete event: {str(nested_e)}"}
    
    async def update_event(self, access_token, refresh_token, client_id, client_secret, token_uri, 
                         event_id, summary=None, location=None, description=None, 
                         start_date=None, start_time=None, end_date=None, end_time=None, 
                         timezone=None, all_day=None, attendees=None):
        """Update an existing event."""
        service = self._get_calendar_service(access_token, refresh_token, client_id, client_secret, token_uri)
        
        try:
            # Get the existing event
            event = service.events().get(calendarId='primary', eventId=event_id).execute()
            
            # Update fields if provided
            if summary:
                event['summary'] = summary
            if location:
                event['location'] = location
            if description:
                event['description'] = description
                
            # Handle date/time updates
            if all_day is not None:
                if all_day:
                    # Convert to all-day event
                    event['start'] = {'date': start_date or event['start'].get('date')}
                    event['end'] = {'date': end_date or event['end'].get('date')}
                elif start_date and end_date:
                    # Convert to timed event
                    start_time = self._normalize_time_format(start_time or '00:00:00')
                    end_time = self._normalize_time_format(end_time or '23:59:59')
                    
                    start_datetime = f"{start_date}T{start_time}"
                    end_datetime = f"{end_date}T{end_time}"
                    
                    if not start_datetime.endswith('Z'):
                        start_datetime = f"{start_datetime}Z"
                    if not end_datetime.endswith('Z'):
                        end_datetime = f"{end_datetime}Z"
                        
                    event['start'] = {'dateTime': start_datetime, 'timeZone': timezone or 'UTC'}
                    event['end'] = {'dateTime': end_datetime, 'timeZone': timezone or 'UTC'}
            else:
                # Just update the times without changing event type
                if 'date' in event['start'] and (start_date or end_date):
                    # All-day event - just update dates
                    if start_date:
                        event['start']['date'] = start_date
                    if end_date:
                        event['end']['date'] = end_date
                elif 'dateTime' in event['start'] and (start_date or start_time or end_date or end_time):
                    # Timed event - format datetime strings
                    if start_date or start_time:
                        curr_start = event['start']['dateTime'].replace('Z', '')
                        curr_start_date, curr_start_time = curr_start.split('T')
                        new_start_date = start_date or curr_start_date
                        new_start_time = self._normalize_time_format(start_time or curr_start_time)
                        event['start']['dateTime'] = f"{new_start_date}T{new_start_time}Z"
                        
                    if end_date or end_time:
                        curr_end = event['end']['dateTime'].replace('Z', '')
                        curr_end_date, curr_end_time = curr_end.split('T')
                        new_end_date = end_date or curr_end_date
                        new_end_time = self._normalize_time_format(end_time or curr_end_time)
                        event['end']['dateTime'] = f"{new_end_date}T{new_end_time}Z"
            
            # Update timezone if provided
            if timezone:
                if 'timeZone' in event['start']:
                    event['start']['timeZone'] = timezone
                if 'timeZone' in event['end']:
                    event['end']['timeZone'] = timezone
            
            # Update attendees if provided
            if attendees:
                event['attendees'] = [{'email': email} for email in attendees]
            
            updated_event = service.events().update(
                calendarId='primary',
                eventId=event_id,
                body=event,
                sendUpdates='all'
            ).execute()
            
            return updated_event
            
        except Exception as e:
            print(f"Error updating event: {e}")
            return {"error": str(e)}

calendar = CalendarService()