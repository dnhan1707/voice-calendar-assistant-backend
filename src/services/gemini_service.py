from google import genai
import os


gemini_api_key = os.getenv("GEMINI_API_KEY")
client = genai.Client(api_key=gemini_api_key)


class GeminiService:
    def __init__(self):
        self.general_discussion_prompt = '''
            You are a helpful assistant
        '''

        self.generate_SQL_prompt = '''
            You are an AI assistant that generates SQL queries based on user input. 
            The user interacts with a calendar management system that stores events in a PostgreSQL database. 
            The `events` table has the following schema:

            CREATE TABLE events (
                id SERIAL PRIMARY KEY,
                title VARCHAR(255) NOT NULL,
                description TEXT,
                start_time TIMESTAMP NOT NULL,
                end_time TIMESTAMP NOT NULL
            );

            The user may ask for various types of information about their events. Here are some example queries and the corresponding SQL code:

            1. User Query: "Give me my calendar for tomorrow."
               Output: {"sql": "SELECT * FROM events WHERE start_time::date = CURRENT_DATE + INTERVAL '1 day';"}

            2. User Query: "Show all events for the next week."
               Output: {
                        "sql": "SELECT * FROM events WHERE start_time::date >= CURRENT_DATE AND start_time::date < CURRENT_DATE + INTERVAL '7 days';"
                        "mode": "get"
                    }

            3. User Query: "List all my meetings."
               Output: {
                        "sql": SELECT * FROM events WHERE title ILIKE '%meeting%';"
                        "mode": "get"
                    }

            4. User Query: "What events do I have today?"
               Output: {"sql": SELECT * FROM events WHERE start_time::date = CURRENT_DATE;"
                        "mode": "get"
                    }

            5. User Query: "Find events with Alice."
               Output: {
                            "sql": SELECT * FROM events WHERE description ILIKE '%Alice%';"
                            "mode": "get"
                        }

            6. User Query: "Create a new event titled 'Team Meeting' with description 'Discuss project status', starting at '2025-03-20 10:00:00' and ending at '2025-03-20 11:00:00'."
               Output: {
                            "sql": INSERT INTO events (title, description, start_time, end_time) VALUES ('Team Meeting', 'Discuss project status', '2025-03-20 10:00:00', '2025-03-20 11:00:00');"
                            "mode": "insert"
                        }

            7. User Query: "Delete the event with title 'Dentist Appointment'."
               Output: {
                            "sql": DELETE FROM events WHERE title = 'Dentist Appointment';"                            
                            "mode": "delete"
                        }
            8. User Query: "Update the event 'Team Meeting' to start at 11:00 AM tomorrow."
               Output: {"sql": "UPDATE events SET start_time = (CURRENT_DATE + INTERVAL '1 day' + INTERVAL '11 hours') WHERE title = 'Team Meeting';", "mode": "update"}
               
            9. User Query: "Change the description of my dentist appointment to 'Remember to bring insurance card'."
               Output: {"sql": "UPDATE events SET description = 'Remember to bring insurance card' WHERE title ILIKE '%dentist%';", "mode": "update"}
               
            10. User Query: "Reschedule my meeting with marketing team from today to tomorrow same time."
                Output: {"sql": "UPDATE events SET start_time = start_time + INTERVAL '1 day', end_time = end_time + INTERVAL '1 day' WHERE title ILIKE '%marketing%' AND start_time::date = CURRENT_DATE;", "mode": "update"}

            When generating SQL code:
                1. Always use ILIKE with wildcards (%keyword%) for matching event titles or descriptions
                2. Consider combining multiple conditions (title ILIKE '%keyword1%' OR title ILIKE '%keyword2%')
                3. For time-specific queries, use date functions appropriately
                4. Return a valid JSON object with 'sql' and 'mode' fields
                5. The mode should be one of: 'get', 'insert', 'update', or 'delete'
            '''

    async def general_discussion(self, user_query):
        response = client.models.generate_content(
            model="gemini-2.0-flash", 
            contents=user_query
        )
        return response.text

    async def generate_SQL(self, user_query):
        response = client.models.generate_content(
            model="gemini-2.0-flash", 
            contents=self.generate_SQL_prompt + "  Here is Input: " + user_query + "            ### **Output (raw JSON only):** "
        )
        return response.text

    async def clean_response(self, event_data):
        prompt = '''
            You are a calendar assistant with access to the user's calendar database. 
            You have received data from the database and need to create a meaningful response. 
            The response should be in one sentence and easy for a human to understand.
        '''
        response = client.models.generate_content(
            model="gemini-2.0-flash", 
            contents=prompt + " Here is the event data: " + event_data
        )
        return response.text

gemini = GeminiService()