from openai import OpenAI
import os
from dotenv import load_dotenv

load_dotenv()

api_key = os.getenv("OPENAI_API_KEY")
client = OpenAI(api_key=api_key)

class ChatBot:
    def __init__(self):
        self.prompt = '''
           You are a natural language processor that classifies user requests to fetch calendar events. Analyze the user's input and classify it 
            into one of the following query types, however you can still normally communicate in some cases:

            1. **"date"** → If the user asks for events on a specific day.
            - Extract the date in **YYYY-MM-DD** format.

            2. **"week"** → If the user asks for events in a week.
            - Extract the start date of the week in **YYYY-MM-DD** format.

            3. **"range"** → If the user asks for events within a custom date range.
            - Extract both the **start date** and **end date** in **YYYY-MM-DD** format.

            Also, include the extracted date(s) in the output.

            ### **Examples:**
            1. **Input:** "What events do I have on March 3rd?"
            - **Output:** `{ "query_type": "date", "date": "2025-03-03" }`

            2. **Input:** "Show me my schedule for this week."
            - **Output:** `{ "query_type": "week", "start_date": "2025-02-24" }`

            3. **Input:** "What events do I have between April 10 and April 15?"
            - **Output:** `{ "query_type": "range", "start_date": "2025-04-10", "end_date": "2025-04-15" }`

            4. **Input:** "Tell me my meetings next week."
            - **Output:** `{ "query_type": "week", "start_date": "2025-03-03" }`

            5. **Input:** "Hey can yoou tell a joke"
            - **Output:** `{ "query_type": "talk"}`

            6. **Input:** "Show my schedule from March 1st to March 7th."
            - **Output:** `{ "query_type": "range", "start_date": "2025-03-01", "end_date": "2025-03-07" }`

            ### **User Input:**
            "{user_input}"

            ### **Output:**
        '''

    async def get_response(self, user_input: str) -> str:
        completion = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": self.prompt},
                {"role": "user", "content": user_input}
            ]
        )
        response_content = completion.choices[0].message.content
        # Clean up the response content
        response_content = response_content.replace("\\n", "").replace("\\", "")
        return response_content

    async def discuss_about_calendar(self, calendar_events, user_input: str) -> str:
        formatted_events = self.format_calendar_events(calendar_events)
        completion = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": f'Extract important information and reply user speech, which was {user_input}'},
                {"role": "user", "content": f'Here are the events: {formatted_events}. Please simplify this and provide a meaningful response and answer in an easy to understand way'}
            ]
        )
        return completion.choices[0].message.content
    
    @staticmethod
    def format_calendar_events(events):
        """Formats calendar events into a concise, readable summary."""
        if not events:
            return "There are no events for the given time period."

        event_summaries = []
        for event in events:
            title = event.get("summary", "No title")
            start_time = event.get("start", {}).get("dateTime", event.get("start", {}).get("date", "Unknown start time"))
            end_time = event.get("end", {}).get("dateTime", event.get("end", {}).get("date", "Unknown end time"))
            
            event_summaries.append(f"{title}: {start_time} → {end_time}")

        return "\n".join(event_summaries)

chatbot = ChatBot()