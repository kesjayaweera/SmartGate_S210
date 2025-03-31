import os
import psycopg

DATABASE_URL = os.getenv("DATABASE_URL")

# Connect to the database
def get_db_connection():
    conn = psycopg.connect(DATABASE_URL)
    return conn

def insert_user(user: dict):
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        # Check if the user already exists based on user_id or username
        cursor.execute("""
            SELECT COUNT(*) FROM users WHERE user_id = %s OR username = %s;
        """, (user['id'], user['login']))

        result = cursor.fetchone()

        # If the count is 0, the user doesn't exist, so insert the user
        if result[0] == 0:
            cursor.execute("""
                INSERT INTO users (user_id, username, role_id) 
                VALUES (%s, %s, %s);
            """, (user['id'], user['login'], user['role_id']))

            conn.commit()
            print("User Inserted Successfully!")
        else:
            print("User already exists. Skipping insert.")
    
    except Exception as e:
        print(f"Error inserting user: {e}")
    finally:
        # Close the connection
        cursor.close()
        conn.close()

# Mock user information (id, login, and role)
user_info1 = {
    "id": 123,  # Example user ID
    "login": "talha",  # Example GitHub username (or whatever username you want)
    "role_id": 1  # Hardcoded role ID
}

user_info2 = {
    "id": 124,  # Example user ID
    "login": "john",  # Example GitHub username (or whatever username you want)
    "role_id": 2  # Hardcoded role ID
}

# Insert the user into the database
# insert_user(user_info1)
# insert_user(user_info2)

def check_permission():
    pass
