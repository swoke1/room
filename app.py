from flask import Flask, request, redirect, make_response
import sqlite3
import datetime
import os

app = Flask(__name__)

# ---------- STYLE ----------
STYLE = """
<style>

body{
    background:#1e1f22;
    color:white;
    font-family:Arial;
    padding:20px;
}

.card{
    background:#2b2d31;
    padding:20px;
    border-radius:15px;
    margin-bottom:20px;
    max-width:600px;
}

input{
    background:#1e1f22;
    border:1px solid #555;
    color:white;
    padding:10px;
    border-radius:10px;
    width:250px;
}

button{
    background:#5865f2;
    color:white;
    border:none;
    padding:10px;
    border-radius:10px;
    cursor:pointer;
}

button:hover{
    opacity:0.9;
}

a{
    color:#58a6ff;
    text-decoration:none;
}

.chat{
    height:300px;
    overflow:auto;
    background:#1e1f22;
    padding:10px;
    border-radius:10px;
}

.msg{
    background:#313338;
    padding:10px;
    border-radius:10px;
    margin-bottom:10px;
}

</style>
"""

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

db.execute("""
CREATE TABLE IF NOT EXISTS friends (
    user1 TEXT,
    user2 TEXT
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

        return STYLE + """
        <div class="card">

        <h1>💬 Messenger</h1>

        <form action="/login" method="POST">

            <input name="username" placeholder="username"><br><br>

            <input
                name="password"
                type="password"
                placeholder="password"
            ><br><br>

            <button>Login / Register</button>

        </form>

        </div>
        """

    me = current_user()

    return STYLE + f"""
    <div class="card">

    <h1>💬 Messenger</h1>

    <h3>Hi, {me} 👋</h3>

    <hr>

    <h2>🔎 Find Friend</h2>

    <form action="/find">

        <input name="q" placeholder="username">

        <button>Search</button>

    </form>

    <br>

    <a href="/friends">
    <button>🧑‍🤝‍🧑 Open Friends</button>
    </a>

    <br><br>

    <a href="/logout">Logout</a>

    </div>
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
            return STYLE + "<div class='card'><h2>❌ Wrong password</h2></div>"

    else:

        try:

            db.execute(
                "INSERT INTO users VALUES (?, ?)",
                (username, password)
            )

            conn.commit()

        except:
            return STYLE + "<div class='card'><h2>❌ Username already exists</h2></div>"

    response = make_response(redirect("/"))

    response.set_cookie("user", username)

    return response


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

    html = STYLE + '<div class="card"><h1>🔎 Results</h1>'

    if not results:
        html += "<p>❌ No users found</p>"

    for r in results:

        username = r[0]

        if username != me:

            html += f"""

            <div class="msg">

            👤 {username}

            <a href="/add_friend/{username}">
                <button>Add Friend</button>
            </a>

            </div>
            """
            html += '<br><a href="/">⬅ Back</a></div>'

    return html


# ---------- ADD FRIEND ----------
@app.route("/add_friend/<username>")
def add_friend(username):

    me = current_user()

    if not me:
        return redirect("/")

    db.execute(
        "SELECT * FROM friends WHERE user1=? AND user2=?",
        (me, username)
    )

    exists = db.fetchone()

    if not exists:

        db.execute(
            "INSERT INTO friends VALUES (?, ?)",
            (me, username)
        )

        conn.commit()

    return redirect("/friends")


# ---------- FRIENDS ----------
@app.route("/friends")
def friends():

    me = current_user()

    if not me:
        return redirect("/")

    db.execute(
        "SELECT user2 FROM friends WHERE user1=?",
        (me,)
    )

    friends = db.fetchall()

    html = STYLE + '<div class="card"><h1>🧑‍🤝‍🧑 Friends</h1>'

    if not friends:
        html += "<p>No friends yet</p>"

    for f in friends:

        username = f[0]

        html += f"""

        <div class="msg">

        👤 <a href="/chat?to={username}">
            {username}
        </a>

        </div>
        """

    html += '<br><a href="/">⬅ Back</a></div>'

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

        <div class="msg">

        <b>{sender}</b>

        [{time}]

        <br><br>

        {msg}

        </div>
        """

    return STYLE + f"""

    <div class="card">

    <h1>💬 {target}</h1>

    <div class="chat">

        {html}

    </div>

    <br>

    <form action="/send" method="POST">

        <input type="hidden" name="to" value="{target}">

        <input name="msg" placeholder="message">

        <button>Send</button>

    </form>

    <br>

    <a href="/friends">⬅ Back</a>

    </div>
    """


# ---------- SEND ----------
@app.route("/send", methods=["POST"])
def send():

    me = current_user()

    if not me:
        return redirect("/")

    target = request.form["to"]

    msg = request.form["msg"]

    if not msg:
        return redirect(f"/chat?to={target}")

    now = datetime.datetime.now().strftime("%H:%M")

    db.execute(
        "INSERT INTO messages VALUES (?, ?, ?, ?)",
        (me, target, msg, now)
    )

    conn.commit()

    return redirect(f"/chat?to={target}")


# ---------- LOGOUT ----------
@app.route("/logout")
def logout():

    response = make_response(redirect("/"))

    response.set_cookie("user", "", expires=0)

    return response


# ---------- RUN ----------
if __name__ == "__main__":

    port = int(os.environ.get("PORT", 8000))

    app.run(
        host="0.0.0.0",
        port=port
    )
