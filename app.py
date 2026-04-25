from flask import Flask, render_template, request, redirect
import sqlite3
import os

app = Flask(__name__)

def init_db():
    conn = sqlite3.connect("database.db")
    cursor = conn.cursor()

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS clients (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        full_name TEXT,
        phone TEXT
    )
    """)

    conn.commit()
    conn.close()

init_db()

def get_db():
    conn = sqlite3.connect("database.db")
    conn.row_factory = sqlite3.Row
    return conn

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/clients")
def clients():
    conn = get_db()
    clients = conn.execute("SELECT * FROM clients").fetchall()
    conn.close()
    return render_template("clients.html", clients=clients)

@app.route("/add_client", methods=["GET", "POST"])
def add_client():
    if request.method == "POST":
        name = request.form["name"]
        phone = request.form["phone"]

        conn = get_db()
        conn.execute("INSERT INTO clients (full_name, phone) VALUES (?, ?)", (name, phone))
        conn.commit()
        conn.close()

        return redirect("/clients")

    return render_template("add_client.html")



if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
