import sqlite3
import razorpay
import os

from datetime import datetime

from flask import (
    Flask,
    send_from_directory,
    request,
    redirect,
    render_template,
    send_file,
    jsonify,
    session,
    flash
)

from werkzeug.security import (
    generate_password_hash,
    check_password_hash
)

from werkzeug.utils import secure_filename

from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer
)

from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.pagesizes import letter

app = Flask(__name__)

# ---------- SECRET KEY ----------
app.secret_key = "voltiX_secret_key"

# ---------- UPLOAD FOLDER ----------
UPLOAD_FOLDER = "static/uploads"
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# ---------- RAZORPAY ----------
client = razorpay.Client(auth=(
    "rzp_test_Sot2bKh2NFbFIr",
    "Se1kdSnR7mbmDx4W7velPYFK"
))

# ---------- DATABASE ----------
def init_db():

    conn = sqlite3.connect("database.db")
    cursor = conn.cursor()

    # USERS
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT,
        phone TEXT,
        email TEXT UNIQUE,
        role TEXT,
        password TEXT,
        profile_image TEXT DEFAULT 'profile.png'
    )
    """)

    # JOBS
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS jobs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        title TEXT,
        description TEXT,
        electrician_id INTEGER,
        status TEXT
    )
    """)

    # TASKS
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS tasks (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        job_id INTEGER,
        task_name TEXT,
        status TEXT
    )
    """)

    # MATERIALS
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS materials (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT,
        quantity INTEGER
    )
    """)

    # PAYMENTS
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS payments (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        payer_name TEXT,
        amount INTEGER,
        status TEXT,
        payment_date TEXT
    )
    """)

    conn.commit()
    conn.close()

# ---------- INITIALIZE DATABASE ----------
init_db()

# ---------- REGISTER ----------
@app.route('/register', methods=['GET', 'POST'])
def register():

    if request.method == 'GET':
        return redirect('/register.html')

    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()

    email = request.form['email']

    cursor.execute(
        "SELECT * FROM users WHERE email=?",
        (email,)
    )

    existing_user = cursor.fetchone()

    if existing_user:
        conn.close()
        return "Email already exists"

    password = generate_password_hash(
        request.form['password']
    )

    cursor.execute("""
        INSERT INTO users (
            name,
            phone,
            email,
            role,
            password
        )
        VALUES (?, ?, ?, ?, ?)
    """, (
        request.form['name'],
        request.form['phone'],
        request.form['email'],
        request.form['role'],
        password
    ))

    conn.commit()
    conn.close()

    return redirect('/login.html')

# ---------- LOGIN ----------
@app.route('/login', methods=['GET', 'POST'])
def login():

    if request.method == 'GET':
        return redirect('/login.html')

    email = request.form['email']
    password = request.form['password']

    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()

    cursor.execute(
        "SELECT * FROM users WHERE email=?",
        (email,)
    )

    user = cursor.fetchone()

    conn.close()

    if user and check_password_hash(user[5], password):

        session['user'] = user[1]
        session['role'] = user[4]
        session['user_id'] = user[0]

        role = user[4]

        if role.lower() == "admin":
            return redirect('/dashboard.html')

        else:
            return redirect('/tasks')

    else:
        return "Invalid Email or Password"
# ---------- LOGOUT ----------
@app.route('/logout')
def logout():

    session.clear()

    flash("Logged Out Successfully")

    return redirect('/login.html')

# ---------- DASHBOARD ----------
@app.route('/dashboard.html')
def dashboard_page():

    if 'user' not in session:
        return redirect('/login.html')

    if session['role'].lower() != "admin":
        return redirect('/tasks')

    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()

    cursor.execute("""
        SELECT COUNT(*)
        FROM users
        WHERE LOWER(role)='electrician'
    """)
    total_users = cursor.fetchone()[0]

    cursor.execute("""
        SELECT COUNT(*)
        FROM jobs
    """)
    total_jobs = cursor.fetchone()[0]

    cursor.execute("""
        SELECT COUNT(*)
        FROM tasks
        WHERE status='Pending'
    """)
    pending_tasks = cursor.fetchone()[0]

    cursor.execute("""
        SELECT COUNT(*)
        FROM tasks
        WHERE status='Completed'
    """)
    completed_tasks = cursor.fetchone()[0]

    conn.close()

    return render_template(
        "dashboard.html",
        total_users=total_users,
        total_jobs=total_jobs,
        pending_tasks=pending_tasks,
        completed_tasks=completed_tasks
    )

# ---------- ELECTRICIANS ----------
@app.route('/electricians.html')
def electricians_page():

    if 'user' not in session:
        return redirect('/login.html')

    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()

    search = request.args.get('search', '')

    cursor.execute("""
        SELECT id, name, phone, email
        FROM users
        WHERE LOWER(role)='electrician'
        AND name LIKE ?
    """, ('%' + search + '%',))

    electricians = cursor.fetchall()

    conn.close()

    return render_template(
        "electricians.html",
        electricians=electricians
    )

# ---------- DELETE USER ----------
@app.route('/delete/<int:id>')
def delete_user(id):

    if 'user' not in session:
        return redirect('/login.html')

    if session['role'].lower() != "admin":
        return redirect('/dashboard.html')

    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()

    cursor.execute(
        "DELETE FROM users WHERE id=?",
        (id,)
    )

    conn.commit()
    conn.close()

    flash("User Deleted Successfully")

    return redirect('/electricians.html')

# ---------- GET ELECTRICIANS ----------
def get_electricians():

    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()

    cursor.execute("""
        SELECT id, name
        FROM users
        WHERE LOWER(role)='electrician'
    """)

    electricians = cursor.fetchall()

    conn.close()

    return electricians

# ---------- JOBS ----------
@app.route('/jobs')
def jobs():

    if 'user' not in session:
        return redirect('/login.html')

    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()

    cursor.execute("""
        SELECT
            jobs.id,
            jobs.title,
            jobs.description,
            jobs.status,
            users.name

        FROM jobs

        LEFT JOIN users
        ON jobs.electrician_id = users.id
    """)

    jobs = cursor.fetchall()

    conn.close()

    return render_template(
        'jobs.html',
        jobs=jobs,
        electricians=get_electricians()
    )

# ---------- ADD JOB ----------
@app.route('/add_job', methods=['POST'])
def add_job():

    if 'user' not in session:
        return redirect('/login.html')

    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()

    cursor.execute("""
        INSERT INTO jobs (
            title,
            description,
            electrician_id,
            status
        )
        VALUES (?, ?, ?, ?)
    """, (
        request.form['title'],
        request.form['description'],
        request.form['electrician_id'],
        "Pending"
    ))

    conn.commit()
    conn.close()

    flash("Job Added Successfully")

    return redirect('/jobs')

# ---------- TASKS ----------
@app.route('/tasks')
def tasks():

    if 'user' not in session:
        return redirect('/login.html')

    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()

    if session['role'].lower() == "electrician":

        cursor.execute("""
            SELECT
                tasks.id,
                tasks.task_name,
                tasks.status,
                jobs.title

            FROM tasks

            LEFT JOIN jobs
            ON tasks.job_id = jobs.id

            WHERE jobs.electrician_id=?
        """, (session['user_id'],))

    else:

        cursor.execute("""
            SELECT
                tasks.id,
                tasks.task_name,
                tasks.status,
                jobs.title

            FROM tasks

            LEFT JOIN jobs
            ON tasks.job_id = jobs.id
        """)

    tasks = cursor.fetchall()

    cursor.execute("""
        SELECT id, title
        FROM jobs
    """)

    jobs = cursor.fetchall()

    conn.close()

    return render_template(
        'tasks.html',
        tasks=tasks,
        jobs=jobs
    )

# ---------- ADD TASK ----------
@app.route('/add_task', methods=['POST'])
def add_task():

    if 'user' not in session:
        return redirect('/login.html')

    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()

    cursor.execute("""
        INSERT INTO tasks (
            job_id,
            task_name,
            status
        )
        VALUES (?, ?, ?)
    """, (
        request.form['job_id'],
        request.form['task_name'],
        "Pending"
    ))

    conn.commit()
    conn.close()

    flash("Task Added Successfully")

    return redirect('/tasks')

# ---------- UPDATE TASK ----------
@app.route('/update_task/<int:id>')
def update_task(id):

    if 'user' not in session:
        return redirect('/login.html')

    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()

    cursor.execute("""
        UPDATE tasks
        SET status='Completed'
        WHERE id=?
    """, (id,))

    conn.commit()
    conn.close()

    flash("Task Completed")

    return redirect('/tasks')

# ---------- MATERIALS ----------
@app.route('/materials')
def materials():

    if 'user' not in session:
        return redirect('/login.html')

    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()

    cursor.execute("""
        SELECT *
        FROM materials
    """)

    materials = cursor.fetchall()

    conn.close()

    return render_template(
        'materials.html',
        materials=materials
    )

# ---------- ADD MATERIAL ----------
@app.route('/add_material', methods=['POST'])
def add_material():

    if 'user' not in session:
        return redirect('/login.html')

    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()

    cursor.execute("""
        INSERT INTO materials (
            name,
            quantity
        )
        VALUES (?, ?)
    """, (
        request.form['name'],
        request.form['quantity']
    ))

    conn.commit()
    conn.close()

    flash("Material Added Successfully")

    return redirect('/materials')

# ---------- REPORTS ----------
# ---------- REPORTS ----------
@app.route('/reports')
def reports():

    if 'user' not in session:
        return redirect('/login.html')

    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()

    # TOTAL ELECTRICIANS
    cursor.execute("""
        SELECT COUNT(*)
        FROM users
        WHERE LOWER(role)='electrician'
    """)
    total_users = cursor.fetchone()[0]

    # TOTAL JOBS
    cursor.execute("""
        SELECT COUNT(*)
        FROM jobs
    """)
    total_jobs = cursor.fetchone()[0]

    # PENDING TASKS
    cursor.execute("""
        SELECT COUNT(*)
        FROM tasks
        WHERE status='Pending'
    """)
    pending_tasks = cursor.fetchone()[0]

    # COMPLETED TASKS
    cursor.execute("""
        SELECT COUNT(*)
        FROM tasks
        WHERE status='Completed'
    """)
    completed_tasks = cursor.fetchone()[0]

    # TOTAL PAYMENTS
    cursor.execute("""
        SELECT SUM(amount)
        FROM payments
    """)

    revenue = cursor.fetchone()[0]

    if revenue is None:
        revenue = 0

    conn.close()

    return render_template(
        "reports.html",
        total_users=total_users,
        total_jobs=total_jobs,
        pending_tasks=pending_tasks,
        completed_tasks=completed_tasks,
        revenue=revenue
    )

# ---------- PAYMENTS ----------
@app.route('/payments')
def payments():

    if 'user' not in session:
        return redirect('/login.html')

    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()

    cursor.execute("""
        SELECT *
        FROM payments
        ORDER BY id DESC
    """)

    payments = cursor.fetchall()

    conn.close()

    return render_template(
        "payments.html",
        payments=payments,
        razorpay_key="rzp_test_Sot2bKh2NFbFIr"
    )

# ---------- CREATE ORDER ----------
@app.route('/create_order', methods=['POST'])
def create_order():

    if 'user' not in session:
        return redirect('/login.html')

    amount = int(request.form['amount']) * 100

    payment = client.order.create({
        "amount": amount,
        "currency": "INR",
        "payment_capture": "1"
    })

    return jsonify({
        "id": payment['id'],
        "amount": payment['amount']
    })

# ---------- PAYMENT SUCCESS ----------
@app.route('/payment_success', methods=['POST'])
def payment_success():

    if 'user' not in session:
        return redirect('/login.html')

    payer_name = request.form['payer_name']
    amount = request.form['amount']
    transaction_id = request.form['razorpay_payment_id']

    payment_date = datetime.now().strftime(
        "%Y-%m-%d %H:%M:%S"
    )

    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()

    cursor.execute("""
        INSERT INTO payments (
            payer_name,
            amount,
            status,
            payment_date
        )
        VALUES (?, ?, ?, ?)
    """, (
        payer_name,
        amount,
        "Success",
        payment_date
    ))

    conn.commit()
    conn.close()

    notification_message = (
        f"₹ {amount} payment successful to {payer_name}"
    )

    return render_template(
        "payment_result.html",
        payer_name=payer_name,
        amount=amount,
        status="Success",
        transaction_id=transaction_id,
        notification=notification_message
    )

# ---------- DOWNLOAD RECEIPT ----------
@app.route('/download_receipt/<transaction_id>')
def download_receipt(transaction_id):

    if 'user' not in session:
        return redirect('/login.html')

    filename = f"receipt_{transaction_id}.pdf"

    doc = SimpleDocTemplate(
        filename,
        pagesize=letter
    )

    styles = getSampleStyleSheet()

    elements = []

    elements.append(
        Paragraph(
            "Payment Receipt",
            styles['Title']
        )
    )

    elements.append(Spacer(1, 20))

    elements.append(
        Paragraph(
            f"Transaction ID: {transaction_id}",
            styles['BodyText']
        )
    )

    elements.append(Spacer(1, 10))

    elements.append(
        Paragraph(
            "Payment completed successfully.",
            styles['BodyText']
        )
    )

    doc.build(elements)

    return send_file(
        filename,
        as_attachment=True
    )

# ---------- PROFILE ----------
@app.route('/profile')
def profile():

    if 'user' not in session:
        return redirect('/login.html')

    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()

    cursor.execute("""
        SELECT *
        FROM users
        WHERE id=?
    """, (session['user_id'],))

    user = cursor.fetchone()

    conn.close()

    return render_template(
        'profile.html',
        user=user
    )

# ---------- UPDATE PROFILE ----------
@app.route('/update_profile', methods=['POST'])
def update_profile():

    if 'user' not in session:
        return redirect('/login.html')

    name = request.form['name']
    phone = request.form['phone']

    image = request.files['profile_image']

    filename = "profile.png"

    if image.filename != "":
        filename = secure_filename(image.filename)

        image.save(
            os.path.join(
                app.config['UPLOAD_FOLDER'],
                filename
            )
        )

    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()

    cursor.execute("""
        UPDATE users
        SET name=?,
            phone=?,
            profile_image=?
        WHERE id=?
    """, (
        name,
        phone,
        filename,
        session['user_id']
    ))

    conn.commit()
    conn.close()

    flash("Profile Updated Successfully")

    return redirect('/profile')

# ---------- CHANGE PASSWORD ----------
@app.route('/change_password', methods=['POST'])
def change_password():

    if 'user' not in session:
        return redirect('/login.html')

    current_password = request.form['current_password']
    new_password = request.form['new_password']

    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()

    cursor.execute("""
        SELECT password
        FROM users
        WHERE id=?
    """, (session['user_id'],))

    user = cursor.fetchone()

    if not check_password_hash(user[0], current_password):

        conn.close()

        flash("Current Password Incorrect")

        return redirect('/profile')

    new_hash = generate_password_hash(new_password)

    cursor.execute("""
        UPDATE users
        SET password=?
        WHERE id=?
    """, (
        new_hash,
        session['user_id']
    ))

    conn.commit()
    conn.close()

    flash("Password Changed Successfully")

    return redirect('/profile')

# ---------- HOME ----------
@app.route('/')
def home():
    return send_from_directory('.', 'index.html')

# ---------- LOGIN PAGE ----------
@app.route('/login.html')
def login_page():
    return send_from_directory('.', 'login.html')

# ---------- REGISTER PAGE ----------
@app.route('/register.html')
def register_page():
    return send_from_directory('.', 'register.html')

# ---------- RUN ----------
if __name__ == "__main__":

    port = int(os.environ.get("PORT", 5000))

    app.run(
        host="0.0.0.0",
        port=port,
        debug=True
    )