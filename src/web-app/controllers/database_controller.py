import psycopg

smartgatedb_connect = psycopg.connect(
    dbname="smartgatedb",
    user="admin",
    password="smartgate",
    host="127.0.0.1",
    port="5432"
)
dbcursor = smartgatedb_connect.cursor()

dbcursor.execute("SELECT * FROM public.test;")
rows = dbcursor.fetchall()
for row in rows:
    print(row)

dbcursor.close()
smartgatedb_connect.close()

