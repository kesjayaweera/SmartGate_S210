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
# user_info1 = {
#     "id": 123,  # Example user ID
#     "login": "talha",  # Example GitHub username (or whatever username you want)
#     "role_id": 1  # Hardcoded role ID
# }

# user_info2 = {
#     "id": 124,  # Example user ID
#     "login": "john",  # Example GitHub username (or whatever username you want)
#     "role_id": 2  # Hardcoded role ID
# }

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

        query = """
            SELECT 1 
            FROM user_perms 
            WHERE username = %s 
            AND permissions @> %s::jsonb 
            LIMIT 1;
        """
        cursor.execute(query, (username, f'["{perm_name}"]'))

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

# Example usage:
# has_permission = check_permission('john', 'open_gate')
# print(has_permission)

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

# change_role("john", 2)
# print(check_permission('john', "open_gate"))
# remove_permission("john", "view_gate")
add_permission("john", "view_gate")
