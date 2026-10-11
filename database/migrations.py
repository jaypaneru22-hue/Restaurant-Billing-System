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


def initialize_database(db_manager: DatabaseManager = db) -> None:
    """Ensures schema is created and initial seed data populated."""
    conn = db_manager.get_connection()
    try:
        init_schema(conn)
        seed_initial_data(conn)
        logger.info(f"Database at {db_manager.db_path} ready for operations.")
    finally:
        conn.close()
