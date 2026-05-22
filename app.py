from flask import Flask, request, redirect, make_response
import sqlite3
import datetime
import os

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


def current_user():
    return request.cookies.get("user")


@app.route("/")
def home():

    if not current_user():

        return '''
        <h1>Messenger</h1>

        <form action="/login" method="POST">

            <input name="username" placeholder="username"><br><br>

            <input name="password" type="password" placeholder="password"><br><br>

            <button>Login / Register</button>

        </form>
        '''

    me = current_user()

    return f'''
    <h1>Messenger</h1>

    <h3>Hi, {me}</h3>

    <hr>

    <h2>Friends</h2>

    <a href="/friends">Open friends list</a>

    <br><br>

    <h2>Find friend</h2>

    <form action="/find">

        <input name="q" placeholder="username">

        <button>Find</button>

    </form>

    <br><br>

    <a href="/logout">Logout</a>
    '''


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
            return "Wrong password"

    else:

        try:

            db.execute(
                "INSERT INTO users VALUES (?, ?)",
                (username, password)
            )

            conn.commit()

        except:
            return "Username already exists"

    response = make_response(redirect("/"))

    response.set_cookie("user", username)

    return response


@app.route("/friends")
def friends():

    me = current_user()

    if not me:
        return redirect("/")

    db.execute("SELECT username FROM users")

    users = db.fetchall()

    html = "<h1>Friends</h1>"

    for u in users:

        username = u[0]

        if username != me:

            html += f'''
            <p>
                <a href="/chat?to={username}">
                    {username}
                </a>
            </p>
            '''

    html += '<br><a href="/">Back</a>'

    return html


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
        return '''
        <h2>User not found</h2>
        <a href="/">Back</a>
        '''

    html = "<h1>Results</h1>"

    for r in results:

        username = r[0]

        if username != me:

            html += f'''
            <p>
                <a href="/chat?to={username}">
                    {username}
                </a>
            </p>
            '''

    html += '<br><a href="/">Back</a>'

    return html


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

        html += f'''
        <p>
            <b>{sender}</b>
            [{time}]
            : {msg}
        </p>
        '''

    return f'''
    <h1>Chat with {target}</h1>

    <div style="
        border:1px solid black;
        height:300px;
        overflow:auto;
        padding:10px;
    ">

        {html}

    </div>

    <br>

    <form action="/send" method="POST">
    <input type="hidden" name="to" value="{target}">

        <input name="msg" placeholder="message">

        <button>Send</button>

    </form>

    <br>

    <a href="/">Back</a>
    '''


@app.route("/send", methods=["POST"])
def send():

    me = current_user()

    if not me:
        return redirect("/")

    target = request.form["to"]

    msg = request.form["msg"]

    now = datetime.datetime.now().strftime("%H:%M")

    db.execute(
        "INSERT INTO messages VALUES (?, ?, ?, ?)",
        (me, target, msg, now)
    )

    conn.commit()

    return redirect(f"/chat?to={target}")


@app.route("/logout")
def logout():

    response = make_response(redirect("/"))

    response.set_cookie("user", "", expires=0)

    return response


if __name__ == "__main__":

    port = int(os.environ.get("PORT", 8000))

    app.run(
        host="0.0.0.0",
        port=port
    )
