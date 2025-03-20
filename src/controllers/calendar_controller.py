from src.utils.db import get_db_connection
from src.services.gpt_service import gpt
from src.services.gemini_service import gemini

import json

class CalendarController:
    def __init__(self):
        pass

    async def read_calendar(self, query: str) -> str:
        try:
            sql_response = await gemini.generate_SQL(user_query=query)
            
            # Extract JSON from potential markdown or text
            json_str = sql_response.strip()
            if "```json" in json_str:
                json_str = json_str.split("```json")[1].split("```")[0].strip()
            elif "```" in json_str:
                json_str = json_str.split("```")[1].split("```")[0].strip()
            
            # Try to parse the JSON
            try:
                parsed_sql = json.loads(json_str)
                print(f"SQL Code: {parsed_sql}")
            except json.JSONDecodeError as e:
                print(f"JSON Decode Error: {e}")
                print(f"Original response: {sql_response}")
                return f"I couldn't understand the response. Please try again with a clearer request."
                
            # Process based on mode
            if parsed_sql.get("mode") == "get":
                event_data = await self.execute_SQL_get(sql=parsed_sql["sql"])
                cleaned_response = await gemini.clean_response(event_data=str(event_data))
                return cleaned_response
            
            elif parsed_sql.get("mode") == "insert":
                event_data_status = await self.execute_SQL_insert(sql=parsed_sql["sql"])
                return event_data_status
            
            elif parsed_sql.get("mode") == "delete":
                event_data_status = await self.execute_SQL_delete(sql=parsed_sql["sql"])
                return event_data_status
            
            elif parsed_sql.get("mode") == "update":
                event_data_status = await self.exceute_SQL_update(sql=parsed_sql["sql"])
                return event_data_status
            else:
                return "Unknown Mode or malformed response"
                
        except Exception as e:
            print(f"Error in read_calendar: {str(e)}")
            return "An error occurred while processing your request."
    async def execute_SQL_get(self, sql: str):
        connection = get_db_connection()
        cursor = connection.cursor()
        cursor.execute(sql)
        connection.commit()  # Ensure the transaction is committed
        event_data = cursor.fetchall()
        cursor.close()
        connection.close()
        if event_data:
            print("Event data: ", event_data)
            return event_data
        else:
            print("Cannot Execute SQL Command")
            return None

    async def execute_SQL_insert(self, sql: str):
        connection = get_db_connection()
        cursor = connection.cursor()
        try:
            cursor.execute(sql)
            connection.commit()  # Ensure the transaction is committed
            cursor.close()
            connection.close()
            return "Successfully created a new event"
        except Exception as e:
            cursor.close()
            connection.close()
            return f"Cannot Execute SQL for Insert Command: {str(e)}"

    async def execute_SQL_delete(self, sql: str):
        connection = get_db_connection()
        cursor = connection.cursor()
        try:
            cursor.execute(sql)
            connection.commit()  # Ensure the transaction is committed
            cursor.close()
            connection.close()
            return "Successfully deleted the event"
        except Exception as e:
            cursor.close()
            connection.close()
            return f"Cannot Execute SQL for Delete Command: {str(e)}"
    
    async def exceute_SQL_update(self, sql: str):
        connection = get_db_connection()
        cursor = connection.cursor()
        try:
            cursor.execute(sql)
            connection.commit()  # Ensure the transaction is committed
            cursor.close()
            connection.close()
            return "Successfully update the event"
        except Exception as e:
            cursor.close()
            connection.close()
            return f"Cannot Execute SQL for Update Command: {str(e)}"

calendar_controller = CalendarController()