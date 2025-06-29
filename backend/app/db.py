from sqlalchemy.orm import sessionmaker
from sqlalchemy import create_engine
from dotenv import load_dotenv
import os

load_dotenv()

connection_string = os.getenv("DATABASE_CONN_STRING") or "postgresql+psycopg2://postgres:@localhost:5432/globedb_dev"
engine = create_engine(connection_string)
SessionLocal = sessionmaker(autocommit = False, autoflush = False, bind = engine)

def check_conn():
    try:
        with engine.connect() as cursor:
            cursor.execute("SELECT 1")
            print("DB Connection Successful.")
    except Exception as e:
        print("DB Connection failed.")
        print(e)

if __name__ == "__main__":
    check_conn()