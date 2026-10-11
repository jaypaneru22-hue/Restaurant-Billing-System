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
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id)
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

-- Performance and reporting indexes
CREATE INDEX IF NOT EXISTS idx_orders_created_at ON orders(created_at);
CREATE INDEX IF NOT EXISTS idx_orders_status ON orders(status);
CREATE INDEX IF NOT EXISTS idx_bills_billed_at ON bills(billed_at);
CREATE INDEX IF NOT EXISTS idx_menu_category ON menu_items(category);
"""


def init_schema(conn: sqlite3.Connection) -> None:
    """Executes the DDL schema against the provided connection."""
    cursor = conn.cursor()
    cursor.executescript(SCHEMA_SQL)
    conn.commit()
    logger.info("Database schema initialized successfully with all indexes and constraints.")
