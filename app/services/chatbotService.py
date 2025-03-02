from openai import OpenAI
import os
from dotenv import load_dotenv

load_dotenv()

api_key = os.getenv("OPENAI_API_KEY")
client = OpenAI()
client.api_key = api_key

class ChatBot:
    def __init__(self):
        self.prompt = '''
            You are a natural language processor that classifies user requests to fetch or create calendar events. Analyze the user's input and classify it 
            into one of the following query types:

            1. **"date"** → If the user asks for events on a specific day.
            - Extract the date in **YYYY-MM-DD** format.

            2. **"week"** → If the user asks for events in a week.
            - Extract the start date of the week in **YYYY-MM-DD** format.

            3. **"range"** → If the user asks for events within a custom date range.
            - Extract both the **start date** and **end date** in **YYYY-MM-DD** format.
            
            4. **"create"** → If the user wants to create a new event.
            - Extract event details including:
            - summary (required): The title of the event
            - start_date (required): Start date in YYYY-MM-DD format
            - end_date (required): End date in YYYY-MM-DD format
            - start_time (optional): Start time in HH:MM format (24-hour)
            - end_time (optional): End time in HH:MM format (24-hour)
            - location (optional): The location of the event
            - description (optional): Description of the event
            - all_day (optional): Whether this is an all-day event (true/false)
            - attendees (optional): List of email addresses

            5. **"talk"** → For general conversation not related to calendar functions.

            Also, include the extracted date(s) and other parameters in the output.

            ### **Examples:**
            1. **Input:** "What events do I have on March 3rd?"
            - **Output:** `{ "query_type": "date", "date": "2025-03-03" }`

            2. **Input:** "Show me my schedule for this week."
            - **Output:** `{ "query_type": "week", "start_date": "2025-02-24" }`

            3. **Input:** "What events do I have between April 10 and April 15?"
            - **Output:** `{ "query_type": "range", "start_date": "2025-04-10", "end_date": "2025-04-15" }`

            4. **Input:** "Tell me my meetings next week."
            - **Output:** `{ "query_type": "week", "start_date": "2025-03-03" }`

            5. **Input:** "Create a meeting with the marketing team tomorrow at 2pm until 3pm."
            - **Output:** `{ "query_type": "create", "summary": "Meeting with marketing team", "start_date": "2025-03-02", "end_date": "2025-03-02", "start_time": "14:00", "end_time": "15:00" }`

            6. **Input:** "Schedule a dentist appointment on March 15 from 10am to 11:30am at Smile Dental Clinic."
            - **Output:** `{ "query_type": "create", "summary": "Dentist appointment", "location": "Smile Dental Clinic", "start_date": "2025-03-15", "end_date": "2025-03-15", "start_time": "10:00", "end_time": "11:30" }`
            
            7. **Input:** "Add an all-day conference on April 5th called AI Summit."
            - **Output:** `{ "query_type": "create", "summary": "AI Summit", "start_date": "2025-04-05", "end_date": "2025-04-05", "all_day": true }`

            8. **Input:** "Hey can you tell a joke"
            - **Output:** `{ "query_type": "talk" }`

            9. **Input:** "Show my schedule from March 1st to March 7th."
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
                    {
                        "role": "user",
                        "content": user_input
                    }
                ]
        )
        return completion.choices[0].message.content

    async def normal_discussion(self, user_input: str) -> str:
        completion = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "assistant", "content": "You are a helpful AI"},
                {
                    "role": "user",
                    "content": user_input
                }
            ]
        )
        return completion.choices[0].message.content

    async def discuss_about_calendar(self, calendar_events, user_input: str) -> str:
        formatted_events = self.format_calendar_events(calendar_events)
        completion = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": f'Extract important information and reply user speech, which was {user_input}'},
                    {
                        "role": "user",
                        "content": f'Here are the events: {formatted_events}. Please simplify this and provide a meaningful response.'
                    }
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