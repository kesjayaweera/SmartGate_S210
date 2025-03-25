import psycopg

def connect_to_db():
    try:
        return psycopg.connect(
            dbname="smartgatedb",
            user="admin",
            password="smartgate",
            host="0.0.0.0",
            port="5432"
        )
    except psycopg.OperationalError:
        print("Connection Failed! Please start the database first!")
        return None

def fetch_data(connection, fetch_query):
    if connection is None:
        return
    try:
        dbcursor = connection.cursor()
        dbcursor.execute(fetch_query)
        rows = dbcursor.fetchall()
        for row in rows:
            print(row)
    except psycopg.Error as e:
        print(f"Database error: {e}")
    finally:
        dbcursor.close()
        connection.close()

def fetch_test_data():
    connection = connect_to_db()
    fetch_data(connection, "SELECT * FROM public.test;")

if __name__ == "__main__":
    fetch_test_data()
