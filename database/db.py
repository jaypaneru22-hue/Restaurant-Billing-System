"""Database connection manager with foreign-key enforcement and transaction management."""
import sqlite3
from pathlib import Path
from contextlib import contextmanager
from typing import Optional, Generator, Any, List, Tuple
from config.settings import DEFAULT_DB_PATH
from utils.logger import logger


class DatabaseManager:
    """Manages SQLite connections, transactions, and parameter handling."""

    def __init__(self, db_path: Optional[Path | str] = None):
        self.db_path = Path(db_path) if db_path else DEFAULT_DB_PATH
        self.db_path.parent.mkdir(parents=True, exist_ok=True)

    def get_connection(self) -> sqlite3.Connection:
        """Creates and returns a connection with foreign keys enabled and Row factory."""
        conn = sqlite3.connect(self.db_path, timeout=10.0)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA foreign_keys = ON;")
        return conn

    @contextmanager
    def transaction(self) -> Generator[sqlite3.Connection, None, None]:
        """Context manager for atomic transaction block with automatic rollback on error."""
        conn = self.get_connection()
        try:
            yield conn
            conn.commit()
        except Exception as e:
            conn.rollback()
            logger.error(f"Transaction rolled back due to error: {e}", exc_info=True)
            raise
        finally:
            conn.close()

    def execute(self, query: str, params: Tuple[Any, ...] = ()) -> int:
        """Executes a non-query SQL command and returns the last row ID."""
        with self.transaction() as conn:
            cursor = conn.cursor()
            cursor.execute(query, params)
            return cursor.lastrowid or cursor.rowcount

    def fetchone(self, query: str, params: Tuple[Any, ...] = ()) -> Optional[sqlite3.Row]:
        """Fetches a single row from the database."""
        conn = self.get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute(query, params)
            return cursor.fetchone()
        finally:
            conn.close()

    def fetchall(self, query: str, params: Tuple[Any, ...] = ()) -> List[sqlite3.Row]:
        """Fetches all matching rows from the database."""
        conn = self.get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute(query, params)
            return cursor.fetchall()
        finally:
            conn.close()


# Global default database instance
db = DatabaseManager()
