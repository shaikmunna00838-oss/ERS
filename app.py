import os
import random
import sqlite3
from flask import Flask, render_template, request, redirect, session
from flask_mail import Mail, Message

app = Flask(__name__)
app.secret_key = "supersecretkey"

UPLOAD_FOLDER = "uploads"
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER

# ---------------- EMAIL CONFIG ---------------- #

app.config['MAIL_SERVER'] = 'smtp.gmail.com'
app.config['MAIL_PORT'] = 587
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USERNAME'] = 'shaikmunna00838@gmail.com'
app.config['MAIL_PASSWORD'] = 'idztyzwhdbdtyokl'


mail = Mail(app)


# ---------------- ADMIN LOGIN ---------------- #

ADMIN_USERNAME = "admin"
ADMIN_PASSWORD = "admin123"

@app.route("/admin", methods=["GET","POST"])
def admin_login():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]

        if username == ADMIN_USERNAME and password == ADMIN_PASSWORD:
            session["admin"] = True
            return redirect("/admin/dashboard")
        else:
            return "Invalid Credentials"

    return render_template("admin_login.html")


@app.route("/admin/dashboard")
def admin_dashboard():
    if "admin" not in session:
        return redirect("/admin")

    conn = sqlite3.connect("database.db")
    c = conn.cursor()
    c.execute("SELECT * FROM results")
    data = c.fetchall()
    conn.close()

    return render_template("admin_dashboard.html", data=data)


@app.route("/admin/logout")
def admin_logout():
    session.pop("admin", None)
    return redirect("/admin")



# ---------------- DATABASE INIT ---------------- #

def init_db():
    conn = sqlite3.connect("database.db")
    c = conn.cursor()

    c.execute("""CREATE TABLE IF NOT EXISTS applicants(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT,
        email TEXT,
        phone TEXT,
        department TEXT,
        qualification TEXT,
        certificate TEXT
    )""")

    c.execute("""CREATE TABLE IF NOT EXISTS questions(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        department TEXT,
        question TEXT,
        option1 TEXT,
        option2 TEXT,
        option3 TEXT,
        option4 TEXT,
        answer TEXT
    )""")
    
    
    c.execute("""
    CREATE TABLE IF NOT EXISTS results(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT,
        email TEXT,
        department TEXT,
        score INTEGER,
        status TEXT
    )""")

    conn.commit()
    conn.close()

init_db()

# ---------------- HOME ---------------- #

@app.route("/")
def home():
    return render_template("index.html")

# ---------------- APPLY ---------------- #

@app.route("/apply", methods=["GET", "POST"])
def apply():
    if request.method == "POST":
        name = request.form["name"]
        email = request.form["email"]
        phone = request.form["phone"]
        department = request.form["department"]
        qualification = request.form["qualification"]

        file = request.files["certificate"]
        filepath = os.path.join(app.config["UPLOAD_FOLDER"], file.filename)
        file.save(filepath)

        conn = sqlite3.connect("database.db")
        c = conn.cursor()
        c.execute("INSERT INTO applicants (name,email,phone,department,qualification,certificate) VALUES (?,?,?,?,?,?)",
                  (name,email,phone,department,qualification,filepath))
        conn.commit()
        conn.close()

        session.clear()
        session["department"] = department
        session["email"] = email
        session["name"] = name

        return redirect("/quiz")

    return render_template("apply.html")

# ---------------- QUIZ ---------------- #

@app.route("/quiz", methods=["GET", "POST"])
def quiz():
    if "department" not in session:
        return redirect("/")

    department = session["department"]
    conn = sqlite3.connect("database.db")
    c = conn.cursor()

    if request.method == "GET":
        if "questions" not in session:
            c.execute("SELECT * FROM questions WHERE department=?", (department,))
            all_questions = c.fetchall()
            selected_questions = random.sample(all_questions, 15)
            session["questions"] = selected_questions
        else:
            selected_questions = session["questions"]

        conn.close()
        return render_template("quiz.html", questions=selected_questions)

    if request.method == "POST":
        score = 0
        questions = session.get("questions", [])

        for q in questions:
            selected = request.form.get(str(q[0]))
            if selected == q[7]:
                score += 1

        session["score"] = score
        conn.close()
        return redirect("/result")

# ---------------- RESULT + EMAIL ---------------- #

@app.route("/result")
def result():
    if "score" not in session:
        return redirect("/")

    score = session["score"]
    email = session["email"]
    name = session["name"]

    if score >= 9:
        message_text = f"""
        Dear {name},

        Congratulations!
        You have cleared the online assessment.

        You will get a notification regarding the Campus Interview.

        Regards,
        Recruitment Team
        """
        display_message = "You will get a notification regarding the Campus Interview."
    else:
        message_text = f"""
        Dear {name},

        Thank you for attending the recruitment test.
        Unfortunately, you did not meet the minimum qualifying marks.

        Better luck next time.

        Regards,
        Recruitment Team
        """
        display_message = "Better luck next time."

    
    conn = sqlite3.connect("database.db")
    c = conn.cursor()

    status = "Selected" if score >= 9 else "Rejected"

    c.execute("""
    INSERT INTO results (name,email,department,score,status)
    VALUES (?,?,?,?,?)
    """, (name,email,session["department"],score,status))

    conn.commit()
    conn.close()


    # Send Email
    msg = Message(
        subject="Recruitment Test Result",
        sender=app.config['MAIL_USERNAME'],
        recipients=[email],
        body=message_text
    )

    try:
        mail.send(msg)
    except Exception as e:
        print("Email sending failed:", e)

    session.pop("questions", None)

    return render_template("result.html", message=display_message, score=score)

if __name__ == "__main__":
    app.run(debug=True)