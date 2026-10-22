"""Database administration, safe backup, demo-data cleanup, and seed recovery suite.

Placement-Ready Utility for BBAT104 Restaurant Billing System.
Student: Jay Paneru (Reg: 2410302024)
Quality Goal: Q08 - Improve User Satisfaction
"""
import sys
import shutil
import sqlite3
import argparse
from datetime import datetime, timedelta
from decimal import Decimal
from pathlib import Path

# Add project root to sys.path
BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))

from config.settings import DEFAULT_DB_PATH, DATA_DIR
from database.migrations import initialize_database
from database.schema import init_schema
from utils.security import hash_password
from utils.logger import logger

# Reconfigure standard output for Windows console safety
if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

BACKUPS_DIR = DATA_DIR / "backups"


def get_connection(db_path: Path = DEFAULT_DB_PATH) -> sqlite3.Connection:
    conn = sqlite3.connect(db_path)
    conn.execute("PRAGMA foreign_keys = ON;")
    return conn


def cmd_status(args):
    """Displays database status, tables, and record counts."""
    print("=" * 65)
    print(" RESTAURANT BILLING SYSTEM - DATABASE STATUS AUDIT")
    print("=" * 65)
    print(f"Database Path : {DEFAULT_DB_PATH.resolve()}")
    exists = DEFAULT_DB_PATH.exists()
    print(f"Exists        : {exists}")

    if not exists:
        print("\nDatabase has not been initialized yet.")
        print("Run: python scripts/manage_db.py reset --confirm")
        return

    size_kb = DEFAULT_DB_PATH.stat().st_size / 1024
    print(f"File Size     : {size_kb:.2f} KB")

    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name;")
    tables = [row[0] for row in cursor.fetchall() if row[0] != "sqlite_sequence"]

    print("\n[Master Data & Seed Tables]")
    for t in ["users", "user_settings", "menu_items"]:
        if t in tables:
            cursor.execute(f"SELECT COUNT(*) FROM {t};")
            cnt = cursor.fetchone()[0]
            print(f"  • {t:<15}: {cnt:>4} records")

    print("\n[Transactional & Demonstration Tables]")
    for t in ["orders", "order_items", "bills"]:
        if t in tables:
            cursor.execute(f"SELECT COUNT(*) FROM {t};")
            cnt = cursor.fetchone()[0]
            print(f"  • {t:<15}: {cnt:>4} records")

    # Check admin user
    cursor.execute("SELECT id, username, full_name, role FROM users WHERE username='admin';")
    admin = cursor.fetchone()
    print("\n[Security & Access Check]")
    if admin:
        print(f"  • Admin Account : Present (ID: {admin[0]}, User: '{admin[1]}', Role: {admin[3]})")
    else:
        print("  • Admin Account : MISSING! Run 'python scripts/manage_db.py recover-admin'")

    conn.close()
    print("=" * 65)


def create_backup() -> Path:
    """Creates a timestamped backup of the database file."""
    if not DEFAULT_DB_PATH.exists():
        raise FileNotFoundError(f"Database at {DEFAULT_DB_PATH} does not exist.")

    BACKUPS_DIR.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_path = BACKUPS_DIR / f"restaurant_{timestamp}.bak"
    shutil.copy2(DEFAULT_DB_PATH, backup_path)
    print(f" [BACKUP CREATED] Saved snapshot to: {backup_path.name}")
    logger.info(f"Database backup created: {backup_path}")
    return backup_path


def cmd_backup(args):
    """CLI handler for manual backup creation."""
    try:
        backup_path = create_backup()
        print(f"Full path: {backup_path.resolve()}")
    except Exception as e:
        print(f"Error creating backup: {e}", file=sys.stderr)
        sys.exit(1)


def cmd_list_backups(args):
    """Lists existing backups."""
    print("=" * 65)
    print(" [DATABASE BACKUP ARCHIVES]")
    print("=" * 65)
    if not BACKUPS_DIR.exists():
        print("No backups directory found.")
        return

    backups = sorted(BACKUPS_DIR.glob("*.bak"), reverse=True)
    if not backups:
        print("No backups found in data/backups/.")
        return

    for b in backups:
        size_kb = b.stat().st_size / 1024
        mtime = datetime.fromtimestamp(b.stat().st_mtime).strftime("%Y-%m-%d %H:%M:%S")
        print(f"  * {b.name:<32} ({size_kb:>6.2f} KB) - {mtime}")
    print("=" * 65)


def cmd_clean_demo(args):
    """Cleans all sample transaction data while strictly preserving users, settings, and menu."""
    if not DEFAULT_DB_PATH.exists():
        print("Database does not exist. Nothing to clean.")
        return

    if not args.confirm:
        print("[CAUTION] This will delete all sample orders, order items, and bills!")
        print("          Master data (admin/cashier accounts and 26 menu items) will be PRESERVED.")
        confirm = input("Are you sure you want to proceed? (yes/no): ").strip().lower()
        if confirm not in ("y", "yes"):
            print("Operation aborted by user.")
            return

    # Step 1: Automatic backup before destructive cleanup
    create_backup()

    # Step 2: Clean transactions in atomic foreign-key safe order
    conn = get_connection()
    try:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM bills;")
        cursor.execute("DELETE FROM order_items;")
        cursor.execute("DELETE FROM orders;")

        # Reset autoincrement sequence for transactional tables
        cursor.execute("DELETE FROM sqlite_sequence WHERE name IN ('orders', 'order_items', 'bills');")
        conn.commit()
        print("[OK] Demo transactions cleaned successfully.")
        print("     - Deleted bills, order_items, and orders.")
        print("     - Reset autoincrement sequences.")
        print("     - Preserved users and menu catalog.")
        logger.info("Demo transactions cleared by manage_db.py.")
    except Exception as e:
        conn.rollback()
        print(f"Error during cleanup: {e}", file=sys.stderr)
        sys.exit(1)
    finally:
        conn.close()


def cmd_seed_demo(args):
    """Populates realistic demo transactions across past 5 days for presentation."""
    if not DEFAULT_DB_PATH.exists():
        print("Initializing schema and master seeds first...")
        initialize_database()

    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM orders;")
    existing_orders = cursor.fetchone()[0]
    conn.close()

    if existing_orders > 0 and not args.force:
        print(f"[WARN] Database already contains {existing_orders} orders.")
        print("       To re-seed demo transactions, run:")
        print("       python scripts/manage_db.py clean-demo --confirm")
        print("       python scripts/manage_db.py seed-demo")
        print("       Or use: python scripts/manage_db.py seed-demo --force")
        return

    from database.db import db
    from services.menu_service import menu_service
    from services.auth_service import auth_service
    from services.order_service import order_service
    from services.billing_service import billing_service

    items = menu_service.get_all_items(available_only=True)
    if not items:
        print("Error: No menu items available to seed orders.", file=sys.stderr)
        return

    admin_user = auth_service.user_repo.get_by_username("admin")
    user_id = admin_user.id if admin_user else 1

    customers = [
        ("Rahul Verma", "Table 1", ["CASH", "UPI"]),
        ("Pooja Nair", "Table 3", ["CARD", "UPI"]),
        ("Amitabh Sen", "Takeaway", ["CASH"]),
        ("Sneha Kulkarni", "Table 5", ["CARD"]),
        ("Vikram Singh", "Table 2", ["UPI"]),
        ("Ananya Roy", "Table 4", ["CARD", "CASH"]),
        ("Rajesh Khanna", "Table 6", ["UPI"]),
        ("Kavita Rao", "Takeaway", ["CASH"]),
        ("Rohan Joshi", "Table 2", ["UPI"]),
        ("Meera Patel", "Table 1", ["CARD"])
    ]

    today = datetime.now()
    payment_methods = ["CASH", "CARD", "UPI"]

    print("Seeding 10 demonstration transactions across the past 5 days...")
    seeded_count = 0
    for idx, (cust_name, table, pay_pref) in enumerate(customers):
        days_ago = idx % 5
        ord_date = today - timedelta(days=days_ago, hours=(idx * 2) % 12, minutes=idx * 7)

        dish1 = items[idx % len(items)]
        dish2 = items[(idx + 3) % len(items)]
        entries = [(dish1.id, 1 + (idx % 3)), (dish2.id, 1 + ((idx + 1) % 2))]

        ok, _, order = order_service.create_order(user_id, table, cust_name, entries)
        if ok and order:
            seeded_count += 1
            if idx < 8:
                pm = pay_pref[0] if pay_pref else payment_methods[idx % len(payment_methods)]
                discount = Decimal("5.0") if idx % 3 == 0 else Decimal("0.0")
                ok_bill, _, bill = billing_service.finalize_bill(order.id, pm, discount, Decimal("5.0"))
                if ok_bill and bill:
                    db.execute(
                        "UPDATE orders SET created_at = ? WHERE id = ?;",
                        (ord_date.strftime("%Y-%m-%d %H:%M:%S"), order.id)
                    )
                    db.execute(
                        "UPDATE bills SET billed_at = ? WHERE id = ?;",
                        (ord_date.strftime("%Y-%m-%d %H:%M:%S"), bill.id)
                    )
            elif idx == 8:
                pass  # Keep as PENDING
            else:
                order_service.cancel_order(order.id)

    print(f"[OK] Successfully seeded {seeded_count} demonstration transactions.")
    logger.info("Demo transactions re-seeded successfully.")


def cmd_reset(args):
    """Full database reset with backup and recreation of initial master seeds."""
    if not args.confirm:
        print("[DANGER] This will completely ERASE the current database and reinitialize fresh seeds!")
        confirm = input("Type 'CONFIRM' to proceed: ").strip()
        if confirm != "CONFIRM":
            print("Operation aborted.")
            return

    if DEFAULT_DB_PATH.exists():
        create_backup()
        try:
            DEFAULT_DB_PATH.unlink()
            print("Removed existing database file.")
        except Exception as e:
            print(f"Error removing existing database: {e}", file=sys.stderr)
            sys.exit(1)

    initialize_database()
    print("[OK] Database cleanly reset with default master seeds (users & menu catalog).")


def cmd_recover_admin(args):
    """Recovers or resets the default administrator account."""
    if not DEFAULT_DB_PATH.exists():
        initialize_database()

    password = args.password if args.password else "Admin@123"
    pwd_hash = hash_password(password)

    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id FROM users WHERE username='admin';")
    admin = cursor.fetchone()

    if admin:
        cursor.execute("UPDATE users SET password_hash = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?;", (pwd_hash, admin[0]))
        print(f"[OK] Password for administrator 'admin' successfully reset to: {password}")
    else:
        cursor.execute(
            """INSERT INTO users (username, password_hash, full_name, role)
               VALUES ('admin', ?, 'Administrator (Jay Paneru)', 'ADMIN');""",
            (pwd_hash,)
        )
        admin_id = cursor.lastrowid
        cursor.execute(
            """INSERT OR IGNORE INTO user_settings (user_id, theme, currency, default_tax_rate)
               VALUES (?, 'dark', '₹', 5.0);""",
            (admin_id,)
        )
        print(f"[OK] Administrator account 'admin' created with password: {password}")

    conn.commit()
    conn.close()


def main():
    parser = argparse.ArgumentParser(description="Restaurant Billing System Database Management Suite")
    subparsers = parser.add_subparsers(dest="command", required=True)

    # status
    p_status = subparsers.add_parser("status", help="Display database status, tables, and record counts")
    p_status.set_defaults(func=cmd_status)

    # backup
    p_backup = subparsers.add_parser("backup", help="Create a timestamped backup of the database")
    p_backup.set_defaults(func=cmd_backup)

    # list-backups
    p_list = subparsers.add_parser("list-backups", help="List all backup archives in data/backups/")
    p_list.set_defaults(func=cmd_list_backups)

    # clean-demo
    p_clean = subparsers.add_parser("clean-demo", help="Clean demo transactions while preserving master data")
    p_clean.add_argument("--confirm", action="store_true", help="Confirm execution without interactive prompt")
    p_clean.set_defaults(func=cmd_clean_demo)

    # seed-demo
    p_seed = subparsers.add_parser("seed-demo", help="Seed realistic demo transactions across past 5 days")
    p_seed.add_argument("--force", action="store_true", help="Force seeding even if orders already exist")
    p_seed.set_defaults(func=cmd_seed_demo)

    # reset
    p_reset = subparsers.add_parser("reset", help="Completely reset database to pristine master seeds")
    p_reset.add_argument("--confirm", action="store_true", help="Confirm full reset without interactive prompt")
    p_reset.set_defaults(func=cmd_reset)

    # recover-admin
    p_recover = subparsers.add_parser("recover-admin", help="Reset or recover the default administrator account")
    p_recover.add_argument("--password", type=str, default="Admin@123", help="New admin password (default: Admin@123)")
    p_recover.set_defaults(func=cmd_recover_admin)

    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
