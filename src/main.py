from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from src.routes.chatbot import router as chatbot_router

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  
    allow_credentials=True,
    allow_methods=["*"],  
    allow_headers=["*"],  
)


app.include_router(chatbot_router)

@app.get("/")
def health_check():
    return "Fast api working"

