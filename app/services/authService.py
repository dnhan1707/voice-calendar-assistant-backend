from google_auth_oauthlib.flow import Flow
import os
import json
from fastapi import HTTPException

# Load environment variables
SCOPES = os.getenv("SCOPES", "").split(",")
REDIRECT_URI = os.getenv("REDIRECT_URI")
GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID")
GOOGLE_CLIENT_SECRET = os.getenv("GOOGLE_CLIENT_SECRET")
TOKEN_URI = "https://oauth2.googleapis.com/token"

# Create OAuth Flow
flow = Flow.from_client_secrets_file(
    "credentials.json",
    scopes=SCOPES,
    redirect_uri=REDIRECT_URI
)

def get_google_auth_url():
    """Generate Google OAuth URL for authentication."""
    auth_url, _ = flow.authorization_url(prompt='consent')
    return auth_url

def exchange_token(auth_code: str):
    """Exchange authorization code for an access token."""
    try:
        flow.fetch_token(code=auth_code)
        credentials = flow.credentials
        return {
            "access_token": credentials.token,
            "refresh_token": credentials.refresh_token,
            "expires_in": credentials.expiry.isoformat()
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Token exchange failed: {str(e)}")
