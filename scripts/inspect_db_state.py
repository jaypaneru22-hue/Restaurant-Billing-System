import sqlite3
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from config.settings import DEFAULT_DB_PATH

def inspect_db():
    print(f"Database Path: {DEFAULT_DB_PATH.resolve()}")
    print(f"Exists: {DEFAULT_DB_PATH.exists()}\n")

    conn = sqlite3.connect(DEFAULT_DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name;")
    tables = [r[0] for r in cursor.fetchall()]

    for t in tables:
        cursor.execute(f"PRAGMA table_info(`{t}`);")
        cols = [c[1] for c in cursor.fetchall()]
        cursor.execute(f"SELECT COUNT(*) FROM `{t}`;")
        cnt = cursor.fetchone()[0]
        print(f"Table '{t}' ({cnt} rows):")
        print(f"  Columns: {', '.join(cols)}")
        if cnt > 0 and cnt <= 15:
            cursor.execute(f"SELECT * FROM `{t}` LIMIT 10;")
            rows = cursor.fetchall()
            for r in rows:
                print(f"    {dict(r)}")
        elif cnt > 15:
            cursor.execute(f"SELECT * FROM `{t}` LIMIT 3;")
            rows = cursor.fetchall()
            for r in rows:
                print(f"    [Sample] {dict(r)}")
        print()

    conn.close()

if __name__ == "__main__":
    inspect_db()
