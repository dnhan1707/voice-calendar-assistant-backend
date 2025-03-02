from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
from app.routes.chatbot import router as chatbot_router
from app.routes.auth import router as auth_router  
# from app.routes.calendar import router as calendar_router  

load_dotenv()

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],  
    allow_credentials=True,
    allow_methods=["*"],  
    allow_headers=["*"],  
)

# Include routers
app.include_router(chatbot_router)
app.include_router(auth_router)  

@app.get("/")
def read_root():
    return {"Hello": "World"}
