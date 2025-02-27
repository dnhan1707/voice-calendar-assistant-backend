from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
import datetime
import os
from dotenv import load_dotenv

load_dotenv()


class CalendarService:
    def __init__(self):
        pass

    async def get_event_test_connection(self, access_token: str, refresh_token: str):
        creds = Credentials(
            token=access_token,
            refresh_token=refresh_token,
            token_uri="https://oauth2.googleapis.com/token",
            client_id=os.getenv("GOOGLE_CLIENT_ID"),
            client_secret=os.getenv("GOOGLE_CLIENT_SECRET")
        )
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

    async def get_events_by_date(self, access_token: str, refresh_token: str, date: str):
        creds = Credentials(
            token=access_token,
            refresh_token=refresh_token,
            token_uri="https://oauth2.googleapis.com/token",
            client_id=os.getenv("GOOGLE_CLIENT_ID"),
            client_secret=os.getenv("GOOGLE_CLIENT_SECRET")
        )
        service = build("calendar", "v3", credentials=creds)
        start_of_day = datetime.datetime.strptime(date, "%Y-%m-%d").isoformat() + "Z"
        end_of_day = (datetime.datetime.strptime(date, "%Y-%m-%d") + datetime.timedelta(days=1)).isoformat() + "Z"

        # Fetch events
        events_result = (
            service.events()
            .list(
                calendarId="primary",
                timeMin=start_of_day,
                timeMax=end_of_day,
                singleEvents=True,
                orderBy="startTime",
            )
            .execute()
        )
        return events_result.get("items", [])

    async def get_events_by_week(self, access_token: str, refresh_token: str, start_date: str):
        creds = Credentials(
            token=access_token,
            refresh_token=refresh_token,
            token_uri="https://oauth2.googleapis.com/token",
            client_id=os.getenv("GOOGLE_CLIENT_ID"),
            client_secret=os.getenv("GOOGLE_CLIENT_SECRET")
        )
        service = build("calendar", "v3", credentials=creds)
        start_of_week = datetime.datetime.strptime(start_date, "%Y-%m-%d").isoformat() + "Z"
        end_of_week = (datetime.datetime.strptime(start_date, "%Y-%m-%d") + datetime.timedelta(days=7)).isoformat() + "Z"

        # Fetch events
        events_result = (
            service.events()
            .list(
                calendarId="primary",
                timeMin=start_of_week,
                timeMax=end_of_week,
                singleEvents=True,
                orderBy="startTime",
            )
            .execute()
        )
        return events_result.get("items", [])

    async def get_events_in_custom_range(self, access_token: str, refresh_token: str, start_date: str, end_date: str):
        creds = Credentials(
            token=access_token,
            refresh_token=refresh_token,
            token_uri="https://oauth2.googleapis.com/token",
            client_id=os.getenv("GOOGLE_CLIENT_ID"),
            client_secret=os.getenv("GOOGLE_CLIENT_SECRET")
        )
        service = build("calendar", "v3", credentials=creds)
        start_time = datetime.datetime.strptime(start_date, "%Y-%m-%d").isoformat() + "Z"
        end_time = datetime.datetime.strptime(end_date, "%Y-%m-%d").isoformat() + "Z"

        # Fetch events
        events_result = (
            service.events()
            .list(
                calendarId="primary",
                timeMin=start_time,
                timeMax=end_time,
                singleEvents=True,
                orderBy="startTime",
            )
            .execute()
        )
        return events_result.get("items", [])

calendar = CalendarService()