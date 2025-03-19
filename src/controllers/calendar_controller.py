from src.utils.db import get_db_connection
from src.services.gpt_service import gpt
import json

class CalendarController:
    def __init__(self):
        pass

    async def read_calendar(self, query: str) -> str:
        sql = await gpt.generate_SQL(user_query=query)
        parsed_sql = json.loads(sql)
        print(f"SQL Code: {parsed_sql}")
        if parsed_sql["mode"] == "get":
            event_data = await self.execute_SQL_get(sql=parsed_sql["sql"])
            cleaned_response = await gpt.clean_response(event_data=event_data)
            return cleaned_response
        
        elif parsed_sql["mode"] == "insert":
            event_data_status = await self.execute_SQL_insert(sql=parsed_sql["sql"])
            return event_data_status
        
        elif parsed_sql["mode"] == "delete":
            event_data_status = await self.execute_SQL_delete(sql=parsed_sql["sql"])
            return event_data_status

        else:
            return "Unknown Mode"

    async def execute_SQL_get(self, sql: str):
        connection = get_db_connection()
        cursor = connection.cursor()
        cursor.execute(sql)
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


calendar_controller = CalendarController()