from fastapi import APIRouter, Request
from fastapi.responses import RedirectResponse
from google_auth_oauthlib.flow import Flow
import os
import json

router = APIRouter()

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

@router.get("/auth/login")
async def login():
    """Redirects user to Google OAuth login."""
    auth_url, _ = flow.authorization_url(prompt="consent")
    return RedirectResponse(auth_url)

@router.get("/auth/redirect")
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