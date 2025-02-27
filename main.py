from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.routes import auth, calendar, chatbot
from dotenv import load_dotenv

load_dotenv()

app = FastAPI()

# CORS Middleware should be added before defining any routes
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Only allow frontend origin (not "*")
    allow_credentials=True,
    allow_methods=["*"],  # Allow all HTTP methods
    allow_headers=["*"],  # Allow all headers
)

app.include_router(auth.router)
# app.include_router(calendar.router)
app.include_router(chatbot.router)

@app.get("/")
def read_root():
    return {"Hello": "World"}