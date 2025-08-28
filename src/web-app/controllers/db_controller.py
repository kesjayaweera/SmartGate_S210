import os
import psycopg

DATABASE_URL = os.getenv("DATABASE_URL")

# Connect to the database
def get_db_connection():
    return psycopg.connect(DATABASE_URL)

# Function to check database connection
def check_db_connection():
    try:
        with get_db_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute("SELECT 1;")
                result = cursor.fetchone()
                if result and result[0] == 1:
                    print("Database connection is successful!")
                    return True
        return False
    except Exception as e:
        print(f"Database connection failed: {e}")
        return False


def insert_user(user: dict):
    try:
        with get_db_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute("""
                    SELECT COUNT(*) FROM users WHERE user_id = %s OR username = %s;
                """, (user['id'], user['login']))
                result = cursor.fetchone()

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


def check_permission(username: str, perm_name: str):
    try:
        with get_db_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute("""
                    SELECT 1 
                    FROM user_perms 
                    WHERE username = %s 
                    AND permissions @> %s::jsonb 
                    LIMIT 1;
                """, (username, f'["{perm_name}"]'))
                return cursor.fetchone() is not None
    except Exception as e:
        print(f"Error checking permission: {e}")
        return False


def change_role(username: str, role_name: str):
    try:
        with get_db_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute("SELECT role_id FROM roles WHERE role_name = %s;", (role_name,))
                role_id = cursor.fetchone()
                if not role_id:
                    print(f"Error: Role '{role_name}' not found.")
                    return
                cursor.execute("""
                    UPDATE users SET role_id = %s WHERE username = %s;
                """, (role_id[0], username))
                conn.commit()
                print(f"Role updated successfully for {username}!")
    except Exception as e:
        print(f"Error changing role: {e}")


def remove_permission(username: str, perm_name: str):
    try:
        with get_db_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute("""
                    UPDATE user_perms
                    SET permissions = permissions - %s
                    WHERE username = %s;
                """, (perm_name, username))
                conn.commit()
                print(f"Successfully removed '{perm_name}' from '{username}'.")
    except Exception as e:
        print(f"Error removing permission: {e}")


def add_permission(username: str, perm_name: str):
    try:
        with get_db_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute("""
                    UPDATE user_perms
                    SET permissions = permissions || %s::jsonb
                    WHERE username = %s;
                """, (f'["{perm_name}"]', username))
                conn.commit()
                print(f"Successfully added '{perm_name}' to '{username}'.")
    except Exception as e:
        print(f"Error adding permission: {e}")


def remove_user(username: str):
    try:
        with get_db_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute("DELETE FROM users WHERE username = %s;", (username,))
                conn.commit()
                print(f"Successfully removed '{username}'.")
    except Exception as e:
        print(f"Error removing username: {e}")


def mark_user_logged_in(username: str):
    try:
        with get_db_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute("""
                    UPDATE user_overview SET user_status = 'Logged in' WHERE username = %s;
                """, (username,))
                conn.commit()
                print(f"{username} is Logged in!")
    except Exception as e:
        print(f"Error marking user as logged in: {e}")


def mark_user_logged_out(username: str):
    try:
        with get_db_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute("""
                    UPDATE user_overview SET user_status = 'Logged out' WHERE username = %s;
                """, (username,))
                conn.commit()
                print(f"{username} is Logged out!")
    except Exception as e:
        print(f"Error marking user as logged out: {e}")


def get_user_overview():
    try:
        with get_db_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute("SELECT * FROM user_overview;")
                return cursor.fetchall()
    except Exception as e:
        print(f"Error fetching user overview: {e}")
        return []


def clear_all_users():
    try:
        with get_db_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute("DELETE FROM users;")
                conn.commit()
                print("All users cleared successfully!")
    except Exception as e:
        print(f"Error clearing users: {e}")


def is_user_logged_in(username: str):
    try:
        with get_db_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute("""
                    SELECT user_status = 'Logged in' FROM user_overview WHERE username = %s;
                """, (username,))
                result = cursor.fetchone()
                return result[0] if result else False
    except Exception as e:
        print(f"Error checking if user is logged in: {e}")
        return False


def get_all_roles():
    try:
        with get_db_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute("SELECT role_name FROM roles;")
                return [role[0] for role in cursor.fetchall()]
    except Exception as e:
        print(f"Failed to get all roles from db: {e}!")
        return []


def get_all_alerts():
    try:
        with get_db_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute("SELECT * FROM alerts;")
                return cursor.fetchall()
    except Exception as e:
        print(f"Failed to get all alerts from db: {e}!")
        return []


def add_alert(alert_desc: str, alert_level: str) -> bool:
    try:
        with get_db_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute("""
                    INSERT INTO alerts (alert_desc, alert_level)
                    VALUES (%s, %s);
                """, (alert_desc, alert_level))
                conn.commit()
                print(f"Alert: {alert_desc} added successfully as {alert_level}")
                return True
    except Exception as e:
        print(f"[ERROR] Failed to add alert: {e}")
        return False


def delete_alert(alert_no: int):
    try:
        with get_db_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute("DELETE FROM alerts WHERE alert_no = %s;", (alert_no,))
                conn.commit()
                print(f"Alert no: {alert_no} has been deleted!")
    except Exception as e:
        print(f"[ERROR] Failed to delete alert: {e}")
        return False


def add_gate(gate_no: int, gate_status: str):
    try:
        with get_db_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute("""
                    INSERT INTO gates (gate_no, gate_status) 
                    VALUES (%s, %s);
                """, (gate_no, gate_status))
                conn.commit()
    except Exception as e:
        print(f"[ERROR] Failed to add gate to db: {e}")
        return False


def update_gate_status(gate_no: int, new_status: str):
    try:
        with get_db_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute("SELECT gate_status FROM gates WHERE gate_no = %s;", (gate_no,))
                current_status_row = cursor.fetchone()
                if not current_status_row:
                    print(f"[ERROR] Gate {gate_no} not found.")
                    return
                current_status = current_status_row[0]
                if current_status.lower() == new_status.lower():
                    print(f"[INFO] Gate {gate_no} is already {new_status}. No update needed.")
                    return

                increment_column = "gate_no_opens" if new_status.lower() == "open" else "gate_no_closes"
                cursor.execute(f"""
                    UPDATE gates
                    SET gate_status = %s,
                        {increment_column} = {increment_column} + 1
                    WHERE gate_no = %s;
                """, (new_status, gate_no))
                conn.commit()
                print(f"[INFO] Gate {gate_no} status updated to {new_status}.")
    except Exception as e:
        print(f"[ERROR] Failed to update gate status in db: {e}")
