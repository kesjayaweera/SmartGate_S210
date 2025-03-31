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

# We need to join the users table with the roles table using role_id to get the user's role.
# Then, we join the role_permissions table using role_id to link the user's role to the permissions.
# After that, we join the perms table using permission_id to get the actual permissions associated with the role.
# Finally, we check if the user's role has the permission by filtering based on the perm_name.
def check_permission(username: str, perm_name: str):
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute("""
            SELECT u.username, p.perm_name
            FROM users u
            JOIN roles r ON u.role_id = r.role_id
            JOIN role_permissions rp ON r.role_id = rp.role_id
            JOIN perms p ON rp.permission_id = p.perm_id
            WHERE u.username = %s AND p.perm_name = %s;
        """, (username, perm_name))

        # Fetch the result
        result = cursor.fetchone()

        # Check if the user has the permission
        if result:
            return True
        else:
            return False

    except Exception as e:
        print(f"Error checking permission: {e}")
    finally:
        # Close the connection
        cursor.close()
        conn.close()

# Example usage:
# has_permission = check_permission('talha', 'open_gate')
# print(has_permission)
