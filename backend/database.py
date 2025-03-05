from psycopg2.pool import SimpleConnectionPool
import os
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")  # Format: postgres://user:password@localhost:5432/db_name

db_pool = SimpleConnectionPool(1, 5, dsn=DATABASE_URL)

def get_db_connection():
    conn = db_pool.getconn()
    try:
        yield conn
    finally:
        db_pool.putconn(conn)
