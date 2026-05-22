from flask import Flask, request, redirect, make_response
import sqlite3
import datetime

app = Flask(__name__)

# --- DB ---
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


# --- HOME (friends list) ---
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

    db.execute("SELECT username FROM users")
    users = db.fetchall()

    html = "<h2>Friends</h2>"

    for u in users:
        if u[0] != user():
            html += f'<p><a href="/chat?to={u[0]}">{u[0]}</a></p>'

    html += '<br><a href="/logout">logout</a>'

    return f"<p>You: <b>{user()}</b></p>" + html


# --- LOGIN ---
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
            return "❌ Username already taken"

    resp = make_response(redirect("/"))
    resp.set_cookie("user", username)
    return resp


# --- CHAT ---
@app.route("/chat")
def chat():
    me = user()
    to = request.args.get("to")

    if not to:
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
    <h2>Chat with {to}</h2>

    <div style="height:300px;overflow:auto;border:1px solid black;padding:10px;">
        {html}
    </div>

    <form action="/send" method="POST">
        <input type="hidden" name="to" value="{to}">
        <input name="msg" placeholder="message">
        <button>send</button>
    </form>

    <a href="/">back</a>
    """


# --- SEND ---
@app.route("/send", methods=["POST"])
def send():
    me = user()
    to = request.form["to"]
    msg = request.form["msg"]

    now = datetime.datetime.now().strftime("%H:%M")

    db.execute(
        "INSERT INTO messages VALUES (?, ?, ?, ?)",
        (me, to, msg, now)
    )
    conn.commit()

    return redirect(f"/chat?to={to}")


# --- LOGOUT ---
@app.route("/logout")
def logout():
    resp = make_response(redirect("/"))
    resp.set_cookie("user", "", expires=0)
    return resp


# --- RUN (Railway safe) ---
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000)
