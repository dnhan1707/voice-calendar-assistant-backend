from fastapi import FastAPI
from src.routes.chatbot import router as chatbot_router

app = FastAPI()
app.include_router(chatbot_router)

@app.get("/")
def health_check():
    return "Fast api working"

