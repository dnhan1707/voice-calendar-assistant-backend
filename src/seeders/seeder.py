import os
from utils.db import get_db_connection

def seed_events():
    connection = get_db_connection()
    cursor = connection.cursor()
    
    # Create the events table if it doesn't exist
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS events (
            id SERIAL PRIMARY KEY,
            title VARCHAR(255) NOT NULL,
            description TEXT,
            start_time TIMESTAMP NOT NULL,
            end_time TIMESTAMP NOT NULL
        )
    """)
    
    # Insert sample data
    cursor.execute("""
        INSERT INTO events (title, description, start_time, end_time)
        VALUES
        ('Meeting with Bob', 'Discuss project updates', '2025-03-19 10:00:00', '2025-03-19 11:00:00'),
        ('Lunch with Alice', 'Catch up over lunch', '2025-03-19 12:00:00', '2025-03-19 13:00:00'),
        ('Dentist Appointment', 'Routine check-up', '2025-03-19 15:00:00', '2025-03-19 16:00:00')
    """)
    
    connection.commit()
    cursor.close()
    connection.close()
    print("Database seeded successfully.")

if __name__ == "__main__":
    seed_events()