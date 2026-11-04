import sqlite3
import shutil
import sys
from datetime import datetime
from pathlib import Path

# Add project root to sys.path
BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

from config.settings import DEFAULT_DB_PATH, DATA_DIR

BACKUPS_DIR = DATA_DIR / "backups"

def create_and_verify_backup():
    print("=" * 65)
    print("RESTOPRO: DATABASE BACKUP AND INTEGRITY VERIFICATION")
    print("=" * 65)

    if not DEFAULT_DB_PATH.exists():
        raise FileNotFoundError(f"Database file does not exist at {DEFAULT_DB_PATH}")

    BACKUPS_DIR.mkdir(parents=True, exist_ok=True)
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_file = BACKUPS_DIR / f"restaurant_pre_cleanup_{ts}.bak"

    print(f"Source Database : {DEFAULT_DB_PATH.resolve()}")
    print(f"Target Backup   : {backup_file.resolve()}")

    # 1. Copy database file cleanly
    shutil.copy2(DEFAULT_DB_PATH, backup_file)

    # 2. Verify file existence and non-zero size
    if not backup_file.exists():
        raise RuntimeError(f"Backup file was not created at {backup_file}")
    
    size_bytes = backup_file.stat().st_size
    if size_bytes == 0:
        raise RuntimeError(f"Backup file was created but has 0 bytes.")
    
    print(f"Backup Size     : {size_bytes:,} bytes ({size_bytes / 1024:.2f} KB)")

    # 3. Connect to backup and perform SQLite integrity check
    conn = sqlite3.connect(backup_file)
    cursor = conn.cursor()

    cursor.execute("PRAGMA integrity_check;")
    integrity = cursor.fetchall()
    print(f"Integrity Check : {integrity}")
    if integrity != [("ok",)]:
        raise RuntimeError(f"Integrity check failed: {integrity}")

    # 4. Count tables and rows in backup
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name;")
    tables = [r[0] for r in cursor.fetchall()]
    print(f"\nTables Verified in Backup ({len(tables)} tables):")
    total_records = 0
    for t in tables:
        cursor.execute(f"SELECT COUNT(*) FROM `{t}`;")
        cnt = cursor.fetchone()[0]
        total_records += cnt
        print(f"  - {t:<25}: {cnt:>4} rows")

    conn.close()

    print(f"\nTotal Records in Backup: {total_records}")
    print("[SUCCESS] Backup created and verified cleanly.")
    return backup_file

if __name__ == "__main__":
    create_and_verify_backup()
