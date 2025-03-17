from openai import OpenAI
from dotenv import load_dotenv
import os
import datetime
import json

load_dotenv()

api_key = os.getenv("OPENAI_API_KEY")
client = OpenAI()
client.api_key = api_key

class ChatBot:
    def __init__(self):
        today = datetime.datetime.now()
        
        self.prompt = f'''
            You are a natural language processor that classifies user requests to fetch or create calendar events. 
            Today's date is {today.strftime("%Y-%m-%d")}. Always calculate dates based on this current date.
            
            Analyze the user's input and classify it into one of the following query types:

            1. **"date"** → If the user asks for events on a specific day.
            - Extract the date in **YYYY-MM-DD** format.
            - For relative terms: "today" = {today.strftime("%Y-%m-%d")}, "tomorrow" = {(today + datetime.timedelta(days=1)).strftime("%Y-%m-%d")}, etc.

            2. **"custom"** → If the user asks for events within a custom date range.
            - Extract both the **start date** and **end date** in **YYYY-MM-DD** format.
            - User may ask for week, month, etc.

            3. **"create"** → If the user wants to create a new event.
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

            For all date references, always calculate the actual date based on today being {today.strftime("%Y-%m-%d")}.

            ### **Examples:**
            1. **Input:** "What events do I have on March 15th?"
            - **Output:** {{ "endpoint": "get", "query-type": "date", "date": "2025-03-15" }}

            2. **Input:** "Show me my schedule for this week."
            - **Output:** {{ "endpoint": "get", "query-type": "custom", "start_date": "{today.strftime("%Y-%m-%d")}", "end_date": "{(today + datetime.timedelta(days=7)).strftime("%Y-%m-%d")}" }}

            3. **Input:** "Create a meeting with the marketing team tomorrow at 2pm until 3pm."
            - **Output:** {{ "endpoint": "create", "summary": "Meeting with marketing team", "start_date": "{(today + datetime.timedelta(days=1)).strftime("%Y-%m-%d")}", "end_date": "{(today + datetime.timedelta(days=1)).strftime("%Y-%m-%d")}", "start_time": "14:00", "end_time": "15:00" }}

            4. **Input:** "Add an all-day conference tomorrow called AI Summit."
            - **Output:** {{ "endpoint": "create", "summary": "AI Summit", "start_date": "{(today + datetime.timedelta(days=1)).strftime("%Y-%m-%d")}", "end_date": "{(today + datetime.timedelta(days=1)).strftime("%Y-%m-%d")}", "all_day": true }}

            ### **User Input:**

            ### **Output (raw JSON only):**
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
    
    async def find_best_event_match(self, events_data, user_query, id_only=False):
        """Find the best matching event based on user query."""
        events = events_data.get("events", [])
        original_query = events_data.get("original_query", user_query)
        
        if not events:
            return {"found": False, "message": "No upcoming events found in your calendar."}
        
        # Format events as a simple string with numbered list to save tokens
        events_text = "\n".join([
            f"{i+1}. {e['title']} - {e['time']}{' - ' + e['location'] if e.get('location') else ''}"
            for i, e in enumerate(events)
        ])
        
        prompt = f"""
            USER QUERY: "{original_query}"
            
            UPCOMING EVENTS:
            {events_text}
            
            Based on the user's query, find the SINGLE most relevant event from the list above.
            No need to be exact - if the meaning is similar, consider it a match.
            If there's a match, respond with the EVENT NUMBER (just the number) and a brief explanation.
            If there's no good match, say "No matching event found."
            
            Respond in this format:
            MATCH: [event number or "none"]
            REASON: [brief explanation of why this event matches or doesn't]
        """
        
        completion = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "You are a calendar assistant helping find matching events."},
                {"role": "user", "content": prompt}
            ]
        )
        
        response = completion.choices[0].message.content
        print("GPT Response:", response)
        
        # Parse the response to get the match
        match_event = None
        match_line = [line for line in response.split('\n') if line.startswith("MATCH:")]
        if match_line and "none" not in match_line[0].lower():
            try:
                # Extract the event number - look for the first number in the string
                match_text = match_line[0].split("MATCH:")[1].strip()
                import re
                numbers = re.findall(r'\d+', match_text)
                if numbers:
                    match_num = int(numbers[0]) - 1  # Convert to 0-based index
                    if 0 <= match_num < len(events):
                        match_event = events[match_num]
            except Exception as e:
                print(f"Error parsing match number: {e}")
        
        if match_event:
            if id_only:
                return [match_event.get("id")]
            return {
                "found": True,
                "event": match_event,
                "explanation": response,
                "all_events_count": len(events)
            }
        else:
            return {
                "found": False,
                "message": "No matching event found based on your query.",
                "explanation": response,
                "all_events_count": len(events)
            }

    async def create_meaningful_response(self, input):
        completion = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "assistant", "content": f'You are a Voice AI Calendar Assistant'},
                    {
                        "role": "user",
                        "content": f'Here is the info: {input}. Please simplify this and provide a user friendly response in 1 sentence'
                    }
                ]
            )
        return completion.choices[0].message.content

    async def extract_event_params(self, user_input: str) -> dict:
        """Use GPT to extract event parameters from user input."""
        prompt = f'''
            You are a natural language processor that extracts event details from user requests.
            Today's date is {datetime.datetime.now().strftime("%Y-%m-%d")}.
            
            Analyze the user's input and extract the following event details:
            - summary (required): The title of the event
            - start_date (required): Start date in YYYY-MM-DD format
            - end_date (required): End date in YYYY-MM-DD format
            - start_time (optional): Start time in HH:MM format (24-hour)
            - end_time (optional): End time in HH:MM format (24-hour)
            - location (optional): The location of the event
            - description (optional): Description of the event
            - all_day (optional): Whether this is an all-day event (true/false)
            - attendees (optional): List of email addresses

            For all date references, always calculate the actual date based on today being {datetime.datetime.now().strftime("%Y-%m-%d")}.
            
            ### **Examples:**
            1. **Input:** "Create a meeting with the marketing team tomorrow at 2pm until 3pm."
            - **Output:** {{ "summary": "Meeting with marketing team", "start_date": "{(datetime.datetime.now() + datetime.timedelta(days=1)).strftime("%Y-%m-%d")}", "end_date": "{(datetime.datetime.now() + datetime.timedelta(days=1)).strftime("%Y-%m-%d")}", "start_time": "14:00", "end_time": "15:00" }}

            2. **Input:** "Add an all-day conference tomorrow called AI Summit."
            - **Output:** {{ "summary": "AI Summit", "start_date": "{(datetime.datetime.now() + datetime.timedelta(days=1)).strftime("%Y-%m-%d")}", "end_date": "{(datetime.datetime.now() + datetime.timedelta(days=1)).strftime("%Y-%m-%d")}", "all_day": true }}

            ### **User Input:**
            {user_input}

            ### **Output (raw JSON only):**
        '''
        
        completion = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": prompt},
                {"role": "user", "content": user_input}
            ]
        )
        
        response = completion.choices[0].message.content
        try:
            event_params = json.loads(response)
            return event_params
        except json.JSONDecodeError:
            return {"error": "Failed to parse event parameters from user input."}


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