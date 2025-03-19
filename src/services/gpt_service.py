from openai import OpenAI
import os

api_key = os.getenv("OPENAI_API_KEY")
client = OpenAI()
client.api_key = api_key

class GPT_Service:
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

            When generating SQL code, ensure that the query is accurate and handles potential edge cases. The SQL code should be safe and efficient.
            ### **Output (raw JSON only):** 
        '''

    async def general_discussion(self, user_query):
        completion = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": self.general_discussion_prompt},
                {"role": "user", "content": user_query}
            ]
        )
        return completion.choices[0].message.content

    async def generate_SQL(self, user_query):
        completion = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": self.generate_SQL_prompt},
                {"role": "user", "content": user_query}
            ]
        )
        return completion.choices[0].message.content

    async def clean_response(self, event_data):
        prompt = '''
            You are a calendar assistant with access to the user's calendar database. 
            You have received data from the database and need to create a meaningful response. 
            The response should be in one sentence and easy for a human to understand.
        '''
        completion = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": prompt},
                {"role": "user", "content": str(event_data)}
            ]
        )
        return completion.choices[0].message.content

gpt = GPT_Service()