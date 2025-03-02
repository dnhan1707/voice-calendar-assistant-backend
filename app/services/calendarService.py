from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
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
        if add_days:
            date_obj = date_obj + datetime.timedelta(days=add_days)
            
        if time_str:
            # If time is provided, combine date and time
            return f"{date_obj.strftime('%Y-%m-%d')}T{time_str}"
        else:
            # Just return the ISO format with Z
            return date_obj.isoformat() + "Z"

    async def get_event_test_connection(self, access_token, refresh_token, client_id, client_secret, token_uri):
        service = self._get_calendar_service(access_token, refresh_token, client_id, client_secret, token_uri)
        now = datetime.datetime.utcnow().isoformat() + "Z"

        events_result = service.events().list(
            calendarId="primary",
            timeMin=now,
            maxResults=10,
            singleEvents=True,
            orderBy="startTime"
        ).execute()
        
        return events_result.get("items", [])

    async def get_events_by_date(self, access_token, refresh_token, client_id, client_secret, token_uri, date):
        service = self._get_calendar_service(access_token, refresh_token, client_id, client_secret, token_uri)
        start_of_day = self._format_datetime(date)
        end_of_day = self._format_datetime(date, add_days=1)

        events_result = service.events().list(
            calendarId="primary",
            timeMin=start_of_day,
            timeMax=end_of_day,
            singleEvents=True,
            orderBy="startTime"
        ).execute()
        
        return events_result.get("items", [])

    async def get_events_by_week(self, access_token, refresh_token, client_id, client_secret, token_uri, start_date):
        service = self._get_calendar_service(access_token, refresh_token, client_id, client_secret, token_uri)
        start_of_week = self._format_datetime(start_date)
        end_of_week = self._format_datetime(start_date, add_days=7)

        events_result = service.events().list(
            calendarId="primary",
            timeMin=start_of_week,
            timeMax=end_of_week,
            singleEvents=True,
            orderBy="startTime"
        ).execute()
        
        return events_result.get("items", [])

    async def get_events_in_custom_range(self, access_token, refresh_token, client_id, client_secret, token_uri, 
                                         start_date, end_date):
        service = self._get_calendar_service(access_token, refresh_token, client_id, client_secret, token_uri)
        start_time = self._format_datetime(start_date)
        end_time = self._format_datetime(end_date)

        events_result = service.events().list(
            calendarId="primary",
            timeMin=start_time,
            timeMax=end_time,
            singleEvents=True,
            orderBy="startTime"
        ).execute()
        
        return events_result.get("items", [])
    
    async def create_event(self, access_token, refresh_token, client_id, client_secret, token_uri, 
                      summary, location=None, description=None, start_date=None, start_time=None,
                      end_date=None, end_time=None, timezone="UTC", all_day=False, 
                      recurrence_rule=None, attendees=None, reminders=None):
    
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
            # Correctly format datetime strings with timezone for Google Calendar API
            # Format should be: "2025-03-02T17:00:00-05:00" or "2025-03-02T17:00:00Z" for UTC
            if start_time and not start_time.endswith('Z') and ':' in start_time and len(start_time.split(':')) == 2:
                start_time = f"{start_time}:00"
            if end_time and not end_time.endswith('Z') and ':' in end_time and len(end_time.split(':')) == 2:
                end_time = f"{end_time}:00"
                
            start_datetime = f"{start_date}T{start_time}"
            end_datetime = f"{end_date}T{end_time}"
            
            # Ensure timezone information is included
            if not start_datetime.endswith('Z'):
                start_datetime = f"{start_datetime}Z"  # Default to UTC if no timezone
            if not end_datetime.endswith('Z'):
                end_datetime = f"{end_datetime}Z"  # Default to UTC if no timezone
                
            event['start'] = {'dateTime': start_datetime, 'timeZone': timezone}
            event['end'] = {'dateTime': end_datetime, 'timeZone': timezone}
        
        if recurrence_rule:
            event['recurrence'] = [f'RRULE:{recurrence_rule}']
        
        if attendees:
            event['attendees'] = [{'email': email} for email in attendees]
        
        event['reminders'] = reminders or {'useDefault': True}

        print(f"Creating event with data: {event}")  # Debug log
        
        created_event = service.events().insert(
            calendarId='primary',
            body=event,
            sendUpdates='all'
        ).execute()

        print(f"Event created: {created_event.get('htmlLink')}")
        return created_event
calendar = CalendarService()