import os
from dotenv import load_dotenv

def load_env():
    load_dotenv()
    return {
        "SCOPES": os.getenv("SCOPES").split(","),
        "REDIRECT_URI": os.getenv("REDIRECT_URI"),
        "GOOGLE_CLIENT_ID": os.getenv("GOOGLE_CLIENT_ID"),
        "GOOGLE_CLIENT_SECRET": os.getenv("GOOGLE_CLIENT_SECRET"),
        "TOKEN_URI": "https://oauth2.googleapis.com/token"
    }