from sqlalchemy.orm import sessionmaker
from sqlalchemy import create_engine, text
from dotenv import load_dotenv
from datetime import datetime
import os

load_dotenv()

connection_string = os.getenv("DATABASE_CONN_STRING") or "postgresql+psycopg2://postgres:@localhost:5432/globedb_dev"
engine = create_engine(connection_string)
SessionLocal = sessionmaker(autocommit = False, autoflush = False, bind = engine)

def check_conn():
    try:
        with engine.connect() as cursor:
            cursor.execute(text("SELECT 1"))
            print("DB Connection Successful.")
    except Exception as e:
        print("DB Connection failed.")
        print(e)

def create_auth_tables():
    query = """
    CREATE TABLE IF NOT EXISTS user_table (
        user_id SERIAL PRIMARY KEY,
        email TEXT,
        username TEXT,
        date_created TIMESTAMP WITH TIME ZONE
    );
    """

    now = datetime.utcnow().isoformat()
    test_insert = f"""
    INSERT INTO user_table (email, username, date_created) VALUES (
        'fakeemail', 'testusername', '{now}'
    );
    """
    try:
        with engine.begin() as cursor:
            cursor.execute(text(query))
            cursor.execute(text(test_insert))
            print("table created.")
            
    except Exception as e:
        print("table creation failed.")
        print(e)

if __name__ == "__main__":
    check_conn()