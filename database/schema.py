"""DDL schema definitions and table creation for SQLite database."""
import sqlite3
from utils.logger import logger

SCHEMA_SQL = """
-- Users table for authentication and RBAC
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT UNIQUE NOT NULL,
    password_hash TEXT NOT NULL,
    full_name TEXT NOT NULL,
    role TEXT NOT NULL DEFAULT 'CASHIER',
    is_active INTEGER NOT NULL DEFAULT 1,
    last_login TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- User settings and preferences (Feature 5: User Profile Settings & Feature 3: Persistent Theme)
CREATE TABLE IF NOT EXISTS user_settings (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER UNIQUE NOT NULL,
    theme TEXT NOT NULL DEFAULT 'dark',
    currency TEXT NOT NULL DEFAULT '₹',
    default_tax_rate NUMERIC NOT NULL DEFAULT 5.0,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);

-- Menu items catalog
CREATE TABLE IF NOT EXISTS menu_items (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    category TEXT NOT NULL,
    price NUMERIC NOT NULL,
    is_available INTEGER NOT NULL DEFAULT 1,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(name, category)
);

-- Orders table
CREATE TABLE IF NOT EXISTS orders (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    order_number TEXT UNIQUE NOT NULL,
    user_id INTEGER NOT NULL,
    table_number TEXT DEFAULT 'Takeaway',
    customer_name TEXT DEFAULT 'Walk-in Customer',
    status TEXT NOT NULL DEFAULT 'PENDING',
    special_instructions TEXT DEFAULT '',
    waiter_id INTEGER,
    picked_up_at TIMESTAMP,
    served_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id),
    FOREIGN KEY (waiter_id) REFERENCES users(id)
);

-- Order items with historical price and name snapshot protection
CREATE TABLE IF NOT EXISTS order_items (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    order_id INTEGER NOT NULL,
    menu_item_id INTEGER NOT NULL,
    item_name TEXT NOT NULL,
    unit_price NUMERIC NOT NULL,
    quantity INTEGER NOT NULL CHECK(quantity > 0),
    line_total NUMERIC NOT NULL,
    FOREIGN KEY (order_id) REFERENCES orders(id) ON DELETE CASCADE,
    FOREIGN KEY (menu_item_id) REFERENCES menu_items(id)
);

-- Finalized Bills and Invoices
CREATE TABLE IF NOT EXISTS bills (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    bill_number TEXT UNIQUE NOT NULL,
    order_id INTEGER UNIQUE NOT NULL,
    subtotal NUMERIC NOT NULL,
    tax_rate NUMERIC NOT NULL DEFAULT 5.0,
    tax_amount NUMERIC NOT NULL,
    discount_percent NUMERIC NOT NULL DEFAULT 0.0,
    discount_amount NUMERIC NOT NULL DEFAULT 0.0,
    final_total NUMERIC NOT NULL,
    payment_method TEXT NOT NULL,
    payment_status TEXT NOT NULL DEFAULT 'PAID',
    billed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (order_id) REFERENCES orders(id)
);

-- Restaurant tables and floor layout
CREATE TABLE IF NOT EXISTS restaurant_tables (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    table_number TEXT UNIQUE NOT NULL,
    zone TEXT NOT NULL DEFAULT 'Main Dining',
    capacity INTEGER NOT NULL DEFAULT 4,
    status TEXT NOT NULL DEFAULT 'VACANT',
    active_order_id INTEGER,
    waiter_id INTEGER,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (active_order_id) REFERENCES orders(id),
    FOREIGN KEY (waiter_id) REFERENCES users(id)
);

-- Customer Floor Service Requests
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

-- Performance and reporting indexes
CREATE INDEX IF NOT EXISTS idx_orders_created_at ON orders(created_at);
CREATE INDEX IF NOT EXISTS idx_orders_status ON orders(status);
CREATE INDEX IF NOT EXISTS idx_bills_billed_at ON bills(billed_at);
CREATE INDEX IF NOT EXISTS idx_menu_category ON menu_items(category);
CREATE INDEX IF NOT EXISTS idx_service_requests_status ON service_requests(status);
CREATE INDEX IF NOT EXISTS idx_service_requests_waiter ON service_requests(assigned_waiter_id);
"""


def init_schema(conn: sqlite3.Connection) -> None:
    """Executes the DDL schema against the provided connection."""
    cursor = conn.cursor()
    cursor.executescript(SCHEMA_SQL)
    conn.commit()
    logger.info("Database schema initialized successfully with all indexes and constraints.")
