from flask import Flask, render_template, request, redirect
import sqlite3
import os

app = Flask(__name__)

# ---------- БАЗА ----------
def get_db():
    conn = sqlite3.connect("database.db")
    conn.row_factory = sqlite3.Row
    return conn

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

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS services (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT,
        price INTEGER
    )
    """)

    conn.commit()
    conn.close()

init_db()

# ---------- РОУТЫ ----------
@app.route("/")
def index():
    conn = get_db()
    client_count = conn.execute("SELECT COUNT(*) FROM clients").fetchone()[0]
    service_count = conn.execute("SELECT COUNT(*) FROM services").fetchone()[0]
    conn.close()

    return render_template("index.html", clients=client_count, services=service_count)

# ----- КЛИЕНТЫ -----
@app.route("/clients")
def clients():
    search = request.args.get("search")

    conn = get_db()

    if search:
        data = conn.execute(
            "SELECT * FROM clients WHERE full_name LIKE ?",
            ("%" + search + "%",)
        ).fetchall()
    else:
        data = conn.execute("SELECT * FROM clients").fetchall()

    conn.close()
    return render_template("clients.html", clients=data)

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

@app.route("/toggle_sub/<int:id>")
def toggle_sub(id):
    conn = get_db()

    sub = conn.execute("SELECT status FROM subscriptions WHERE id=?", (id,)).fetchone()

    new_status = "Отключена" if sub["status"] == "Активна" else "Активна"

    conn.execute("UPDATE subscriptions SET status=? WHERE id=?", (new_status, id))
    conn.commit()
    conn.close()

    return redirect("/subscriptions")

@app.route("/stats")
def stats():
    conn = get_db()
    data = conn.execute("""
    SELECT date, SUM(amount) as total
    FROM payments
    GROUP BY date
    """).fetchall()
    conn.close()

    dates = [row["date"] for row in data]
    totals = [row["total"] for row in data]

    return render_template("stats.html", dates=dates, totals=totals)

@app.route("/delete_client/<int:id>")
def delete_client(id):
    conn = get_db()
    conn.execute("DELETE FROM clients WHERE id=?", (id,))
    conn.commit()
    conn.close()
    return redirect("/clients")

# ----- УСЛУГИ -----
@app.route("/services")
def services():
    conn = get_db()
    data = conn.execute("SELECT * FROM services").fetchall()
    conn.close()
    return render_template("services.html", services=data)

@app.route("/add_service", methods=["GET", "POST"])
def add_service():
    if request.method == "POST":
        name = request.form["name"]
        price = request.form["price"]

        conn = get_db()
        conn.execute("INSERT INTO services (name, price) VALUES (?, ?)", (name, price))
        conn.commit()
        conn.close()

        return redirect("/services")

    return render_template("add_service.html")

@app.route("/delete_service/<int:id>")
def delete_service(id):
    conn = get_db()
    conn.execute("DELETE FROM services WHERE id=?", (id,))
    conn.commit()
    conn.close()
    return redirect("/services")

@app.route("/subscriptions")
def subscriptions():
    conn = get_db()
    data = conn.execute("""
    SELECT subscriptions.id, clients.full_name, services.name, start_date, status
    FROM subscriptions
    JOIN clients ON clients.id = subscriptions.client_id
    JOIN services ON services.id = subscriptions.service_id
    """).fetchall()
    conn.close()
    return render_template("subscriptions.html", subs=data)

@app.route("/edit_client/<int:id>", methods=["GET", "POST"])
def edit_client(id):
    conn = get_db()

    if request.method == "POST":
        name = request.form["name"]
        phone = request.form["phone"]

        conn.execute(
            "UPDATE clients SET full_name=?, phone=? WHERE id=?",
            (name, phone, id)
        )
        conn.commit()
        conn.close()
        return redirect("/clients")

    client = conn.execute("SELECT * FROM clients WHERE id=?", (id,)).fetchone()
    conn.close()

    return render_template("edit_client.html", client=client)


@app.route("/payments")
def payments():
    conn = get_db()
    data = conn.execute("""
    SELECT payments.id, clients.full_name, amount, date
    FROM payments
    JOIN clients ON clients.id = payments.client_id
    """).fetchall()
    conn.close()
    return render_template("payments.html", payments=data)


@app.route("/add_payment", methods=["GET", "POST"])
def add_payment():
    conn = get_db()

    if request.method == "POST":
        client_id = request.form["client_id"]
        amount = request.form["amount"]
        date = request.form["date"]

        conn.execute(
            "INSERT INTO payments (client_id, amount, date) VALUES (?, ?, ?)",
            (client_id, amount, date)
        )
        conn.commit()
        conn.close()
        return redirect("/payments")

    clients = conn.execute("SELECT * FROM clients").fetchall()
    conn.close()

    return render_template("add_payment.html", clients=clients)


@app.route("/add_subscription", methods=["GET", "POST"])
def add_subscription():
    conn = get_db()

    if request.method == "POST":
        client_id = request.form["client_id"]
        service_id = request.form["service_id"]
        date = request.form["date"]

        conn.execute(
            "INSERT INTO subscriptions (client_id, service_id, start_date, status) VALUES (?, ?, ?, 'Активна')",
            (client_id, service_id, date)
        )
        conn.commit()
        conn.close()
        return redirect("/subscriptions")

    clients = conn.execute("SELECT * FROM clients").fetchall()
    services = conn.execute("SELECT * FROM services").fetchall()
    conn.close()

    return render_template("add_subscription.html", clients=clients, services=services)

# ---------- ЗАПУСК ----------
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
