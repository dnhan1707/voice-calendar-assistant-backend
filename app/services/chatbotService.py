from openai import OpenAI
import os
from dotenv import load_dotenv
import datetime

load_dotenv()

api_key = os.getenv("OPENAI_API_KEY")
client = OpenAI()
client.api_key = api_key

class ChatBot:
    def __init__(self):
        # Get the current date and calculate examples dynamically
        today = datetime.datetime.now()
        # tomorrow = (today + datetime.timedelta(days=1)).strftime("%Y-%m-%d")
        # next_week_start = (today + datetime.timedelta(days=7)).strftime("%Y-%m-%d")
        # custom_range_start = (today + datetime.timedelta(days=14)).strftime("%Y-%m-%d")
        # custom_range_end = (today + datetime.timedelta(days=19)).strftime("%Y-%m-%d")
        
        self.prompt = f'''
            You are an intelligent assistant that extracts date-related information from user requests 
            and classifies them correctly. Today's date is **{today}**. You must **interpret all relative 
            date expressions** based on this date.

            Your task:
            - Identify whether the user is asking for a **specific date** or a **range of dates**.
            - Convert natural language date expressions like "next Monday" or "this weekend" into actual dates.
            - Classify the request under the correct endpoint.
            - Output structured JSON with correct dates.

            ### **Guidelines:**
            1. **If the user specifies a single date**, return:
            ```json
            {{ "endpoint": "get", "query-type": "date", "date": "YYYY-MM-DD" }}
            ```

            2. **If the user specifies a date range**, return:
            ```json
            {{ "endpoint": "get", "query-type": "custom", "start_date": "YYYY-MM-DD", "end_date": "YYYY-MM-DD" }}
            ```

            3. **Relative Date Conversions:**
            - "today" → {today}
            - "tomorrow" → { (datetime.datetime.now() + datetime.timedelta(days=1)).strftime("%Y-%m-%d") }
            - "this week" → From **Monday** of this week to **Sunday** of this week.
            - "next week" → From **Monday** of next week to **Sunday** of next week.
            - "next Monday" → The upcoming Monday from today.
            - "this weekend" → Saturday & Sunday of this week.

            ### **Examples:**
            1. **Input:** "What events do I have on March 15th?"
            - **Output:** {{ "endpoint": "get", "query-type": "date", "date": "2025-03-15" }}

            2. **Input:** "Show me my schedule for next Monday to next Tuesday."
            - **Output:** {{ "endpoint": "get", "query-type": "custom", "start_date": "YYYY-MM-DD", "end_date": "YYYY-MM-DD" }}

            3. **Input:** "Do I have any meetings this weekend?"
            - **Output:** {{ "endpoint": "get", "query-type": "custom", "start_date": "YYYY-MM-DD", "end_date": "YYYY-MM-DD" }}

            4. **Input:** "Show me events for the first week of April."
            - **Output:** {{ "endpoint": "get", "query-type": "custom", "start_date": "2025-04-01", "end_date": "2025-04-07" }}

            **User Input:**
            
            **Output (JSON only):**
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
    

    async def find_best_event_match(self, events_data, user_query):
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