import os
import psycopg

DATABASE_URL = os.getenv("DATABASE_URL")

# Connect to the database
def get_db_connection():
    conn = psycopg.connect(DATABASE_URL)
    return conn

print(DATABASE_URL)
# Test the connection
conn = get_db_connection()
print(conn)
