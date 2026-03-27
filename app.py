import sqlite3
from flask import Flask, send_from_directory, request, redirect, render_template

app = Flask(__name__)

# ---------- DATABASE ----------
def init_db():
    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()
    
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT,
        phone TEXT,
        email TEXT,
        role TEXT,
        password TEXT
    )
    ''')
    
    conn.commit()
    conn.close()


# ---------- DASHBOARD ----------
@app.route('/dashboard.html')
def dashboard_page():
    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()

    cursor.execute("SELECT COUNT(*) FROM users WHERE role='Electrician'")
    total_users = cursor.fetchone()[0]

    conn.close()

    return render_template("dashboard.html", total_users=total_users)


# ---------- ELECTRICIANS (DYNAMIC) ----------
@app.route('/electricians.html')
def electricians_page():
    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()

    cursor.execute("SELECT id, name, phone, email FROM users WHERE role='Electrician'")
    electricians = cursor.fetchall()

    conn.close()

    return render_template("electricians.html", electricians=electricians)


# ---------- STATIC PAGES ----------
@app.route('/')
def home():
    return send_from_directory('.', 'index.html')

@app.route('/login.html')
def login_page():
    return send_from_directory('.', 'login.html')

@app.route('/register.html')
def register_page():
    return send_from_directory('.', 'register.html')

@app.route('/jobs.html')
def jobs_page():
    return send_from_directory('.', 'jobs.html')

@app.route('/tasks.html')
def tasks_page():
    return send_from_directory('.', 'tasks.html')

@app.route('/materials.html')
def materials_page():
    return send_from_directory('.', 'materials.html')

@app.route('/reports.html')
def reports_page():
    return send_from_directory('.', 'reports.html')

@app.route('/profile.html')
def profile_page():
    return send_from_directory('.', 'profile.html')


# ---------- REGISTER ----------
@app.route('/register', methods=['POST'])
def register():
    name = request.form['name']
    phone = request.form['phone']
    email = request.form['email']
    role = request.form['role']
    password = request.form['password']

    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()

    cursor.execute(
        "INSERT INTO users (name, phone, email, role, password) VALUES (?, ?, ?, ?, ?)",
        (name, phone, email, role, password)
    )

    conn.commit()
    conn.close()

    return redirect('/login.html')


# ---------- LOGIN ----------
@app.route('/login', methods=['POST'])
def login():
    email = request.form['email']
    password = request.form['password']

    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM users WHERE email=? AND password=?", (email, password))
    user = cursor.fetchone()

    conn.close()

    if user:
        return redirect('/dashboard.html')
    else:
        return "Invalid Email or Password"
    
@app.route('/delete/<int:id>')
def delete_user(id):
    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()

    cursor.execute("DELETE FROM users WHERE id=?", (id,))

    conn.commit()
    conn.close()

    return redirect('/electricians.html')


# ---------- RUN ----------
if __name__ == '__main__':
    init_db()
    app.run(debug=True)