import psycopg2
import os
from dotenv import load_dotenv

load_dotenv()

def get_db_connection():
    try: 
        connection = psycopg2.connect(
            database=os.getenv("DB_NAME"),
            host=os.getenv("HOST"),
            user=os.getenv("USER"),
            password=os.getenv("PASSWORD"),
            port=os.getenv("PORT")
        )
        return connection
    except:
        print("No connection")
        return



