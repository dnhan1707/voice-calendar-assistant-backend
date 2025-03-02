from fastapi import APIRouter, Request
from fastapi.responses import RedirectResponse
from app.services.authService import get_google_auth_url, exchange_token

router = APIRouter()

@router.get("/auth/login")
async def login():
    """Redirects user to Google OAuth login."""
    auth_url = get_google_auth_url()
    return RedirectResponse(auth_url)

@router.get("/auth/redirect")
async def auth_callback(request: Request):
    """Handles OAuth callback and exchanges the auth code for tokens."""
    code = request.query_params.get("code")
    if not code:
        return {"error": "No authorization code provided"}
    
    tokens = exchange_token(code)
    
    # Redirect user to frontend with access and refresh tokens
    redirect_url = f"http://localhost:3000?access_token={tokens['access_token']}&refresh_token={tokens['refresh_token']}"
    return RedirectResponse(url=redirect_url)
