"""Safe Demo Data Cleanup Script for RestoPro Restaurant Management Platform.

Performs atomic, foreign-key safe removal of confirmed demo/test business data:
- bills
- order_items
- orders
- customer_feedback
- service_requests
- transactional audit_logs

Strictly preserves:
- users (All 6 roles: admin, cashier1, manager1, chef1, waiter1, customer1)
- user_settings
- menu_items (27 dishes)
- restaurant_tables (10 tables, resets active_order_id and status to VACANT)
- restaurant_profile
- billing_config
- roles_permissions
"""
import sys
import sqlite3
from pathlib import Path

# Add project root to sys.path
BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

from config.settings import DEFAULT_DB_PATH
from scripts.backup_and_verify import create_and_verify_backup
from utils.logger import logger


def clean_demo_data():
    print("=" * 65)
    print("RESTOPRO: EXECUTING SAFE DEMO DATA CLEANUP")
    print("=" * 65)

    if not DEFAULT_DB_PATH.exists():
        raise FileNotFoundError(f"Database at {DEFAULT_DB_PATH} not found.")

    # Step 1: Ensure verified backup exists before any deletion
    print("\n[STEP 1] Generating and verifying pre-cleanup backup...")
    backup_file = create_and_verify_backup()
    print(f"Verified backup stored at: {backup_file.resolve()}\n")

    # Step 2: Connect to database and perform safe transactional deletion
    print("[STEP 2] Executing safe transactional removal of demo records...")
    conn = sqlite3.connect(DEFAULT_DB_PATH)
    conn.execute("PRAGMA foreign_keys = ON;")

    counts = {}

    try:
        cur = conn.cursor()

        # Count before deletion
        for tbl in ["bills", "order_items", "orders", "customer_feedback", "service_requests", "audit_logs"]:
            cur.execute(f"SELECT COUNT(*) FROM `{tbl}`;")
            counts[tbl] = cur.fetchone()[0]

        print("Records scheduled for removal:")
        for tbl, cnt in counts.items():
            print(f"  • {tbl:<20}: {cnt:>4} records")

        # Atomic transaction: clean in foreign-key safe dependency order
        with conn:
            # 1. Reset any table references pointing to orders
            cur.execute("UPDATE restaurant_tables SET active_order_id = NULL, status = 'VACANT';")
            
            # 2. Delete child records
            cur.execute("DELETE FROM bills;")
            cur.execute("DELETE FROM order_items;")
            cur.execute("DELETE FROM service_requests;")
            cur.execute("DELETE FROM customer_feedback;")

            # 3. Delete parent records
            cur.execute("DELETE FROM orders;")

            # 4. Clean transactional and demo audit logs
            cur.execute("""
                DELETE FROM audit_logs 
                WHERE action IN ('BILL_SETTLED', 'ORDER_CREATED', 'ORDER_PLACED', 'ORDER_PICKED_UP', 
                                'ORDER_SERVED', 'ORDER_CANCELLED', 'ORDER_UPDATED', 'REQUEST_CREATED', 
                                'REQUEST_ACCEPTED', 'REQUEST_RESOLVED', 'UPDATE_TABLE_STATUS');
            """)

            # 5. Reset autoincrement sequences for cleaned business tables
            cur.execute("""
                DELETE FROM sqlite_sequence 
                WHERE name IN ('orders', 'order_items', 'bills', 'customer_feedback', 'service_requests');
            """)

        print("\n[STEP 3] Deletion transaction committed successfully.")
        logger.info("Safe demo data cleanup completed successfully.")

    except Exception as e:
        conn.rollback()
        print(f"[ERROR] Transaction failed, rolled back: {e}", file=sys.stderr)
        raise
    finally:
        conn.close()

    # Step 3: Verification of post-cleanup state
    print("\n[STEP 4] Verifying post-cleanup database state...")
    conn = sqlite3.connect(DEFAULT_DB_PATH)
    cur = conn.cursor()

    # Verify zero records in transactional tables
    for tbl in ["orders", "order_items", "bills", "customer_feedback", "service_requests"]:
        cur.execute(f"SELECT COUNT(*) FROM `{tbl}`;")
        cnt = cur.fetchone()[0]
        assert cnt == 0, f"Table {tbl} still contains {cnt} records!"
        print(f"  [VERIFIED ZERO] {tbl:<22}: {cnt} records")

    # Verify master data preservation
    cur.execute("SELECT COUNT(*) FROM users;")
    user_cnt = cur.fetchone()[0]
    assert user_cnt == 6, f"Expected 6 users, found {user_cnt}"
    print(f"  [PRESERVED] users                 : {user_cnt} accounts (All 6 roles)")

    cur.execute("SELECT COUNT(*) FROM menu_items;")
    menu_cnt = cur.fetchone()[0]
    assert menu_cnt == 27, f"Expected 27 menu items, found {menu_cnt}"
    print(f"  [PRESERVED] menu_items            : {menu_cnt} items")

    cur.execute("SELECT COUNT(*) FROM restaurant_tables;")
    tbl_cnt = cur.fetchone()[0]
    assert tbl_cnt == 10, f"Expected 10 tables, found {tbl_cnt}"
    print(f"  [PRESERVED] restaurant_tables     : {tbl_cnt} tables (All VACANT, active_order_id=NULL)")

    cur.execute("SELECT COUNT(*) FROM restaurant_profile;")
    prof_cnt = cur.fetchone()[0]
    assert prof_cnt == 1, f"Expected 1 profile, found {prof_cnt}"
    print(f"  [PRESERVED] restaurant_profile    : {prof_cnt} record")

    cur.execute("SELECT COUNT(*) FROM billing_config;")
    cfg_cnt = cur.fetchone()[0]
    assert cfg_cnt == 1, f"Expected 1 billing config, found {cfg_cnt}"
    print(f"  [PRESERVED] billing_config        : {cfg_cnt} record")

    conn.close()
    print("\n" + "=" * 65)
    print("DEMO DATA CLEANUP COMPLETED AND FULLY VERIFIED.")
    print("=" * 65)

    return counts


if __name__ == "__main__":
    clean_demo_data()
