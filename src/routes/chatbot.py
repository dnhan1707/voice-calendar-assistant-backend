from fastapi import APIRouter
from pydantic import BaseModel
from src.services.gpt_service import gpt
from src.services.gemini_service import gemini

from src.controllers.calendar_controller import calendar_controller

class QueryRequest(BaseModel):
    query: str

router = APIRouter()


@router.post("/chatbot/")
async def gpt_chat(query: str) -> str:
    return f"Recieved: {query}"


@router.post("/chatbot/discusion")
async def general_discussion(query: str) -> str:
    return await gemini.general_discussion(query)


@router.post("/chatbot/sql")
async def create_query(query: str) -> str:
    return await gemini.generate_SQL(query)


@router.post("/chatbot/event")
async def read_calendar(request: QueryRequest) -> str:
    return await calendar_controller.read_calendar(request.query)


# @router.post("/chatbot/insert_event")
# async def read_calendar(query: str) -> str:
#     return await calendar_controller.read_calendar(query)



# @router.post("/chatbot/delete_calendar")
# async def read_calendar(query: str) -> str:
#     return await calendar_controller.read_calendar(query)



