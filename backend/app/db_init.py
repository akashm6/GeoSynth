import psycopg2

def db_conn():
    conn_params = {
        "dbname": "globedb_dev",
        "user": "postgres",
        "password": "",
        "host": "localhost",
        "port": "5432"
    }
    global conn
    try:
        conn = psycopg2.connect(**conn_params)
        print("works", flush=True)
    except Exception as e:
        print(e)

if __name__ == "__main__":
    print("trying to connect...")
    db_conn()
    