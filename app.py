import sqlite3
from flask import Flask, send_from_directory, request, redirect, render_template
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)

# ---------- DATABASE ----------
def init_db():
    conn = sqlite3.connect("database.db")
    cursor = conn.cursor()

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT,
        phone TEXT,
        email TEXT,
        role TEXT,
        password TEXT
    )
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS jobs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        title TEXT,
        description TEXT,
        electrician_id INTEGER,
        status TEXT
    )
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS tasks (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        job_id INTEGER,
        task_name TEXT,
        status TEXT
    )
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS materials (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT,
        quantity INTEGER
    )
    """)

    conn.commit()
    conn.close()


# ---------- REGISTER (UPDATED) ----------
@app.route('/register', methods=['POST'])
def register():
    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()

    password = generate_password_hash(request.form['password'])

    cursor.execute(
        "INSERT INTO users (name, phone, email, role, password) VALUES (?, ?, ?, ?, ?)",
        (
            request.form['name'],
            request.form['phone'],
            request.form['email'],
            request.form['role'],
            password
        )
    )

    conn.commit()
    conn.close()

    return redirect('/login.html')


# ---------- LOGIN (UPDATED) ----------
@app.route('/login', methods=['POST'])
def login():
    email = request.form['email']
    password = request.form['password']

    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM users WHERE email=?", (email,))
    user = cursor.fetchone()

    conn.close()

    if user and check_password_hash(user[5], password):

        role = user[4]

        if role == "Admin":
            return redirect('/dashboard.html')
        else:
            return redirect('/tasks')

    else:
        return "Invalid Email or Password"


# ---------- DASHBOARD ----------
@app.route('/dashboard.html')
def dashboard_page():
    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()

    cursor.execute("SELECT COUNT(*) FROM users WHERE role='Electrician'")
    total_users = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM jobs")
    total_jobs = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM tasks WHERE status='Pending'")
    pending_tasks = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM tasks WHERE status='Completed'")
    completed_tasks = cursor.fetchone()[0]

    conn.close()

    return render_template("dashboard.html",
                           total_users=total_users,
                           total_jobs=total_jobs,
                           pending_tasks=pending_tasks,
                           completed_tasks=completed_tasks)


# ---------- ELECTRICIANS ----------
@app.route('/electricians.html')
def electricians_page():
    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()

    # FIX: make role check case-insensitive
    cursor.execute("""
        SELECT id, name, phone, email 
        FROM users 
        WHERE LOWER(role) = 'electrician'
    """)
    
    electricians = cursor.fetchall()

    conn.close()

    return render_template("electricians.html", electricians=electricians)


@app.route('/delete/<int:id>')
def delete_user(id):
    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()

    cursor.execute("DELETE FROM users WHERE id=?", (id,))
    conn.commit()
    conn.close()

    return redirect('/electricians.html')


# ---------- JOBS ----------
def get_electricians():
    conn = sqlite3.connect("database.db")
    cursor = conn.cursor()
    cursor.execute("SELECT id, name FROM users WHERE role='Electrician'")
    electricians = cursor.fetchall()
    conn.close()
    return electricians


@app.route('/jobs')
def jobs():
    conn = sqlite3.connect("database.db")
    cursor = conn.cursor()

    cursor.execute("""
        SELECT jobs.id, jobs.title, jobs.description, jobs.status, users.name
        FROM jobs
        LEFT JOIN users ON jobs.electrician_id = users.id
    """)

    jobs = cursor.fetchall()
    conn.close()

    return render_template('jobs.html', jobs=jobs, electricians=get_electricians())


@app.route('/add_job', methods=['POST'])
def add_job():
    conn = sqlite3.connect("database.db")
    cursor = conn.cursor()

    cursor.execute(
        "INSERT INTO jobs (title, description, electrician_id, status) VALUES (?, ?, ?, ?)",
        (request.form['title'], request.form['description'], request.form['electrician_id'], "Pending")
    )

    conn.commit()
    conn.close()

    return redirect('/jobs')


# ---------- TASKS ----------
@app.route('/tasks')
def tasks():
    conn = sqlite3.connect("database.db")
    cursor = conn.cursor()

    cursor.execute("""
        SELECT tasks.id, tasks.task_name, tasks.status, jobs.title
        FROM tasks
        LEFT JOIN jobs ON tasks.job_id = jobs.id
    """)
    tasks = cursor.fetchall()

    cursor.execute("SELECT id, title FROM jobs")
    jobs = cursor.fetchall()

    conn.close()

    return render_template('tasks.html', tasks=tasks, jobs=jobs)


@app.route('/add_task', methods=['POST'])
def add_task():
    conn = sqlite3.connect("database.db")
    cursor = conn.cursor()

    cursor.execute(
        "INSERT INTO tasks (job_id, task_name, status) VALUES (?, ?, ?)",
        (request.form['job_id'], request.form['task_name'], "Pending")
    )

    conn.commit()
    conn.close()

    return redirect('/tasks')


# ---------- MATERIALS ----------
@app.route('/materials')
def materials():
    conn = sqlite3.connect("database.db")
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM materials")
    materials = cursor.fetchall()

    conn.close()

    return render_template('materials.html', materials=materials)


@app.route('/add_material', methods=['POST'])
def add_material():
    conn = sqlite3.connect("database.db")
    cursor = conn.cursor()

    cursor.execute(
        "INSERT INTO materials (name, quantity) VALUES (?, ?)",
        (request.form['name'], request.form['quantity'])
    )

    conn.commit()
    conn.close()

    return redirect('/materials')


# ---------- REPORTS ----------
@app.route('/reports')
def reports():
    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()

    cursor.execute("SELECT COUNT(*) FROM users WHERE role='Electrician'")
    total_users = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM jobs")
    total_jobs = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM tasks WHERE status='Pending'")
    pending_tasks = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM tasks WHERE status='Completed'")
    completed_tasks = cursor.fetchone()[0]

    conn.close()

    return render_template("reports.html",
                           total_users=total_users,
                           total_jobs=total_jobs,
                           pending_tasks=pending_tasks,
                           completed_tasks=completed_tasks)


# ---------- STATIC ----------
@app.route('/')
def home():
    return send_from_directory('.', 'index.html')

@app.route('/login.html')
def login_page():
    return send_from_directory('.', 'login.html')

@app.route('/register.html')
def register_page():
    return send_from_directory('.', 'register.html')


# ---------- RUN ----------
if __name__ == "__main__":
    init_db()
    app.run(debug=True)