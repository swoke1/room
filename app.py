from flask import Flask, request, redirect, make_response
import sqlite3
import datetime

app = Flask(__name__)

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


def user():
    return request.cookies.get("user")


# ---------------- HOME ----------------
@app.route("/")
def home():
    if not user():
        return """
        <h2>Login</h2>
        <form action="/login" method="POST">
            <input name="username" placeholder="username"><br><br>
            <input name="password" placeholder="password"><br><br>
            <button>login</button>
        </form>
        """

    me = user()

    return f"""
    <h1>💬 Messenger</h1>
    <h3>Hi, {me} 👋</h3>

    <hr>

    <h2>🧑‍🤝‍🧑 Friends</h2>
    <a href="/friends">Open friends list</a>

    <h2>🔎 Find friend</h2>
    <form action="/find" method="GET">
        <input name="q" placeholder="username">
        <button>search</button>
    </form>

    <br><br>
    <a href="/logout">logout</a>
    """


# ---------------- LOGIN ----------------
@app.route("/login", methods=["POST"])
def login():
    username = request.form["username"]
    password = request.form["password"]

    db.execute("SELECT * FROM users WHERE username=?", (username,))
    u = db.fetchone()

    if u:
        if u[1] != password:
            return "Wrong password"
    else:
        try:
            db.execute("INSERT INTO users VALUES (?, ?)", (username, password))
            conn.commit()
        except:
            return "Username already taken"

    resp = make_response(redirect("/"))
    resp.set_cookie("user", username)
    return resp


# ---------------- FRIENDS ----------------
@app.route("/friends")
def friends():
    me = user()
    if not me:
        return redirect("/")

    db.execute("SELECT username FROM users")
    users = db.fetchall()

    html = "<h2>🧑‍🤝‍🧑 Friends</h2>"

    for u in users:
        if u[0] != me:
            html += f'<p>👤 <a href="/chat?to={u[0]}">{u[0]}</a></p>'

    html += "<br><a href='/'>⬅ back</a>"

    return html


# ---------------- FIND ----------------
@app.route("/find")
def find():
    me = user()
    if not me:
        return redirect("/")

    q = request.args.get("q")

    db.execute("SELECT username FROM users WHERE username LIKE ?", (f"%{q}%",))
    results = db.fetchall()

    if not results:
        return "<h3>No users found ❌</h3><a href='/'>back</a>"

    html = "<h2>🔎 Results</h2>"

    for r in results:
        if r[0] != me:
            html += f'<p>👤 <a href="/chat?to={r[0]}">{r[0]}</a></p>'

    html += "<br><a href='/'>⬅ back</a>"

    return html


# ---------------- CHAT ----------------
@app.route("/chat")
def chat():
    me = user()
    to = request.args.get("to")

    if not me:
        return redirect("/")

    db.execute("""
        SELECT sender, message, time FROM messages
        WHERE (sender=? AND receiver=?)
        OR (sender=? AND receiver=?)
        ORDER BY rowid
    """, (me, to, to, me))

    msgs = db.fetchall()

    html = ""
    for s, m, t in msgs:
        html += f"<div><b>{s}</b> [{t}]: {m}</div>"

    return f"""
    <h2>💬 Chat with {to}</h2>

    <div style="height:300px;overflow:auto;border:1px solid #ccc;padding:10px;">
        {html}
    </div>

    <form action="/send" method="POST">
        <input type="hidden" name="to" value="{to}">
        <input name="msg" placeholder="message">
        <button>send</button>
    </form>

    <br>
    <a href="/">⬅ back</a>
    """


# ---------------- SEND ----------------
@app.route("/send", methods=["POST"])
def send():
    me = user()
    to = request.form["to"]
    msg = request.form["msg"]

    now = datetime.datetime.now().strftime("%H:%M")

    db.execute(
