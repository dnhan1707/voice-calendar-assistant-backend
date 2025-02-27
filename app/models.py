from pydantic import BaseModel

class ChatRequest(BaseModel):
    user_input: str
    access_token: str
    refresh_token: str
