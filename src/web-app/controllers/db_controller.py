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

def check_permission(username: str, perm_name: str):
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute("""
            SELECT 1 
            FROM user_perms 
            WHERE username = %s 
            AND permissions @> %s::jsonb 
            LIMIT 1;
        """, (username, f'["{perm_name}"]'))

        # Fetch the result
        result = cursor.fetchone()

        # Check if the user has the permission
        return result is not None

    except Exception as e:
        print(f"Error checking permission: {e}")
        return False
    finally:
        # Close the connection
        cursor.close()
        conn.close()

def change_role(username: str, role_id: int):
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        # Update the user's role
        cursor.execute("""
            UPDATE users SET role_id = %s WHERE username = %s;
        """, (role_id, username))

        conn.commit()
        print(f"Role updated successfully for {username}!")

    except Exception as e:
        print(f"Error changing role: {e}")
    finally:
        # Close the connection
        cursor.close()
        conn.close()

def remove_permission(username: str, perm_name: str):
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute("""
            UPDATE user_perms
            SET permissions = permissions - %s
            WHERE username = %s;
        """, (perm_name, username))

        conn.commit()
        print(f"Successfully removed '{perm_name}' from '{username}'.")

    except Exception as e:
        print(f"Error removing permission: {e}")
    finally:
        cursor.close()
        conn.close()

def add_permission(username: str, perm_name: str):
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute("""
            UPDATE user_perms
            SET permissions = permissions || %s::jsonb
            WHERE username = %s;
        """, (f'["{perm_name}"]', username))

        conn.commit()
        print(f"Successfully added '{perm_name}' to '{username}'.")

    except Exception as e:
        print(f"Error adding permission: {e}")
    finally:
        cursor.close()
        conn.close()

def remove_user(username: str):
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute("""
            DELETE FROM users WHERE username = %s;
        """, (username,))

        conn.commit()
        print(f"Successfully removed '{username}'.")
    except Exception as e:
        print(f"Error removing username: {e}")
    finally:
        cursor.close()
        conn.close()


def mark_user_logged_in(username: str):
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            INSERT INTO user_logged_in_set (username, logged_in_at)
            VALUES (%s, NOW())
            ON CONFLICT(username) DO UPDATE
            SET logged_in_at = NOW();
        """, (username,))
        
        conn.commit()
        print(f"{username} is Logged in!")
    except Exception as e:
        print(f"Error marking user as logged in: {e}")
    finally:
        cursor.close()
        conn.close()

def mark_user_logged_out(username: str):
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            DELETE FROM user_logged_in_set WHERE username = %s
        """, (username,))
        
        conn.commit()
        print(f"{username} is Logged out!")
    except Exception as e:
        print(f"Error marking user as logged out: {e}")
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()

def get_user_overview():
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute("""
            SELECT 
                u.username,
                r.role_name,
                CASE
                    WHEN us.username IS NOT NULL THEN 'Logged In'
                    ELSE 'Logged Out'
                END AS status
            FROM users u
            JOIN roles r ON u.role_id = r.role_id
            LEFT JOIN user_logged_in_set us ON u.username = us.username;
        """)

        return cursor.fetchall()
    except Exception as e:
        print(f"Error fetching user overview: {e}")
    finally:
        cursor.close()
        conn.close()

# Function to clear the users table for all users
def clear_all_users():
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute("""
            DELETE FROM users;
        """)

        conn.commit()
        print("All users cleared successfully!")
    except Exception as e:
        print(f"Error clearing users: {e}")
    finally:
        cursor.close()
        conn.close()
