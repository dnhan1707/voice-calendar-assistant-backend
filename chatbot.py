from openai import OpenAI
import os
from dotenv import load_dotenv

load_dotenv()

api_key = os.getenv("OPENAI_API_KEY")
client = OpenAI()
client.api_key = api_key

class ChatBot:
    def __init__(self):
        pass

    async def get_response(self, user_input: str) -> str:
        completion = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "developer", "content": "You are a helpful assistant."},
                    {
                        "role": "user",
                        "content": user_input
                    }
                ]
            )
        return completion.choices[0].message


chatbot = ChatBot()
