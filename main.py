from fastapi import FastAPI, Request, HTTPException
from chatbot import chatbot
from calendar_service import calendar
from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import RedirectResponse
from google_auth_oauthlib.flow import Flow
import os
from dotenv import load_dotenv
import json

load_dotenv()

app = FastAPI()

# CORS Middleware should be added before defining any routes
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],  # Only allow frontend origin (not "*")
    allow_credentials=True,
    allow_methods=["*"],  # Allow all HTTP methods
    allow_headers=["*"],  # Allow all headers
)

SCOPES = os.getenv("SCOPES").split(",")
REDIRECT_URI = os.getenv("REDIRECT_URI")
GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID")
GOOGLE_CLIENT_SECRET = os.getenv("GOOGLE_CLIENT_SECRET")
TOKEN_URI = "https://oauth2.googleapis.com/token"

# Create a credentials.json file dynamically
credentials_content = {
    "web": {
        "client_id": GOOGLE_CLIENT_ID,
        "client_secret": GOOGLE_CLIENT_SECRET,
        "redirect_uris": [REDIRECT_URI],
        "auth_uri": "https://accounts.google.com/o/oauth2/auth",
        "token_uri": TOKEN_URI
    }
}

with open("credentials.json", "w") as f:
    json.dump(credentials_content, f)

# Step 1: Initialize OAuth Flow
flow = Flow.from_client_secrets_file(
    "credentials.json",  # Path to the dynamically created credentials.json file
    scopes=SCOPES,
    redirect_uri=REDIRECT_URI
)

class ChatRequest(BaseModel):
    user_input: str
    access_token: str
    refresh_token: str

@app.get("/")
def read_root():
    return {"Hello": "World"}

@app.post("/chatbot/")
async def talk_with_model(request: ChatRequest):
    user_input = request.user_input  # Extract user_input correctly
    access_token = request.access_token
    refresh_token = request.refresh_token
    result = await chatbot.get_response(user_input)
    print(result)
    try:
        result = json.loads(result)  # Ensure response is parsed as JSON
        print("Result after json: ", result)
    except json.JSONDecodeError:
        raise HTTPException(status_code=400, detail="Invalid response from chatbot")

    if result["query_type"] == "date":
        calendar_events =  await calendar.get_events_by_date(access_token, refresh_token, GOOGLE_CLIENT_ID, GOOGLE_CLIENT_SECRET, TOKEN_URI, result["date"])
        return await chatbot.discuss_about_calendar(calendar_events, user_input)
    elif result["query_type"] == "week":
        calendar_events = await calendar.get_events_by_week(access_token, refresh_token, GOOGLE_CLIENT_ID, GOOGLE_CLIENT_SECRET, TOKEN_URI, result["start_date"])
        return await chatbot.discuss_about_calendar(calendar_events, user_input)
    elif result["query_type"] == "range":
        calendar_events = await calendar.get_events_in_custom_range(access_token, refresh_token, GOOGLE_CLIENT_ID, GOOGLE_CLIENT_SECRET, TOKEN_URI, result["start_date"], result["end_date"])
        return await chatbot.discuss_about_calendar(calendar_events, user_input)
    elif result["query_type"] == "talk":
        return await chatbot.normal_discussion(user_input)
    else:
        return {"error": "Could not determine event query type"}

@app.get("/auth/login")
async def login():
    """Redirects user to Google OAuth login."""
    auth_url, _ = flow.authorization_url(prompt="consent")
    return RedirectResponse(auth_url)

@app.get("/auth/redirect")
async def auth_callback(request: Request):
    """Handles the OAuth callback and gets access token."""
    code = request.query_params.get("code")
    flow.fetch_token(code=code)
    credentials = flow.credentials
    access_token = credentials.token
    refresh_token = credentials.refresh_token
    # Redirect back to the frontend with the access token and refresh token
    redirect_url = f"http://localhost:3000?access_token={access_token}&refresh_token={refresh_token}"
    return RedirectResponse(url=redirect_url)

@app.get("/calendar/")
async def get_events(access_token: str, refresh_token: str):
    events = await calendar.get_event_test_connection(access_token, refresh_token, GOOGLE_CLIENT_ID, GOOGLE_CLIENT_SECRET, TOKEN_URI)
    return events