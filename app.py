from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify
from functools import wraps
import mysql.connector
from werkzeug.security import generate_password_hash, check_password_hash
import os
import random

app = Flask(__name__)
app.secret_key = os.urandom(24)

# Database Configuration
DB_USER = 'root'
DB_PASSWORD = '!QA2ws#ED'
DB_HOST = 'localhost'
DB_NAME = 'jstock_db'

def get_db_connection():
    try:
        conn = mysql.connector.connect(
            user=DB_USER,
            password=DB_PASSWORD,
            host=DB_HOST,
            database=DB_NAME
        )
        return conn
    except mysql.connector.Error as err:
        print(f"Error: {err}")
        return None

@app.route('/')
def index():
    return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        user_id = request.form.get('user_id')
        password = request.form.get('password')
        
        conn = get_db_connection()
        if not conn:
            flash("Database connection error. Please contact admin.", "error")
            return render_template('login.html')
            
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT * FROM users WHERE user_id = %s", (user_id,))
        user = cursor.fetchone()
        cursor.close()
        conn.close()
        
        if user and check_password_hash(user['password_hash'], password):
            if user['status'] == 'pending':
                flash("Your account registration is pending approval by admin.", "error")
                return render_template('login.html')
            elif user['status'] == 'rejected':
                flash("Your application was declined. Please contact admin.", "error")
                return render_template('login.html')
                
            session['user_id'] = user['user_id']
            session['role'] = user['role']
            session['name'] = user['full_name']
            
            if user['role'] == 'owner':
                return redirect(url_for('owner_dashboard'))
            else:
                return redirect(url_for('employee_dashboard'))
        else:
            flash("Invalid User ID or Password.", "error")
            
    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        name = request.form.get('name')
        mobile = request.form.get('mobile')
        email = request.form.get('email')
        password = request.form.get('password')
        
        # Temp request ID
        temp_user_id = f"REQ-{random.randint(1000, 9999)}"
        password_hash = generate_password_hash(password)
        
        conn = get_db_connection()
        if not conn:
            flash("Database connection error.", "error")
            return render_template('registration.html')
            
        cursor = conn.cursor()
        try:
            cursor.execute(
                "INSERT INTO users (user_id, password_hash, full_name, mobile, email, role, status) VALUES (%s, %s, %s, %s, %s, %s, %s)",
                (temp_user_id, password_hash, name, mobile, email, 'employee', 'pending')
            )
            conn.commit()
            flash("Application submitted successfully! Please wait for the admin to approve your request.", "success")
            return redirect(url_for('login'))
        except mysql.connector.Error as err:
            flash(f"Registration failed: {err}", "error")
        finally:
            cursor.close()
            conn.close()
            
    return render_template('registration.html')

def login_required(role=None):
    def decorator(view):
        @wraps(view)
        def wrapped_view(**kwargs):
            if 'user_id' not in session:
                return redirect(url_for('login'))
            if role and session.get('role') != role:
                return redirect(url_for('login'))
            return view(**kwargs)
        return wrapped_view
    return decorator

@app.route('/dashboard')
@login_required()
def dashboard():
    if session.get('role') == 'owner':
        return redirect(url_for('owner_dashboard'))
    return redirect(url_for('employee_dashboard'))

@app.route('/owner-dashboard')
@login_required(role='owner')
def owner_dashboard():
    return render_template('owner-dashboard.html', name=session.get('name'))

@app.route('/employee-dashboard')
@login_required(role='employee')
def employee_dashboard():
    return render_template('employee-dashboard.html', name=session.get('name'))

@app.route('/customer-management')
@login_required()
def customer_management():
    return render_template('customer-management.html', name=session.get('name'))

@app.route('/order-management')
@login_required()
def order_management():
    return render_template('order-management.html', name=session.get('name'))

@app.route('/ornaments-inventory')
@login_required()
def ornaments_inventory():
    return render_template('ornaments-inventory.html', name=session.get('name'))

@app.route('/task-management')
@login_required()
def task_management():
    return render_template('task-management.html', name=session.get('name'))

@app.route('/employee-requests')
@login_required()
def employee_requests():
    return render_template('employee-requests.html', name=session.get('name'))

@app.route('/business-status')
@login_required()
def business_status():
    return render_template('business-status.html', name=session.get('name'))

# API: Get Pending Employee Requests
@app.route('/api/employee-requests', methods=['GET'])
@login_required()
def get_employee_requests():
    conn = get_db_connection()
    if not conn:
        return jsonify({"success": False, "message": "Database connection error"}), 500
    
    cursor = conn.cursor(dictionary=True)
    cursor.execute("""
        SELECT id, user_id, full_name, email, mobile, status, 
               DATE_FORMAT(created_at, '%b %d, %Y %h:%i %p') as date_applied 
        FROM users WHERE status = 'pending' ORDER BY created_at DESC
    """)
    pending = cursor.fetchall()
    
    cursor.execute("SELECT COUNT(*) as count FROM users WHERE status = 'pending'")
    total_pending = cursor.fetchone()['count']
    
    cursor.execute("SELECT COUNT(*) as count FROM users WHERE status = 'approved' AND role = 'employee'")
    total_approved = cursor.fetchone()['count']
    
    cursor.close()
    conn.close()
    
    return jsonify({
        "success": True,
        "pending": pending,
        "stats": {
            "total_pending": total_pending,
            "total_approved": total_approved
        }
    })

# API: Approve Employee Request & Assign Employee User ID
@app.route('/api/employee-requests/approve', methods=['POST'])
@login_required()
def approve_employee_request():
    data = request.get_json() or {}
    request_id = data.get('id')
    custom_user_id = data.get('user_id')
    
    if not request_id or not custom_user_id:
        return jsonify({"success": False, "message": "Missing request ID or User ID"}), 400
        
    conn = get_db_connection()
    if not conn:
        return jsonify({"success": False, "message": "Database connection error"}), 500
        
    cursor = conn.cursor(dictionary=True)
    # Check if user_id is already taken by another user
    cursor.execute("SELECT id FROM users WHERE user_id = %s AND id != %s", (custom_user_id, request_id))
    existing = cursor.fetchone()
    if existing:
        cursor.close()
        conn.close()
        return jsonify({"success": False, "message": f"User ID '{custom_user_id}' is already taken by another user."}), 400
        
    cursor.execute("UPDATE users SET user_id = %s, status = 'approved' WHERE id = %s", (custom_user_id, request_id))
    conn.commit()
    cursor.close()
    conn.close()
    
    return jsonify({"success": True, "message": f"Employee request approved! New User ID is '{custom_user_id}'."})

# API: Decline Employee Request
@app.route('/api/employee-requests/decline', methods=['POST'])
@login_required()
def decline_employee_request():
    data = request.get_json() or {}
    request_id = data.get('id')
    
    if not request_id:
        return jsonify({"success": False, "message": "Missing request ID"}), 400
        
    conn = get_db_connection()
    if not conn:
        return jsonify({"success": False, "message": "Database connection error"}), 500
        
    cursor = conn.cursor()
    cursor.execute("UPDATE users SET status = 'rejected' WHERE id = %s", (request_id,))
    conn.commit()
    cursor.close()
    conn.close()
    
    return jsonify({"success": True, "message": "Employee request declined."})

# API: Get Orders List
@app.route('/api/orders', methods=['GET'])
@login_required()
def get_orders():
    conn = get_db_connection()
    if not conn:
        return jsonify({"success": False, "message": "Database connection error"}), 500
        
    cursor = conn.cursor(dictionary=True)
    cursor.execute("""
        SELECT id, order_id, category, item_type, weight, purity, customer_name, status,
               DATE_FORMAT(created_at, '%b %d, %Y') as order_date
        FROM orders ORDER BY created_at DESC
    """)
    orders = cursor.fetchall()
    cursor.close()
    conn.close()
    
    return jsonify({"success": True, "orders": orders})

# API: Create New Order
@app.route('/api/orders', methods=['POST'])
@login_required()
def create_order():
    data = request.get_json(silent=True) or request.form or {}
    category = data.get('category')
    item_type = data.get('item_type')
    weight = data.get('weight')
    purity = data.get('purity')
    customer_name = data.get('customer_name')
    
    if not all([category, item_type, weight, purity, customer_name]):
        return jsonify({"success": False, "message": "All fields are required"}), 400
        
    conn = get_db_connection()
    if not conn:
        return jsonify({"success": False, "message": "Database connection error"}), 500
        
    cursor = conn.cursor(dictionary=True)
    # Generate next order ID
    order_id = f"ORD-{random.randint(1000, 9999)}"
    cursor.execute(
        "INSERT INTO orders (order_id, category, item_type, weight, purity, customer_name, status) VALUES (%s, %s, %s, %s, %s, %s, 'Processing')",
        (order_id, category, item_type, weight, purity, customer_name)
    )
    conn.commit()
    cursor.close()
    conn.close()
    
    return jsonify({"success": True, "message": f"Order {order_id} created successfully!", "order_id": order_id})


# API: Get Ornaments Inventory Data (Calculated from DB orders)
@app.route('/api/ornaments', methods=['GET'])
@login_required()
def get_ornaments_inventory():
    conn = get_db_connection()
    if not conn:
        return jsonify({"success": False, "message": "Database connection error"}), 500
        
    cursor = conn.cursor(dictionary=True)
    cursor.execute("""
        SELECT id, order_id, category, item_type, weight, purity, customer_name, status,
               DATE_FORMAT(created_at, '%b %d, %Y') as order_date
        FROM orders ORDER BY created_at DESC
    """)
    orders = cursor.fetchall()
    
    # Calculate purity group stats
    stats = {
        "999 Gold": {"items": 0, "weight": 0.0},
        "24K": {"items": 0, "weight": 0.0},
        "22K": {"items": 0, "weight": 0.0},
        "18K": {"items": 0, "weight": 0.0}
    }
    
    for item in orders:
        purity = item['purity']
        wt = float(item['weight'])
        if purity in stats:
            stats[purity]["items"] += 1
            stats[purity]["weight"] += wt
        elif "999" in purity:
            stats["999 Gold"]["items"] += 1
            stats["999 Gold"]["weight"] += wt
        elif "24K" in purity:
            stats["24K"]["items"] += 1
            stats["24K"]["weight"] += wt
        elif "22K" in purity:
            stats["22K"]["items"] += 1
            stats["22K"]["weight"] += wt
        elif "18K" in purity:
            stats["18K"]["items"] += 1
            stats["18K"]["weight"] += wt

    cursor.close()
    conn.close()
    
    return jsonify({
        "success": True,
        "stats": stats,
        "items": orders
    })

# API: Get Tasks
@app.route('/api/tasks', methods=['GET'])
@login_required()
def get_tasks():
    conn = get_db_connection()
    if not conn:
        return jsonify({"success": False, "message": "Database connection error"}), 500
        
    cursor = conn.cursor(dictionary=True)
    cursor.execute("""
        SELECT id, task_id, description, priority, status, assignee, category_tag,
               DATE_FORMAT(due_date, '%b %d, %Y') as due_date
        FROM tasks ORDER BY created_at DESC
    """)
    tasks = cursor.fetchall()
    
    cursor.execute("SELECT COUNT(*) as count FROM tasks WHERE status != 'Completed'")
    active_count = cursor.fetchone()['count']
    
    cursor.execute("SELECT COUNT(*) as count FROM tasks WHERE priority = 'High' AND status != 'Completed'")
    pending_alerts = cursor.fetchone()['count']
    
    cursor.close()
    conn.close()
    
    return jsonify({
        "success": True,
        "tasks": tasks,
        "stats": {
            "active_count": active_count,
            "pending_alerts": pending_alerts
        }
    })

# API: Create New Task
@app.route('/api/tasks', methods=['POST'])
@login_required()
def create_task():
    data = request.get_json(silent=True) or request.form or {}
    description = data.get('description')
    priority = data.get('priority', 'Medium')
    assignee = data.get('assignee', 'Unassigned')
    category_tag = data.get('category_tag', '#inventory')
    due_date = data.get('due_date')
    
    if not description:
        return jsonify({"success": False, "message": "Task description is required"}), 400
        
    conn = get_db_connection()
    if not conn:
        return jsonify({"success": False, "message": "Database connection error"}), 500
        
    cursor = conn.cursor(dictionary=True)
    task_id = f"TSK-{random.randint(1000, 9999)}"
    cursor.execute(
        "INSERT INTO tasks (task_id, description, priority, status, assignee, category_tag, due_date) VALUES (%s, %s, %s, 'In Progress', %s, %s, %s)",
        (task_id, description, priority, assignee, category_tag, due_date if due_date else None)
    )
    conn.commit()
    cursor.close()
    conn.close()
    
    return jsonify({"success": True, "message": f"Task {task_id} created successfully!", "task_id": task_id})

# API: Update Task Status
@app.route('/api/tasks/status', methods=['POST'])
@login_required()
def update_task_status():
    data = request.get_json(silent=True) or request.form or {}
    task_db_id = data.get('id')
    new_status = data.get('status')
    
    if not task_db_id or not new_status:
        return jsonify({"success": False, "message": "Missing task ID or status"}), 400
        
    conn = get_db_connection()
    if not conn:
        return jsonify({"success": False, "message": "Database connection error"}), 500
        
    cursor = conn.cursor()
    cursor.execute("UPDATE tasks SET status = %s WHERE id = %s", (new_status, task_db_id))
    conn.commit()
    cursor.close()
    conn.close()
    
    return jsonify({"success": True, "message": "Task status updated."})

# API: Update Order Status
@app.route('/api/orders/status', methods=['POST'])
@login_required()
def update_order_status():
    data = request.get_json(silent=True) or request.form or {}
    order_db_id = data.get('id')
    new_status = data.get('status')
    
    if not order_db_id or not new_status:
        return jsonify({"success": False, "message": "Missing order ID or status"}), 400
        
    conn = get_db_connection()
    if not conn:
        return jsonify({"success": False, "message": "Database connection error"}), 500
        
    cursor = conn.cursor()
    cursor.execute("UPDATE orders SET status = %s WHERE id = %s", (new_status, order_db_id))
    conn.commit()
    cursor.close()
    conn.close()
    
    return jsonify({"success": True, "message": "Order status updated."})

INDIAN_GOLD_RATES = {
    "999 Gold": 7300.0,
    "24K": 7250.0,
    "22K": 6645.0,
    "18K": 5440.0
}

# API: Add Money / Record Cash Transaction
@app.route('/api/cash/add', methods=['POST'])
@login_required()
def add_cash_transaction():
    data = request.get_json(silent=True) or request.form or {}
    try:
        amount = float(data.get('amount', 0))
    except (ValueError, TypeError):
        amount = 0.0
        
    payment_mode = data.get('payment_mode', 'Cash')
    source = data.get('source', 'Capital Top-up')
    remarks = data.get('remarks', 'Added to Treasury')
    
    if amount <= 0:
        return jsonify({"success": False, "message": "Valid amount greater than ₹0 is required"}), 400
        
    conn = get_db_connection()
    if not conn:
        return jsonify({"success": False, "message": "Database connection error"}), 500
        
    cursor = conn.cursor()
    txn_id = f"TXN-{random.randint(10000, 99999)}"
    cursor.execute(
        "INSERT INTO cash_transactions (transaction_id, type, amount, payment_mode, source, remarks) VALUES (%s, 'Add Money', %s, %s, %s, %s)",
        (txn_id, amount, payment_mode, source, remarks)
    )
    conn.commit()
    cursor.close()
    conn.close()
    
    return jsonify({"success": True, "message": f"Successfully added ₹{amount:,.2f} to Treasury!", "transaction_id": txn_id})

# API: Get Cash Transactions & Balance
@app.route('/api/cash/transactions', methods=['GET'])
@login_required()
def get_cash_transactions():
    conn = get_db_connection()
    if not conn:
        return jsonify({"success": False, "message": "Database connection error"}), 500
        
    cursor = conn.cursor(dictionary=True)
    cursor.execute("""
        SELECT id, transaction_id, type, amount, payment_mode, source, remarks,
               DATE_FORMAT(created_at, '%b %d, %Y %h:%i %p') as date_str
        FROM cash_transactions ORDER BY created_at DESC LIMIT 20
    """)
    txns = cursor.fetchall()
    
    cursor.execute("SELECT COALESCE(SUM(amount), 0) as total_cash FROM cash_transactions")
    total_cash = float(cursor.fetchone()['total_cash'])
    
    cursor.close()
    conn.close()
    
    return jsonify({
        "success": True,
        "total_cash": total_cash,
        "transactions": txns
    })

# API: Unified Dashboard Summary (Indian Gold Rates & Cash Sync)
@app.route('/api/dashboard-summary', methods=['GET'])
@login_required()
def get_dashboard_summary():
    conn = get_db_connection()
    if not conn:
        return jsonify({"success": False, "message": "Database connection error"}), 500
        
    cursor = conn.cursor(dictionary=True)
    
    # Recent 6 orders
    cursor.execute("""
        SELECT id, order_id, category, item_type, weight, purity, customer_name, status,
               DATE_FORMAT(created_at, '%b %d, %Y') as order_date
        FROM orders ORDER BY created_at DESC LIMIT 6
    """)
    recent_orders = cursor.fetchall()
    
    # Recent 6 tasks
    cursor.execute("""
        SELECT id, task_id, description, priority, status, assignee, category_tag,
               DATE_FORMAT(due_date, '%b %d, %Y') as due_date
        FROM tasks ORDER BY created_at DESC LIMIT 6
    """)
    recent_tasks = cursor.fetchall()
    
    # Calculate Total Gold Weight & Indian Gold Value (in INR)
    cursor.execute("SELECT weight, purity FROM orders")
    all_orders = cursor.fetchall()
    
    total_weight = 0.0
    total_gold_value_inr = 0.0
    
    for item in all_orders:
        wt = float(item['weight'])
        purity = item['purity']
        total_weight += wt
        
        # Determine rate by Indian purity standards
        rate = INDIAN_GOLD_RATES.get(purity)
        if not rate:
            if "999" in purity: rate = INDIAN_GOLD_RATES["999 Gold"]
            elif "24" in purity: rate = INDIAN_GOLD_RATES["24K"]
            elif "22" in purity: rate = INDIAN_GOLD_RATES["22K"]
            elif "18" in purity: rate = INDIAN_GOLD_RATES["18K"]
            else: rate = 7250.0 # Default 24K Indian benchmark rate
        
        total_gold_value_inr += wt * rate
        
    # Cash Treasury Balance
    cursor.execute("SELECT COALESCE(SUM(amount), 0) as total_cash FROM cash_transactions")
    total_cash_inr = float(cursor.fetchone()['total_cash'])
    
    # Active tasks count
    cursor.execute("SELECT COUNT(*) as count FROM tasks WHERE status != 'Completed'")
    active_tasks_count = cursor.fetchone()['count']
    
    # Total orders count
    cursor.execute("SELECT COUNT(*) as count FROM orders")
    total_orders_count = cursor.fetchone()['count']
    
    cursor.close()
    conn.close()
    
    return jsonify({
        "success": True,
        "recent_orders": recent_orders,
        "recent_tasks": recent_tasks,
        "stats": {
            "gold_rate_24k_inr": 7250.0,
            "gold_rate_22k_inr": 6645.0,
            "gold_rate_display": "₹7,250 / g (24K)",
            "gold_rate_10g_display": "₹72,500 / 10g",
            "total_weight_g": total_weight,
            "total_weight_kg": round(total_weight / 1000.0, 2),
            "total_gold_value_inr": total_gold_value_inr,
            "total_cash_inr": total_cash_inr,
            "active_tasks": active_tasks_count,
            "total_orders": total_orders_count
        }
    })

# API: Business Status Data Endpoint
@app.route('/api/business-status-data', methods=['GET'])
@login_required()
def get_business_status_data():
    conn = get_db_connection()
    if not conn:
        return jsonify({"success": False, "message": "Database connection error"}), 500
        
    cursor = conn.cursor(dictionary=True)
    
    # Orders and weight breakdown
    cursor.execute("SELECT weight, purity FROM orders")
    all_orders = cursor.fetchall()
    
    total_weight = 0.0
    total_gold_value_inr = 0.0
    items_count = len(all_orders)
    
    for item in all_orders:
        wt = float(item['weight'])
        purity = item['purity']
        total_weight += wt
        rate = INDIAN_GOLD_RATES.get(purity, 7250.0)
        total_gold_value_inr += wt * rate
        
    # Cash Treasury Balance
    cursor.execute("SELECT COALESCE(SUM(amount), 0) as total_cash FROM cash_transactions")
    total_cash_inr = float(cursor.fetchone()['total_cash'])
    
    # Counts
    cursor.execute("SELECT COUNT(*) as count FROM orders WHERE status = 'Processing'")
    pending_orders = cursor.fetchone()['count']
    
    cursor.execute("SELECT COUNT(*) as count FROM tasks WHERE status != 'Completed'")
    active_tasks = cursor.fetchone()['count']
    
    cursor.execute("SELECT COUNT(*) as count FROM users WHERE status = 'pending'")
    pending_requests = cursor.fetchone()['count']
    
    # Fetch recent cash transactions for table
    cursor.execute("""
        SELECT transaction_id, type, amount, payment_mode, source, remarks,
               DATE_FORMAT(created_at, '%b %d, %Y') as date_str
        FROM cash_transactions ORDER BY created_at DESC LIMIT 5
    """)
    recent_cash_txns = cursor.fetchall()
    
    cursor.close()
    conn.close()
    
    return jsonify({
        "success": True,
        "metrics": {
            "total_weight_kg": round(total_weight / 1000.0, 2),
            "total_weight_g": total_weight,
            "total_gold_value_inr": total_gold_value_inr,
            "total_cash_inr": total_cash_inr,
            "items_count": items_count,
            "gold_rate_24k_inr": 7250.0,
            "pending_orders": pending_orders,
            "active_tasks": active_tasks,
            "pending_requests": pending_requests
        },
        "recent_cash_txns": recent_cash_txns
    })

# API: Customer Management - List Customers & Stats
@app.route('/api/customers', methods=['GET'])
@login_required()
def get_customers():
    conn = get_db_connection()
    if not conn:
        return jsonify({"success": False, "message": "Database connection error"}), 500
        
    cursor = conn.cursor(dictionary=True)
    cursor.execute("""
        SELECT id, customer_id, name, email, mobile, credit_balance, debit_balance, orders_count,
               DATE_FORMAT(created_at, '%b %d, %Y') as created_date
        FROM customers ORDER BY created_at DESC
    """)
    customers = cursor.fetchall()
    
    # Calculate stats
    cursor.execute("SELECT COUNT(*) as count, COALESCE(SUM(credit_balance), 0) as total_credit, COALESCE(SUM(debit_balance), 0) as total_debit FROM customers")
    stats_row = cursor.fetchone()
    
    cursor.close()
    conn.close()
    
    return jsonify({
        "success": True,
        "customers": customers,
        "stats": {
            "total_customers": stats_row['count'],
            "total_credit_inr": float(stats_row['total_credit']),
            "total_debit_inr": float(stats_row['total_debit'])
        }
    })

# API: Customer Management - Add New Customer
@app.route('/api/customers/add', methods=['POST'])
@login_required()
def add_customer():
    data = request.get_json(silent=True) or request.form or {}
    name = data.get('name', '').strip()
    email = data.get('email', '').strip()
    mobile = data.get('mobile', '').strip()
    
    try:
        credit_balance = float(data.get('credit_balance', 0))
    except (ValueError, TypeError):
        credit_balance = 0.0
        
    try:
        debit_balance = float(data.get('debit_balance', 0))
    except (ValueError, TypeError):
        debit_balance = 0.0
        
    if not name or not mobile:
        return jsonify({"success": False, "message": "Customer name and mobile number are required"}), 400
        
    conn = get_db_connection()
    if not conn:
        return jsonify({"success": False, "message": "Database connection error"}), 500
        
    cursor = conn.cursor()
    customer_id = f"JS-{random.randint(1000, 9999)}"
    
    cursor.execute("""
        INSERT INTO customers (customer_id, name, email, mobile, credit_balance, debit_balance, orders_count)
        VALUES (%s, %s, %s, %s, %s, %s, 0)
    """, (customer_id, name, email or 'N/A', mobile, credit_balance, debit_balance))
    
    conn.commit()
    cursor.close()
    conn.close()
    
    return jsonify({"success": True, "message": f"Customer '{name}' created successfully!", "customer_id": customer_id})

# API: Customer Management - Update Credit & Debit Balances
@app.route('/api/customers/update-balance', methods=['POST'])
@login_required()
def update_customer_balance():
    data = request.get_json(silent=True) or request.form or {}
    cust_db_id = data.get('id')
    
    try:
        credit_balance = float(data.get('credit_balance', 0))
    except (ValueError, TypeError):
        credit_balance = 0.0
        
    try:
        debit_balance = float(data.get('debit_balance', 0))
    except (ValueError, TypeError):
        debit_balance = 0.0
        
    if not cust_db_id:
        return jsonify({"success": False, "message": "Missing customer ID"}), 400
        
    conn = get_db_connection()
    if not conn:
        return jsonify({"success": False, "message": "Database connection error"}), 500
        
    cursor = conn.cursor()
    cursor.execute("""
        UPDATE customers SET credit_balance = %s, debit_balance = %s WHERE id = %s
    """, (credit_balance, debit_balance, cust_db_id))
    
    conn.commit()
    cursor.close()
    conn.close()
    
    return jsonify({"success": True, "message": "Customer balances updated live."})

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

if __name__ == '__main__':
    app.run(debug=True, use_reloader=True)



