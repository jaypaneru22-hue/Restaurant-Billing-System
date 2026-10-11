"""Unit tests for DatabaseManager and transaction atomicity."""
import sqlite3
import pytest
from database.db import DatabaseManager


@pytest.fixture
def temp_db(tmp_path):
    db_file = tmp_path / "test.db"
    manager = DatabaseManager(db_file)
    with manager.transaction() as conn:
        conn.execute("CREATE TABLE parent (id INTEGER PRIMARY KEY, name TEXT);")
        conn.execute("CREATE TABLE child (id INTEGER PRIMARY KEY, parent_id INTEGER, FOREIGN KEY(parent_id) REFERENCES parent(id));")
    return manager


def test_database_foreign_key_enforcement(temp_db):
    # Trying to insert orphan child record should fail with IntegrityError
    with pytest.raises(sqlite3.IntegrityError):
        temp_db.execute("INSERT INTO child (parent_id) VALUES (999);")


def test_transaction_rollback_on_failure(temp_db):
    # Insert parent
    temp_db.execute("INSERT INTO parent (name) VALUES (?);", ("ValidParent",))
    assert len(temp_db.fetchall("SELECT * FROM parent;")) == 1

    # Attempt a transaction block that raises halfway
    with pytest.raises(ValueError):
        with temp_db.transaction() as conn:
            conn.execute("INSERT INTO parent (name) VALUES (?);", ("RollbackCandidate",))
            raise ValueError("Simulated unexpected process failure")

    # The record should not exist in the database
    rows = temp_db.fetchall("SELECT * FROM parent WHERE name = ?;", ("RollbackCandidate",))
    assert len(rows) == 0
    assert len(temp_db.fetchall("SELECT * FROM parent;")) == 1


def test_fetchone_and_fetchall(temp_db):
    temp_db.execute("INSERT INTO parent (name) VALUES (?);", ("Item1",))
    temp_db.execute("INSERT INTO parent (name) VALUES (?);", ("Item2",))

    row = temp_db.fetchone("SELECT name FROM parent WHERE name = ?;", ("Item1",))
    assert row is not None
    assert row["name"] == "Item1"

    all_rows = temp_db.fetchall("SELECT * FROM parent ORDER BY id ASC;")
    assert len(all_rows) == 2
