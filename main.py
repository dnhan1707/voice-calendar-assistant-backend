from fastapi import FastAPI, Request
from chatbot import chatbot
from calendar_service import calendar
from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import RedirectResponse
from google_auth_oauthlib.flow import Flow
import os
import pathlib

app = FastAPI()

SCOPES = ["https://www.googleapis.com/auth/calendar"]
REDIRECT_URI = "http://localhost:8000/auth/redirect"

# Step 1: Initialize OAuth Flow
flow = Flow.from_client_secrets_file(
    "credentials.json",  # Path to the credentials.json file
    scopes=SCOPES,
    redirect_uri=REDIRECT_URI
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins (change this in production)
    allow_methods=["*"],  # Allow all HTTP methods (GET, POST, etc.)
    allow_headers=["*"],  # Allow all headers
)

class ChatRequest(BaseModel):
    user_input: str

@app.get("/")
def read_root():
    return {"Hello": "World"}

@app.post("/chatbot/")
async def talk_with_model(request: ChatRequest):
    user_input = request.user_input  # Extract user_input correctly
    response = await chatbot.get_response(user_input)
    return response

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
    # Redirect back to the frontend with the access token
    redirect_url = f"http://localhost:3000?access_token={access_token}"
    return RedirectResponse(url=redirect_url)

@app.get("/calendar/")
async def get_events(access_token: str):
    events = await calendar.get_event_test_connection(access_token)
    return events