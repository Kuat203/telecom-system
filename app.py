from flask import Flask, render_template, request, redirect
import sqlite3
import os

app = Flask(__name__)

def get_db():
    conn = sqlite3.connect("database.db")
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = sqlite3.connect("database.db")
    c = conn.cursor()

    c.execute("""
    CREATE TABLE IF NOT EXISTS clients (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        full_name TEXT,
        phone TEXT
    )
    """)

    c.execute("""
    CREATE TABLE IF NOT EXISTS tariffs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT,
        type TEXT,
        speed INTEGER,
        channels INTEGER,
        price INTEGER
    )
    """)

    c.execute("""
    CREATE TABLE IF NOT EXISTS subscriptions (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        client_id INTEGER,
        tariff_id INTEGER,
        start_date TEXT,
        status TEXT,
        balance INTEGER DEFAULT 0
    )
    """)

    c.execute("""
    CREATE TABLE IF NOT EXISTS payments (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        client_id INTEGER,
        amount INTEGER,
        date TEXT
    )
    """)

    conn.commit()
    conn.close()


# ❗ ОДИН РАЗ оставить, потом удалить
if os.path.exists("database.db"):
    os.remove("database.db")

init_db()


# ---------------- ГЛАВНАЯ ----------------
@app.route("/")
def index():
    db = get_db()

    clients = db.execute("SELECT COUNT(*) FROM clients").fetchone()[0]
    subs = db.execute("SELECT COUNT(*) FROM subscriptions").fetchone()[0]
    income = db.execute("SELECT IFNULL(SUM(amount),0) FROM payments").fetchone()[0]

    db.close()

    return render_template("index.html", clients=clients, subs=subs, income=income)


# ---------------- КЛИЕНТЫ ----------------
@app.route("/clients")
def clients():
    db = get_db()
    data = db.execute("SELECT * FROM clients").fetchall()
    db.close()
    return render_template("clients.html", clients=data)


@app.route("/add_client", methods=["GET", "POST"])
def add_client():
    if request.method == "POST":
        db = get_db()
        db.execute("INSERT INTO clients (full_name, phone) VALUES (?, ?)",
                   (request.form["name"], request.form["phone"]))
        db.commit()
        db.close()
        return redirect("/clients")

    return render_template("add_client.html")


# ---------------- ТАРИФЫ ----------------
@app.route("/tariffs")
def tariffs():
    db = get_db()
    data = db.execute("SELECT * FROM tariffs").fetchall()
    db.close()
    return render_template("tariffs.html", tariffs=data)


@app.route("/add_tariff", methods=["GET", "POST"])
def add_tariff():
    if request.method == "POST":
        db = get_db()
        db.execute("""
        INSERT INTO tariffs (name, type, speed, channels, price)
        VALUES (?, ?, ?, ?, ?)
        """, (
            request.form["name"],
            request.form["type"],
            request.form["speed"],
            request.form["channels"],
            request.form["price"]
        ))
        db.commit()
        db.close()
        return redirect("/tariffs")

    return render_template("add_tariff.html")


# ---------------- ПОДКЛЮЧЕНИЯ ----------------
@app.route("/subscriptions")
def subscriptions():
    db = get_db()

    data = db.execute("""
    SELECT s.id, c.full_name, t.name, t.price, s.balance, s.status
    FROM subscriptions s
    JOIN clients c ON c.id = s.client_id
    JOIN tariffs t ON t.id = s.tariff_id
    """).fetchall()

    db.close()
    return render_template("subscriptions.html", subs=data)


@app.route("/add_subscription", methods=["GET", "POST"])
def add_subscription():
    db = get_db()

    if request.method == "POST":
        db.execute("""
        INSERT INTO subscriptions (client_id, tariff_id, start_date, status, balance)
        VALUES (?, ?, date('now'), 'Активна', 0)
        """, (
            request.form["client_id"],
            request.form["tariff_id"]
        ))

        db.commit()
        db.close()
        return redirect("/subscriptions")

    clients = db.execute("SELECT * FROM clients").fetchall()
    tariffs = db.execute("SELECT * FROM tariffs").fetchall()
    db.close()

    return render_template("add_subscription.html", clients=clients, tariffs=tariffs)

@app.route("/activate/<int:id>")
def activate(id):
    db = get_db()
    db.execute("UPDATE subscriptions SET status='Активна' WHERE id=?", (id,))
    db.commit()
    db.close()
    return redirect("/subscriptions")

@app.route("/deactivate/<int:id>")
def deactivate(id):
    db = get_db()
    db.execute("UPDATE subscriptions SET status='Отключена' WHERE id=?", (id,))
    db.commit()
    db.close()
    return redirect("/subscriptions")


# начисление
@app.route("/charge")
def charge():
    db = get_db()

    subs = db.execute("SELECT id, tariff_id FROM subscriptions").fetchall()

    for s in subs:
        price = db.execute("SELECT price FROM tariffs WHERE id=?", (s["tariff_id"],)).fetchone()[0]
        db.execute("UPDATE subscriptions SET balance = balance - ? WHERE id=?", (price, s["id"]))

    db.commit()
    db.close()

    return redirect("/subscriptions")


# ---------------- ПЛАТЕЖИ ----------------
@app.route("/payments")
def payments():
    db = get_db()
    data = db.execute("""
    SELECT p.id, c.full_name, p.amount, p.date
    FROM payments p
    JOIN clients c ON c.id = p.client_id
    """).fetchall()
    db.close()
    return render_template("payments.html", payments=data)


@app.route("/add_payment", methods=["GET", "POST"])
def add_payment():
    db = get_db()

    if request.method == "POST":
        client_id = request.form["client_id"]
        amount = int(request.form["amount"])

        db.execute("INSERT INTO payments (client_id, amount, date) VALUES (?, ?, date('now'))",
                   (client_id, amount))

        db.execute("UPDATE subscriptions SET balance = balance + ? WHERE client_id=?",
                   (amount, client_id))

        db.commit()
        db.close()

        return redirect("/payments")

    clients = db.execute("SELECT * FROM clients").fetchall()
    db.close()

    return render_template("add_payment.html", clients=clients)


# ---------------- СТАТИСТИКА ----------------
@app.route("/stats")
def stats():
    db = get_db()

    data = db.execute("""
    SELECT date, SUM(amount) as total
    FROM payments
    GROUP BY date
    """).fetchall()

    db.close()

    dates = [row["date"] for row in data]
    totals = [row["total"] for row in data]

    return render_template("stats.html", dates=dates, totals=totals)


# ---------------- ЗАПУСК ----------------
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
