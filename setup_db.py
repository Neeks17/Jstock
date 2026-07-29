import mysql.connector
from mysql.connector import errorcode

# Default credentials as proposed
DB_USER = 'root'
DB_PASSWORD = '!QA2ws#ED'
DB_HOST = 'localhost'
DB_NAME = 'jstock_db'

def setup_database():
    try:
        # Connect to MySQL server (without database specified)
        conn = mysql.connector.connect(
            user=DB_USER,
            password=DB_PASSWORD,
            host=DB_HOST
        )
        cursor = conn.cursor()
        
        # Create database if not exists
        cursor.execute(f"CREATE DATABASE IF NOT EXISTS {DB_NAME}")
        print(f"Database '{DB_NAME}' created or already exists.")
        
        # Select the database
        cursor.execute(f"USE {DB_NAME}")
        
        # Create the users table
        users_table_query = """
        CREATE TABLE IF NOT EXISTS users (
            id INT AUTO_INCREMENT PRIMARY KEY,
            user_id VARCHAR(50) UNIQUE NOT NULL,
            password_hash VARCHAR(255) NOT NULL,
            full_name VARCHAR(100) NOT NULL,
            mobile VARCHAR(20) NOT NULL,
            email VARCHAR(100) NOT NULL,
            role ENUM('owner', 'employee') NOT NULL DEFAULT 'employee',
            status ENUM('pending', 'approved', 'rejected') NOT NULL DEFAULT 'pending',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """
        cursor.execute(users_table_query)
        print("Table 'users' created or already exists.")
        
        # Create the orders table
        orders_table_query = """
        CREATE TABLE IF NOT EXISTS orders (
            id INT AUTO_INCREMENT PRIMARY KEY,
            order_id VARCHAR(50) UNIQUE NOT NULL,
            category VARCHAR(50) NOT NULL,
            item_type VARCHAR(100) NOT NULL,
            weight DECIMAL(10, 2) NOT NULL,
            purity VARCHAR(50) NOT NULL,
            customer_name VARCHAR(100) NOT NULL,
            status VARCHAR(50) NOT NULL DEFAULT 'Processing',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """
        cursor.execute(orders_table_query)
        try:
            cursor.execute("ALTER TABLE orders MODIFY status VARCHAR(50) NOT NULL DEFAULT 'Processing'")
        except Exception:
            pass
        print("Table 'orders' created or updated.")
        
        # Create the tasks table
        tasks_table_query = """
        CREATE TABLE IF NOT EXISTS tasks (
            id INT AUTO_INCREMENT PRIMARY KEY,
            task_id VARCHAR(50) UNIQUE NOT NULL,
            description TEXT NOT NULL,
            priority ENUM('High', 'Medium', 'Low') NOT NULL DEFAULT 'Medium',
            status VARCHAR(50) NOT NULL DEFAULT 'Pending',
            assignee VARCHAR(100) NOT NULL,
            category_tag VARCHAR(50) DEFAULT '#inventory',
            due_date DATE,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """
        cursor.execute(tasks_table_query)
        try:
            cursor.execute("ALTER TABLE tasks MODIFY status VARCHAR(50) NOT NULL DEFAULT 'Pending'")
        except Exception:
            pass
        print("Table 'tasks' created or updated.")
        
        # Create cash_transactions table
        cash_table_query = """
        CREATE TABLE IF NOT EXISTS cash_transactions (
            id INT AUTO_INCREMENT PRIMARY KEY,
            transaction_id VARCHAR(50) UNIQUE NOT NULL,
            type ENUM('Add Money', 'Sale Cash', 'Expense') NOT NULL DEFAULT 'Add Money',
            amount DECIMAL(12, 2) NOT NULL,
            payment_mode VARCHAR(50) NOT NULL DEFAULT 'Cash',
            source VARCHAR(100) NOT NULL,
            remarks VARCHAR(255),
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """
        cursor.execute(cash_table_query)
        print("Table 'cash_transactions' created or updated.")

        # Create customers table
        customers_table_query = """
        CREATE TABLE IF NOT EXISTS customers (
            id INT AUTO_INCREMENT PRIMARY KEY,
            customer_id VARCHAR(50) UNIQUE NOT NULL,
            name VARCHAR(100) NOT NULL,
            email VARCHAR(100) NOT NULL,
            mobile VARCHAR(20) NOT NULL,
            credit_balance DECIMAL(12, 2) NOT NULL DEFAULT 0.00,
            debit_balance DECIMAL(12, 2) NOT NULL DEFAULT 0.00,
            orders_count INT NOT NULL DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """
        cursor.execute(customers_table_query)
        print("Table 'customers' created or updated.")

        # Insert a default owner if not exists
        cursor.execute("SELECT COUNT(*) FROM users WHERE role = 'owner'")
        if cursor.fetchone()[0] == 0:
            from werkzeug.security import generate_password_hash
            default_password = generate_password_hash("admin123")
            insert_owner = """
            INSERT INTO users (user_id, password_hash, full_name, mobile, email, role, status)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
            """
            cursor.execute(insert_owner, ("admin", default_password, "System Owner", "0000000000", "admin@jstock.com", "owner", "approved"))
            conn.commit()
            print("Default owner created (user_id: admin, password: admin123)")

        # Seed initial orders if empty
        cursor.execute("SELECT COUNT(*) FROM orders")
        if cursor.fetchone()[0] == 0:
            seed_orders = [
                ('ORD-9021', 'Gold', 'Bridal Necklace', 45.20, '22K', 'Ananya Sharma', 'Processing'),
                ('ORD-8944', 'Diamond', 'Solitaire Ring', 8.45, '18K', 'Vikram Malhotra', 'Ready for Pickup'),
                ('ORD-8910', 'Platinum', 'Men\'s Band', 12.10, '24K', 'Rajesh Khanna', 'Processing'),
                ('ORD-8850', 'Gold', 'Gold Bullion Coin', 50.00, '999 Gold', 'Meera Gupta', 'Reserved'),
                ('ORD-8840', 'Gold', 'Temple Work Bangle', 122.45, '24K', 'Suresh Kumar', 'Processing'),
                ('ORD-8830', 'Gold', 'Standard Delivery Ingot', 1000.00, '999 Gold', 'Vipul Patel', 'Ready for Pickup')
            ]
            insert_order = """
            INSERT INTO orders (order_id, category, item_type, weight, purity, customer_name, status)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
            """
            cursor.executemany(insert_order, seed_orders)
            conn.commit()
            print("Initial seed orders created.")

        # Seed initial tasks if empty
        cursor.execute("SELECT COUNT(*) FROM tasks")
        if cursor.fetchone()[0] == 0:
            seed_tasks = [
                ('TSK-1001', 'Monthly Gold Audit - Central Vault', 'High', 'In Progress', 'Alex Mercer', '#audit', '2024-10-24'),
                ('TSK-1002', 'Supplier Intake: Rose Gold Rings', 'Medium', 'Pending', 'Sarah Chen', '#inventory', '2024-10-26'),
                ('TSK-1003', 'Re-tag Bangle Collection with QR codes', 'Low', 'Completed', 'James Wilson', '#inventory', '2024-10-21'),
                ('TSK-1004', 'Client Order Appraisal Valuation', 'High', 'Pending', 'Alex Mercer', '#customer', '2024-10-25')
            ]
            insert_task = """
            INSERT INTO tasks (task_id, description, priority, status, assignee, category_tag, due_date)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
            """
            cursor.executemany(insert_task, seed_tasks)
            conn.commit()
            print("Initial seed tasks created.")

        # Seed initial cash transactions if empty
        cursor.execute("SELECT COUNT(*) FROM cash_transactions")
        if cursor.fetchone()[0] == 0:
            seed_cash = [
                ('TXN-1001', 'Add Money', 550000.00, 'Bank Transfer', 'Opening Capital', 'Store Opening Treasury Deposit'),
                ('TXN-1002', 'Add Money', 225000.00, 'UPI', 'Daily Counter Cash', 'Counter Sales Deposit')
            ]
            cursor.executemany("INSERT INTO cash_transactions (transaction_id, type, amount, payment_mode, source, remarks) VALUES (%s, %s, %s, %s, %s, %s)", seed_cash)
            conn.commit()
            print("Initial cash transactions created.")

        # Seed initial customers if empty
        cursor.execute("SELECT COUNT(*) FROM customers")
        if cursor.fetchone()[0] == 0:
            seed_cust = [
                ('JS-8842', 'Julianne Burke', 'j.burke@example.com', '+91 98765 43210', 1250.00, 0.00, 24),
                ('JS-2109', 'Marcus Sterling', 'sterling.m@web.com', '+91 98123 45678', 0.00, 4500.00, 8),
                ('JS-4512', 'Elena Ortega', 'e.ortega@design.io', '+91 97111 22233', 12400.00, 0.00, 112),
                ('JS-1288', 'David Kim', 'd.kim@logistics.com', '+91 96555 44332', 0.00, 850.00, 56)
            ]
            cursor.executemany("INSERT INTO customers (customer_id, name, email, mobile, credit_balance, debit_balance, orders_count) VALUES (%s, %s, %s, %s, %s, %s, %s)", seed_cust)
            conn.commit()
            print("Initial seed customers created.")
            
        cursor.close()
        conn.close()
        print("Database setup complete.")
        
    except mysql.connector.Error as err:
        print(f"Error connecting to MySQL: {err}")
        if err.errno == errorcode.ER_ACCESS_DENIED_ERROR:
            print("Something is wrong with your user name or password")
        elif err.errno == errorcode.ER_BAD_DB_ERROR:
            print("Database does not exist")
        else:
            print(err)

if __name__ == "__main__":
    setup_database()


