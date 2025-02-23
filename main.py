from fastapi import FastAPI, Depends, HTTPException
from chatbot import chatbot
from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import RedirectResponse
from google_auth_oauthlib.flow import Flow
import os
import pathlib

app = FastAPI()

# OAuth Setup
os.environ["OAUTHLIB_INSECURE_TRANSPORT"] = "1"  # Allow HTTP for local dev
CLIENT_SECRETS_FILE = pathlib.Path(__file__).parent / "client_secret.json"
SCOPES = ["https://www.googleapis.com/auth/calendar.events"]
REDIRECT_URI = "http://localhost:3000"


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


# Route to start OAuth login
@app.get("/auth/login")
async def login():
    flow = Flow.from_client_secrets_file(
        CLIENT_SECRETS_FILE,
        scopes=SCOPES,
        redirect_uri=REDIRECT_URI,
    )
    auth_url, _ = flow.authorization_url(prompt="consent")
    return RedirectResponse(auth_url)

# Callback Route to exchange token
@app.get("/auth/callback")
async def auth_callback(code: str):
    flow = Flow.from_client_secrets_file(
        CLIENT_SECRETS_FILE,
        scopes=SCOPES,
        redirect_uri=REDIRECT_URI,
    )
    flow.fetch_token(code=code)
    
    credentials = flow.credentials
    return {"access_token": credentials.token, "refresh_token": credentials.refresh_token}
