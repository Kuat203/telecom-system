import sqlite3

conn = sqlite3.connect("database.db")
cursor = conn.cursor()

cursor.execute("""
CREATE TABLE clients (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    full_name TEXT,
    phone TEXT
)
""")
cursor.execute("""
CREATE TABLE IF NOT EXISTS subscriptions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    client_id INTEGER,
    service_id INTEGER,
    start_date TEXT,
    status TEXT
)
""")

conn.commit()
conn.close()
