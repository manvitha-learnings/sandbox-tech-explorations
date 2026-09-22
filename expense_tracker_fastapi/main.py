from fastapi import FastAPI
import os
import pymysql

app = FastAPI()

def get_db_connection():
    db_host = os.getenv("DB_HOST", "")
    try:
        if db_host.startswith("/cloudsql/"):
            return pymysql.connect(
                unix_socket=db_host,
                user=os.getenv("DB_USER"),
                password=os.getenv("DB_PASSWORD"),
                database=os.getenv("DB_NAME"),
                cursorclass=pymysql.cursors.DictCursor
            )
        else:
            return pymysql.connect(
                host=db_host,
                port=int(os.getenv("DB_PORT", 3306)),
                user=os.getenv("DB_USER"),
                password=os.getenv("DB_PASSWORD"),
                database=os.getenv("DB_NAME"),
                cursorclass=pymysql.cursors.DictCursor
            )
    except Exception as e:
        print(f"Database connection error: {e}")
        return None

@app.get("/")
def read_root():
    conn = get_db_connection()
    if conn:
        conn.close()
        return {"status": "online", "database": os.getenv("DB_NAME")}
    return {"status": "online", "database": None}