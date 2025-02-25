from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
import datetime

class CalendarService:
    def __init__(self):
        pass

    async def get_event_test_connection(self, access_token: str):
        creds = Credentials(token=access_token)
        service = build("calendar", "v3", credentials=creds)
        now = datetime.datetime.utcnow().isoformat() + "Z"  # 'Z' indicates UTC time

        # Fetch events
        events_result = (
            service.events()
            .list(
                calendarId="primary",
                timeMin=now,
                maxResults=10,
                singleEvents=True,
                orderBy="startTime",
            )
            .execute()
        )
        return events_result.get("items", [])

calendar = CalendarService()