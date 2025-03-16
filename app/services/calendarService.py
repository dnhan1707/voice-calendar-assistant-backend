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
        
        print(f"Original date: {date_obj.isoformat()}")
        
        # Add days if specified
        if add_days > 0:
            date_obj = date_obj + datetime.timedelta(days=add_days)
            print(f"After adding {add_days} days: {date_obj.isoformat()}")
            
        result = date_obj.isoformat() + "Z" if not time_str else f"{date_obj.strftime('%Y-%m-%d')}T{time_str}"
        print(f"Final formatted datetime: {result}")
        
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
    
    # ===== CORE CALENDAR OPERATIONS =====
    
    async def get_events(self, time_range=None, query=None, max_results=10, id_only=False, minimal=False, **auth_params, ):
        """
        Core method for getting events with various filtering options.
        
        Args:
            **auth_params: Authentication parameters (access_token, refresh_token, etc.)
            time_range: Either a predefined range ('day', 'week', 'month', 'test') or a dict with 'start' and optional 'end'
            query: Optional search query
            max_results: Maximum results to return
            id_only: If True, return only event IDs
            minimal: If True, return minimal event info for GPT
            
        Returns:
            List of events or event IDs depending on options
        """
        service = self._get_calendar_service(**auth_params)
        
        # Set up time parameters
        now = datetime.datetime.utcnow()
        time_min = now.isoformat() + "Z"
        time_max = None
        
        # Handle different time range options
        if time_range:
            if isinstance(time_range, dict):
                # Custom range with explicit dates
                if 'date' in time_range:
                    # Single day with 'date' key
                    print("IN DATE")
                    time_min = self._format_datetime(time_range['date'])
                    time_max = self._format_datetime(time_range['date'], add_days=1)
                elif 'start' in time_range and 'end' in time_range:
                    # Custom range with start and end
                    start_date = time_range['start']
                    end_date = time_range['end']
                    
                    # Check if this is actually a single-day query (start == end)
                    if start_date == end_date:
                        print("Single day query detected with start=end")
                        time_min = self._format_datetime(start_date)
                        time_max = self._format_datetime(start_date, add_days=1)
                    else:
                        time_min = self._format_datetime(start_date)
                        time_max = self._format_datetime(end_date)
                elif 'start' in time_range:
                    time_min = self._format_datetime(time_range['start'])
                    if 'end' in time_range:
                        time_max = self._format_datetime(time_range['end'])
            else:
                # Simple string presets
                if time_range == 'test':
                    # Just use default (now to unspecified future)
                    pass
                elif time_range == 'future':
                    # Next 30 days
                    time_max = (now + datetime.timedelta(days=30)).isoformat() + "Z"
                elif time_range == 'today':
                    # Just today
                    today = now.strftime("%Y-%m-%d")
                    time_min = self._format_datetime(today)
                    time_max = self._format_datetime(today, add_days=1)
                elif time_range == 'tomorrow':
                    # Just tomorrow
                    tomorrow = (now + datetime.timedelta(days=1)).strftime("%Y-%m-%d")
                    time_min = self._format_datetime(tomorrow)
                    time_max = self._format_datetime(tomorrow, add_days=1)
                elif time_range == 'this_week':
                    # This week
                    today = now.strftime("%Y-%m-%d")
                    time_min = self._format_datetime(today)
                    time_max = self._format_datetime(today, add_days=7)

        # Build params dictionary
        params = {
            "calendarId": "primary",
            "timeMin": time_min,
            "maxResults": max_results,
            "singleEvents": True,
            "orderBy": "startTime"
        }
        
        if time_max:
            params["timeMax"] = time_max
            
        if query:
            params["q"] = query
        
        print(f'Params for calendaar: ', params)

        # Get events
        events_result = service.events().list(**params).execute()
        events = events_result.get("items", [])
        print(f'Found events: ', events)
        # Format the response based on options
        if id_only:
            return [event.get("id") for event in events if event.get("id")]
        elif minimal:
            minimal_events = self._extract_minimal_event_info(events)
            return {
                "original_query": query,
                "events": minimal_events
            }
        else:
            return events
    
    async def get_event_by_id(self, event_id, **auth_params):
        """Get a specific event by ID."""
        service = self._get_calendar_service(**auth_params)
        try:
            return service.events().get(calendarId="primary", eventId=event_id).execute()
        except Exception as e:
            print(f"Error getting event by ID: {e}")
            return None
    
    async def delete_events(self, time_range=None, query=None, **auth_params):
        """
        Unified method to delete events by various criteria.
        
        Args:
            event_ids: List of event IDs to delete
            time_range: Time range to delete events from (see get_events for format)
            query: Query string to match events to delete
            **auth_params: Authentication parameters
            
        Returns:
            Results of the delete operation
        """
        service = self._get_calendar_service(**auth_params)
        event_ids = await self.find_events_by_name_match(query=query, id_only=True, **auth_params)
        # Get IDs of events to delete if not directly provided
        if not event_ids:
            if time_range or query:
                event_ids = await self.get_events(
                    **auth_params,
                    time_range=time_range,
                    query=query,
                    id_only=True
                )
            else:
                return {"success": False, "message": "No criteria provided for deletion"}
        
        if not event_ids:
            return {"success": False, "message": "No matching events found to delete"}
        
        # Delete the events
        results = {
            "success": True,
            "deleted_count": 0,
            "failed_count": 0,
            "details": []
        }
        
        for event_id in event_ids:
            try:
                # Try regular delete first
                service.events().delete(calendarId='primary', eventId=event_id).execute()
                results["deleted_count"] += 1
                results["details"].append({"id": event_id, "status": "deleted"})
                
            except Exception as e:
                # If regular delete fails, try handling as recurring event
                try:
                    event = service.events().get(calendarId='primary', eventId=event_id).execute()
                    event['status'] = 'cancelled'
                    service.events().update(calendarId='primary', eventId=event_id, body=event).execute()
                    results["deleted_count"] += 1
                    results["details"].append({"id": event_id, "status": "cancelled (recurring)"})
                    
                except Exception as nested_e:
                    results["failed_count"] += 1
                    results["details"].append({
                        "id": event_id, 
                        "status": "failed", 
                        "error": str(nested_e)
                    })
        
        # Set overall success based on results
        if results["failed_count"] > 0:
            if results["deleted_count"] == 0:
                results["success"] = False
                results["message"] = "Failed to delete any events"
            else:
                results["message"] = f"Deleted {results['deleted_count']} events, {results['failed_count']} failed"
        else:
            results["message"] = f"Successfully deleted {results['deleted_count']} events"
        
        return results
    
    # ===== BACKWARD COMPATIBILITY METHODS =====
    
    # These methods maintain the same interface but delegate to the core methods
    
    # GET
    async def get_event_test_connection(self, **auth_params):
        """Test connection by getting a few upcoming events."""
        return await self.get_events(**auth_params, time_range="test")

    async def get_events_by_date(self, date, **auth_params):
        """Get events for a specific date."""
        return await self.get_events(**auth_params, time_range={"start": date, "end": self._format_datetime(date, add_days=1)})

    async def get_events_by_week(self, start_date, **auth_params):
        """Get events for a week starting from the given date."""
        return await self.get_events(**auth_params, time_range={"start": start_date, "end": self._format_datetime(start_date, add_days=7)})

    async def get_events_in_custom_range(self, start_date, end_date, **auth_params):
        """Get events within a custom date range."""
        return await self.get_events(**auth_params, time_range={"start": start_date, "end": end_date})
    
    async def get_event_by_name(self, name, max_results=10, time_min=None, exact_match=False, **auth_params):
        """Search for events by name/summary."""
        time_range = {"start": time_min} if time_min else None
        events = await self.get_events(**auth_params, time_range=time_range, query=name, max_results=max_results)
        
        # Filter for exact matches if requested
        if exact_match and events:
            events = [event for event in events if event.get("summary", "").lower() == name.lower()]
        
        return events
    
    # FIND (extra GET)
    async def find_events_by_name_match(self, query, max_results=20, id_only=False, **auth_params): 
        """Get events and return minimal info to use with GPT for matching."""
        if id_only:
            return await self.get_events(**auth_params, query=query, max_results=max_results, id_only=True)
        else:
            return await self.get_events(**auth_params, query=query, max_results=max_results, minimal=True)

    async def find_event_id(self, query=None, max_results=20, **auth_params):
        """Find event IDs matching the query or all upcoming events."""
        return await self.get_events(**auth_params, query=query, max_results=max_results, id_only=True)
    
    # DELETE
    async def delete_event_by_name(self, query, **auth_params):
        """Delete events matching a query."""
        return await self.delete_events(query=query, **auth_params)
    
    async def delete_event_by_id(self, service, id_list):
        """Legacy method - delegates to delete_events."""
        # This is a bit special as it takes a service directly
        # We'll adapt by extracting auth params and passing event_ids
        results = {
            "success": True,
            "deleted_count": 0,
            "failed_count": 0,
            "details": []
        }
        
        for event_id in id_list:
            try:
                # Try regular delete first
                service.events().delete(calendarId='primary', eventId=event_id).execute()
                results["deleted_count"] += 1
                results["details"].append({"id": event_id, "status": "deleted"})
                
            except Exception as e:
                # If regular delete fails, try handling as recurring event
                try:
                    event = service.events().get(calendarId='primary', eventId=event_id).execute()
                    event['status'] = 'cancelled'
                    service.events().update(calendarId='primary', eventId=event_id, body=event).execute()
                    results["deleted_count"] += 1
                    results["details"].append({"id": event_id, "status": "cancelled (recurring)"})
                    
                except Exception as nested_e:
                    results["failed_count"] += 1
                    results["details"].append({
                        "id": event_id, 
                        "status": "failed", 
                        "error": str(nested_e)
                    })
        
        # Set overall success based on results
        if results["failed_count"] > 0:
            if results["deleted_count"] == 0:
                results["success"] = False
                results["message"] = "Failed to delete any events"
            else:
                results["message"] = f"Deleted {results['deleted_count']} events, {results['failed_count']} failed"
        else:
            results["message"] = f"Successfully deleted {results['deleted_count']} events"
        
        return results

    async def delete_event_by_date(self, date, **auth_params):
        """Delete events on a specific date."""
        return await self.delete_events(time_range={"start": date, "end": self._format_datetime(date, add_days=1)}, **auth_params)

calendar = CalendarService()