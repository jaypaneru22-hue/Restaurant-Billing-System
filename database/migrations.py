"""Database initialization, seed data population, and schema migration helpers."""
import sqlite3
from decimal import Decimal
from database.db import DatabaseManager, db
from database.schema import init_schema
from utils.security import hash_password
from utils.logger import logger

DEFAULT_MENU_SEED = [
    # Beverages
    ("Masala Chai", "Beverages", "30.00", 1),
    ("Cold Coffee with Ice Cream", "Beverages", "90.00", 1),
    ("Fresh Lime Soda", "Beverages", "60.00", 1),
    ("Mango Lassi", "Beverages", "80.00", 1),
    ("Mineral Water 1L", "Beverages", "20.00", 1),

    # Starters
    ("Paneer Tikka", "Starters", "220.00", 1),
    ("Crispy Corn Salt & Pepper", "Starters", "180.00", 1),
    ("Chicken Tikka", "Starters", "260.00", 1),
    ("Vegetable Spring Rolls", "Starters", "160.00", 1),
    ("Fish Fingers", "Starters", "290.00", 1),

    # Main Course
    ("Paneer Butter Masala", "Main Course", "280.00", 1),
    ("Dal Makhani", "Main Course", "240.00", 1),
    ("Butter Chicken", "Main Course", "340.00", 1),
    ("Kadhai Paneer", "Main Course", "270.00", 1),
    ("Mutton Rogan Josh", "Main Course", "390.00", 1),
    ("Mix Vegetable Curry", "Main Course", "220.00", 1),

    # Breads & Rice
    ("Butter Naan", "Breads & Rice", "45.00", 1),
    ("Garlic Naan", "Breads & Rice", "60.00", 1),
    ("Tandoori Roti", "Breads & Rice", "25.00", 1),
    ("Jeera Rice", "Breads & Rice", "140.00", 1),
    ("Hyderabadi Veg Biryani", "Breads & Rice", "240.00", 1),
    ("Chicken Dum Biryani", "Breads & Rice", "290.00", 1),

    # Desserts
    ("Gulab Jamun (2 pcs)", "Desserts", "70.00", 1),
    ("Rasmalai (2 pcs)", "Desserts", "90.00", 1),
    ("Chocolate Brownie with Sizzler", "Desserts", "150.00", 1),
    ("Vanilla Ice Cream", "Desserts", "60.00", 1)
]


def seed_initial_data(conn: sqlite3.Connection) -> None:
    """Seeds default administrative & cashier accounts and menu catalog if tables are empty."""
    cursor = conn.cursor()

    # 1. Seed Users
    cursor.execute("SELECT COUNT(*) FROM users;")
    user_count = cursor.fetchone()[0]
    if user_count == 0:
        logger.info("Seeding default administrative and cashier users...")
        admin_hash = hash_password("Admin@123")
        cashier_hash = hash_password("Cashier@123")

        cursor.execute(
            """INSERT INTO users (username, password_hash, full_name, role)
               VALUES (?, ?, ?, ?);""",
            ("admin", admin_hash, "Administrator (Jay Paneru)", "ADMIN")
        )
        admin_id = cursor.lastrowid
        cursor.execute(
            """INSERT INTO user_settings (user_id, theme, currency, default_tax_rate)
               VALUES (?, 'dark', '₹', 5.0);""",
            (admin_id,)
        )

        cursor.execute(
            """INSERT INTO users (username, password_hash, full_name, role)
               VALUES (?, ?, ?, ?);""",
            ("cashier1", cashier_hash, "Senior Billing Cashier", "CASHIER")
        )
        cashier_id = cursor.lastrowid
        cursor.execute(
            """INSERT INTO user_settings (user_id, theme, currency, default_tax_rate)
               VALUES (?, 'dark', '₹', 5.0);""",
            (cashier_id,)
        )
        logger.info("Default users seeded successfully.")

    # 2. Seed Menu Items
    cursor.execute("SELECT COUNT(*) FROM menu_items;")
    menu_count = cursor.fetchone()[0]
    if menu_count == 0:
        logger.info("Seeding standard restaurant menu catalog...")
        for name, category, price, is_available in DEFAULT_MENU_SEED:
            cursor.execute(
                """INSERT INTO menu_items (name, category, price, is_available)
                   VALUES (?, ?, ?, ?);""",
                (name, category, str(Decimal(price).quantize(Decimal("0.01"))), is_available)
            )
        logger.info(f"Seeded {len(DEFAULT_MENU_SEED)} menu items.")

    conn.commit()


def run_migrations(conn: sqlite3.Connection) -> None:
    """Executes idempotent schema upgrades for enterprise features."""
    cursor = conn.cursor()

    # 1. Add is_active & last_login to users if missing
    cursor.execute("PRAGMA table_info(users);")
    user_cols = {r[1] for r in cursor.fetchall()}
    if "is_active" not in user_cols:
        cursor.execute("ALTER TABLE users ADD COLUMN is_active INTEGER NOT NULL DEFAULT 1;")
    if "last_login" not in user_cols:
        cursor.execute("ALTER TABLE users ADD COLUMN last_login TIMESTAMP;")

    # 1b. Add special_instructions to orders if missing
    cursor.execute("PRAGMA table_info(orders);")
    order_cols = {r[1] for r in cursor.fetchall()}
    if "special_instructions" not in order_cols:
        cursor.execute("ALTER TABLE orders ADD COLUMN special_instructions TEXT DEFAULT '';")
    if "waiter_id" not in order_cols:
        cursor.execute("ALTER TABLE orders ADD COLUMN waiter_id INTEGER REFERENCES users(id);")
    if "picked_up_at" not in order_cols:
        cursor.execute("ALTER TABLE orders ADD COLUMN picked_up_at TIMESTAMP;")
    if "served_at" not in order_cols:
        cursor.execute("ALTER TABLE orders ADD COLUMN served_at TIMESTAMP;")

    # 1c. Add waiter_id to restaurant_tables if missing
    cursor.execute("PRAGMA table_info(restaurant_tables);")
    table_cols = {r[1] for r in cursor.fetchall()}
    if "waiter_id" not in table_cols:
        cursor.execute("ALTER TABLE restaurant_tables ADD COLUMN waiter_id INTEGER REFERENCES users(id);")

    # 2. Restaurant Profile & Legal Info
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS restaurant_profile (
        id INTEGER PRIMARY KEY CHECK (id = 1),
        restaurant_name TEXT NOT NULL DEFAULT 'TQM Multi-Cuisine Restaurant',
        tagline TEXT DEFAULT 'Excellence in Food & Service',
        address TEXT DEFAULT '123 MG Road, Connaught Place, New Delhi',
        phone TEXT DEFAULT '+91 98765 43210',
        email TEXT DEFAULT 'contact@tqmrestaurant.com',
        gstin TEXT DEFAULT '07AAAAA0000A1Z5',
        fssai_license TEXT DEFAULT '10019011000123',
        receipt_header TEXT DEFAULT 'Thank you for dining with us!',
        receipt_footer TEXT DEFAULT 'Goods once sold cannot be returned. Please visit again!',
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    """)
    cursor.execute("SELECT COUNT(*) FROM restaurant_profile;")
    if cursor.fetchone()[0] == 0:
        cursor.execute("INSERT INTO restaurant_profile (id) VALUES (1);")

    # 3. Enterprise Billing & Tax Configuration
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS billing_config (
        id INTEGER PRIMARY KEY CHECK (id = 1),
        cgst_rate NUMERIC NOT NULL DEFAULT 2.5,
        sgst_rate NUMERIC NOT NULL DEFAULT 2.5,
        service_charge_rate NUMERIC NOT NULL DEFAULT 0.0,
        enable_service_charge INTEGER NOT NULL DEFAULT 0,
        enable_discounts INTEGER NOT NULL DEFAULT 1,
        max_discount_percent NUMERIC NOT NULL DEFAULT 25.0,
        round_off_total INTEGER NOT NULL DEFAULT 1,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    """)
    cursor.execute("SELECT COUNT(*) FROM billing_config;")
    if cursor.fetchone()[0] == 0:
        cursor.execute("INSERT INTO billing_config (id) VALUES (1);")

    # 4. Roles & Permissions Matrix
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS roles_permissions (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        role TEXT NOT NULL,
        module TEXT NOT NULL,
        permission_key TEXT NOT NULL,
        is_granted INTEGER NOT NULL DEFAULT 1,
        UNIQUE(role, module, permission_key)
    );
    """)

    # 5. Tamper-Evident Security & Audit Trail
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS audit_logs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        username TEXT NOT NULL,
        action TEXT NOT NULL,
        module TEXT NOT NULL,
        details TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (user_id) REFERENCES users(id)
    );
    """)

    # 6. Customer Feedback & Satisfaction (Q08)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS customer_feedback (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        order_id INTEGER,
        customer_name TEXT DEFAULT 'Guest',
        table_number TEXT,
        rating INTEGER NOT NULL CHECK (rating >= 1 AND rating <= 5),
        nps_score INTEGER DEFAULT 9,
        feedback_status TEXT DEFAULT 'RESOLVED',
        comment TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (order_id) REFERENCES orders(id)
    );
    """)

    # 6b. Customer Floor Service Requests
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS service_requests (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        table_number TEXT NOT NULL,
        order_id INTEGER,
        customer_id INTEGER,
        customer_name TEXT DEFAULT 'Guest',
        request_type TEXT NOT NULL,
        notes TEXT DEFAULT '',
        status TEXT NOT NULL DEFAULT 'PENDING',
        assigned_waiter_id INTEGER,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        resolved_at TIMESTAMP,
        FOREIGN KEY (order_id) REFERENCES orders(id),
        FOREIGN KEY (customer_id) REFERENCES users(id),
        FOREIGN KEY (assigned_waiter_id) REFERENCES users(id)
    );
    """)
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_service_requests_status ON service_requests(status);")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_service_requests_waiter ON service_requests(assigned_waiter_id);")

    # 7. Restaurant Floor & Table Management (Phase E)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS restaurant_tables (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        table_number TEXT UNIQUE NOT NULL,
        zone TEXT NOT NULL DEFAULT 'Main Dining',
        capacity INTEGER NOT NULL DEFAULT 4,
        status TEXT NOT NULL DEFAULT 'VACANT',
        active_order_id INTEGER,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (active_order_id) REFERENCES orders(id)
    );
    """)

    cursor.execute("SELECT COUNT(*) FROM restaurant_tables;")
    if cursor.fetchone()[0] == 0:
        default_tables = [
            ("T-1", "Main Dining", 4, "VACANT"),
            ("T-2", "Main Dining", 4, "VACANT"),
            ("T-3", "Main Dining", 2, "VACANT"),
            ("T-4", "Main Dining", 6, "VACANT"),
            ("P-1", "Patio Garden", 4, "VACANT"),
            ("P-2", "Patio Garden", 4, "VACANT"),
            ("F-1", "Family Section", 8, "VACANT"),
            ("F-2", "Family Section", 6, "VACANT"),
            ("C-1", "Counter / Bar", 2, "VACANT"),
            ("C-2", "Counter / Bar", 2, "VACANT")
        ]
        cursor.executemany(
            """INSERT INTO restaurant_tables (table_number, zone, capacity, status)
               VALUES (?, ?, ?, ?);""",
            default_tables
        )

    # 8. Ensure All 5 Roles Exist (Admin, Manager, Cashier, Chef, Customer)
    existing_roles = {r[0] for r in cursor.execute("SELECT role FROM users;").fetchall()}
    if "CHEF" not in existing_roles:
        chef_hash = hash_password("Chef@123")
        cursor.execute(
            """INSERT INTO users (username, password_hash, full_name, role, is_active)
               VALUES ('chef1', ?, 'Executive Head Chef (Vikram)', 'CHEF', 1);""",
            (chef_hash,)
        )
        c_id = cursor.lastrowid
        cursor.execute("INSERT INTO user_settings (user_id, theme, currency) VALUES (?, 'dark', '₹');", (c_id,))

    if "CUSTOMER" not in existing_roles:
        cust_hash = hash_password("Customer@123")
        cursor.execute(
            """INSERT INTO users (username, password_hash, full_name, role, is_active)
               VALUES ('customer1', ?, 'Guest Diner (Ananya Roy)', 'CUSTOMER', 1);""",
            (cust_hash,)
        )
        cu_id = cursor.lastrowid
        cursor.execute("INSERT INTO user_settings (user_id, theme, currency) VALUES (?, 'dark', '₹');", (cu_id,))

    if "MANAGER" not in existing_roles:
        mgr_hash = hash_password("Manager@123")
        cursor.execute(
            """INSERT INTO users (username, password_hash, full_name, role, is_active)
               VALUES ('manager1', ?, 'Operations Floor Manager', 'MANAGER', 1);""",
            (mgr_hash,)
        )
        m_id = cursor.lastrowid
        cursor.execute("INSERT INTO user_settings (user_id, theme, currency) VALUES (?, 'dark', '₹');", (m_id,))

    if "WAITER" not in existing_roles:
        waiter_hash = hash_password("Waiter@123")
        cursor.execute(
            """INSERT INTO users (username, password_hash, full_name, role, is_active)
               VALUES ('waiter1', ?, 'Floor Server (Rahul Sharma)', 'WAITER', 1);""",
            (waiter_hash,)
        )
        w_id = cursor.lastrowid
        cursor.execute("INSERT INTO user_settings (user_id, theme, currency) VALUES (?, 'dark', '₹');", (w_id,))

    cursor.execute("SELECT COUNT(*) FROM customer_feedback;")
    if cursor.fetchone()[0] == 0:
        feedbacks = [
            (None, "Aarav Sharma", "Table 4", 5, "Outstanding butter chicken and quick counter service! Will visit again."),
            (None, "Priya Nair", "Table 2", 5, "Paneer tikka was exceptionally fresh and smoky. Loved the service."),
            (None, "Rohan Verma", "Table 7", 4, "Great food taste and neat billing receipt. Garlic naan was very soft."),
            (None, "Ananya Sen", "Takeaway", 5, "Fast takeaway packing and authentic Biryani aroma. 5 stars!"),
            (None, "Vikram Malhotra", "Table 1", 4, "Crispy veg spring rolls and refreshing mint cooler. Friendly staff."),
        ]
        cursor.executemany(
            """INSERT INTO customer_feedback (order_id, customer_name, table_number, rating, comment)
               VALUES (?, ?, ?, ?, ?);""",
            feedbacks
        )

    conn.commit()


def initialize_database(db_manager: DatabaseManager = db) -> None:
    """Ensures schema is created, initial seed data populated, and migrations applied."""
    conn = db_manager.get_connection()
    try:
        init_schema(conn)
        seed_initial_data(conn)
        run_migrations(conn)
        logger.info(f"Database at {db_manager.db_path} ready for operations.")
    finally:
        conn.close()
