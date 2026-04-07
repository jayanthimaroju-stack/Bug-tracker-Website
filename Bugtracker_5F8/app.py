from flask import Flask, render_template, request, redirect, session, url_for
import sqlite3

app = Flask(__name__)
app.secret_key = "secret_key"

# ---------------- DATABASE ----------------

def get_db():
    conn = sqlite3.connect("users.db")
    conn.row_factory = sqlite3.Row
    return conn

def create_tables():
    conn = get_db()
    cursor = conn.cursor()

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS users(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE,
        password TEXT
    )
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS bugs(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        title TEXT,
        description TEXT,
        assigned_to TEXT,
        status TEXT,
        priority TEXT
    )
    """)

    conn.commit()
    conn.close()

# ---------------- INDEX ----------------

@app.route("/")
def index():
    return render_template("index.html")

# ---------------- REGISTER ----------------

@app.route("/register", methods=["GET", "POST"])
def register():

    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]

        try:
            conn = get_db()
            conn.execute(
                "INSERT INTO users(username,password) VALUES(?,?)",
                (username, password)
            )
            conn.commit()
            conn.close()

            return redirect(url_for("login"))

        except:
            return "Username already exists"

    return render_template("register.html")

# ---------------- LOGIN ----------------

@app.route("/login", methods=["GET", "POST"])
def login():

    if request.method == "POST":

        username = request.form["username"]
        password = request.form["password"]

        conn = get_db()

        user = conn.execute(
            "SELECT * FROM users WHERE username=? AND password=?",
            (username, password)
        ).fetchone()

        conn.close()

        if user:
            session["user"] = username
            return redirect(url_for("home"))
        else:
            return "Invalid credentials"

    return render_template("login.html")

# ---------------- HOME ----------------

@app.route("/home")
def home():

    if "user" not in session:
        return redirect(url_for("login"))

    return render_template("home.html", user=session["user"])

# ---------------- ADD BUG ----------------

@app.route("/add_bug", methods=["GET", "POST"])
def add_bug():

    if "user" not in session:
        return redirect(url_for("login"))

    if request.method == "POST":

        title = request.form["title"]
        description = request.form["description"]
        assigned_to = request.form["assigned_to"]
        status = request.form["status"]
        priority = request.form["priority"]

        conn = get_db()

        conn.execute("""
        INSERT INTO bugs(title,description,assigned_to,status,priority)
        VALUES(?,?,?,?,?)
        """, (title, description, assigned_to, status, priority))

        conn.commit()
        conn.close()

        return redirect(url_for("view_bugs"))

    return render_template("add_bug.html")

# ---------------- VIEW BUGS ----------------

@app.route("/view_bugs")
def view_bugs():

    if "user" not in session:
        return redirect(url_for("login"))

    conn = get_db()

    bugs = conn.execute("SELECT * FROM bugs").fetchall()

    total = len(bugs)
    open_bugs = len([b for b in bugs if b["status"] == "Open"])
    closed = len([b for b in bugs if b["status"] == "Closed"])

    conn.close()

    return render_template(
        "view_bugs.html",
        bugs=bugs,
        total=total,
        open_bugs=open_bugs,
        closed=closed
    )

# ---------------- DASHBOARD ----------------

@app.route("/dashboard")
def dashboard():

    if "user" not in session:
        return redirect(url_for("login"))

    conn = get_db()

    total = conn.execute(
        "SELECT COUNT(*) FROM bugs"
    ).fetchone()[0]

    open_bugs = conn.execute(
        "SELECT COUNT(*) FROM bugs WHERE status='Open'"
    ).fetchone()[0]

    closed = conn.execute(
        "SELECT COUNT(*) FROM bugs WHERE status='Closed'"
    ).fetchone()[0]

    conn.close()

    return render_template(
        "dashboard.html",
        total=total,
        open_bugs=open_bugs,
        closed=closed
    )

# ---------------- TOGGLE ----------------

@app.route("/toggle/<int:id>")
def toggle(id):

    if "user" not in session:
        return redirect(url_for("login"))

    conn = get_db()

    bug = conn.execute(
        "SELECT status FROM bugs WHERE id=?",
        (id,)
    ).fetchone()

    new_status = "Closed" if bug["status"] == "Open" else "Open"

    conn.execute(
        "UPDATE bugs SET status=? WHERE id=?",
        (new_status, id)
    )

    conn.commit()
    conn.close()

    return redirect(url_for("view_bugs"))

# ---------------- DELETE ----------------

@app.route("/delete_bug/<int:id>")
def delete_bug(id):

    if "user" not in session:
        return redirect(url_for("login"))

    conn = get_db()

    conn.execute(
        "DELETE FROM bugs WHERE id=?",
        (id,)
    )

    conn.commit()
    conn.close()

    return redirect(url_for("view_bugs"))

# ---------------- LOGOUT ----------------

@app.route("/logout")
def logout():

    session.pop("user", None)
    return redirect(url_for("login"))

# ---------------- RUN ----------------

if __name__ == "__main__":
    create_tables()
    app.run(debug=True)