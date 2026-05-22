from flask import Flask, request, redirect, make_response
import sqlite3
import datetime
import os

app = Flask(__name__)

# ---------- DATABASE ----------
conn = sqlite3.connect("db.db", check_same_thread=False)
db = conn.cursor()

db.execute("""
CREATE TABLE IF NOT EXISTS users (
    username TEXT UNIQUE,
    password TEXT
)
""")

db.execute("""
CREATE TABLE IF NOT EXISTS messages (
    sender TEXT,
    receiver TEXT,
    message TEXT,
    time TEXT
)
""")

conn.commit()


# ---------- USER ----------
def current_user():
    return request.cookies.get("user")


# ---------- HOME ----------
@app.route("/")
def home():

    if not current_user():

        return """
        <h1>💬 Messenger</h1>

        <form action="/login" method="POST">

            <input name="username" placeholder="username"><br><br>

            <input name="password" type="password" placeholder="password"><br><br>

            <button>Login / Register</button>

        </form>
        """

    me = current_user()

    return f"""
    <h1>💬 Messenger</h1>

    <h3>Hi, {me} 👋</h3>

    <hr>

    <h2>🧑‍🤝‍🧑 Friends</h2>

    <a href="/friends">Open friends list</a>

    <br><br>

    <h2>🔎 Find friend</h2>

    <form action="/find">

        <input name="q" placeholder="username">

        <button>Find</button>

    </form>

    <br><br>

    <a href="/logout">Logout</a>
    """


# ---------- LOGIN ----------
@app.route("/login", methods=["POST"])
def login():

    username = request.form["username"]
    password = request.form["password"]

    db.execute(
        "SELECT * FROM users WHERE username=?",
        (username,)
    )

    user = db.fetchone()

    if user:

        if user[1] != password:
            return "❌ Wrong password"

    else:

        try:

            db.execute(
                "INSERT INTO users VALUES (?, ?)",
                (username, password)
            )

            conn.commit()

        except:
            return "❌ Username already exists"

    response = make_response(redirect("/"))

    response.set_cookie("user", username)

    return response


# ---------- FRIENDS ----------
@app.route("/friends")
def friends():

    me = current_user()

    if not me:
        return redirect("/")

    db.execute("SELECT username FROM users")

    users = db.fetchall()

    html = """
    <h1>🧑‍🤝‍🧑 Friends</h1>
    """

    for u in users:

        username = u[0]

        if username != me:

            html += f"""
            👤 <a href="/chat?to={username}">
                {username}
            </a><br><br>
            """

    html += '<br><a href="/">⬅ Back</a>'

    return html


# ---------- FIND ----------
@app.route("/find")
def find():

    me = current_user()

    if not me:
        return redirect("/")

    q = request.args.get("q")

    db.execute(
        "SELECT username FROM users WHERE username LIKE ?",
        (f"%{q}%",)
    )

    results = db.fetchall()

    if not results:
        return """
        <h2>❌ User not found</h2>
        <a href="/">⬅ Back</a>
        """

    html = "<h1>🔎 Results</h1>"

    for r in results:

        username = r[0]

        if username != me:

            html += f"""
            👤 <a href="/chat?to={username}">
                {username}
            </a><br><br>
            """

    html += '<br><a href="/">⬅ Back</a>'

    return html


# ---------- CHAT ----------
@app.route("/chat")
def chat():

    me = current_user()

    if not me:
        return redirect("/")

    target = request.args.get("to")

    db.execute("""
    SELECT sender, message, time
    FROM messages
    WHERE
    (sender=? AND receiver=?)
    OR
    (sender=? AND receiver=?)
    ORDER BY rowid
    """, (me, target, target, me))

    messages = db.fetchall()

    html = ""

    for sender, msg, time in messages:

        html += f"""
        <p>
        <b>{sender}</b>
        [{time}]
        : {msg}
        </p>
        """

    return f"""
    <h1>💬 Chat with {target}</h1>
