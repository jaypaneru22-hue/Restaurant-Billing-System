"""Repository for user persistence and credential storage."""
from typing import Optional, List
from database.db import DatabaseManager, db
from models.user import User
from utils.logger import logger


class UserRepository:
    def __init__(self, db_manager: DatabaseManager = db):
        self.db = db_manager

    def get_by_id(self, user_id: int) -> Optional[User]:
        row = self.db.fetchone(
            "SELECT id, username, password_hash, full_name, role, created_at, updated_at FROM users WHERE id = ?;",
            (user_id,)
        )
        if not row:
            return None
        return User(
            id=row["id"],
            username=row["username"],
            password_hash=row["password_hash"],
            full_name=row["full_name"],
            role=row["role"],
            created_at=row["created_at"],
            updated_at=row["updated_at"]
        )

    def get_by_username(self, username: str) -> Optional[User]:
        row = self.db.fetchone(
            "SELECT id, username, password_hash, full_name, role, created_at, updated_at FROM users WHERE username = ?;",
            (username.strip(),)
        )
        if not row:
            return None
        return User(
            id=row["id"],
            username=row["username"],
            password_hash=row["password_hash"],
            full_name=row["full_name"],
            role=row["role"],
            created_at=row["created_at"],
            updated_at=row["updated_at"]
        )

    def create(self, username: str, password_hash: str, full_name: str, role: str = "CASHIER") -> User:
        with self.db.transaction() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """INSERT INTO users (username, password_hash, full_name, role)
                   VALUES (?, ?, ?, ?);""",
                (username.strip(), password_hash, full_name.strip(), role.upper())
            )
            user_id = cursor.lastrowid
            # Also create default settings
            cursor.execute(
                """INSERT INTO user_settings (user_id, theme, currency, default_tax_rate)
                   VALUES (?, 'dark', '₹', 5.0);""",
                (user_id,)
            )
            logger.info(f"User created successfully: id={user_id}, username={username}, role={role}")
        return self.get_by_id(user_id)

    def update_profile(self, user_id: int, full_name: str) -> bool:
        with self.db.transaction() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """UPDATE users SET full_name = ?, updated_at = CURRENT_TIMESTAMP
                   WHERE id = ?;""",
                (full_name.strip(), user_id)
            )
            return cursor.rowcount > 0

    def update_password(self, user_id: int, new_password_hash: str) -> bool:
        with self.db.transaction() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """UPDATE users SET password_hash = ?, updated_at = CURRENT_TIMESTAMP
                   WHERE id = ?;""",
                (new_password_hash, user_id)
            )
            logger.info(f"Password updated for user id={user_id}")
            return cursor.rowcount > 0

    def list_all(self) -> List[User]:
        rows = self.db.fetchall(
            "SELECT id, username, password_hash, full_name, role, created_at, updated_at FROM users ORDER BY id ASC;"
        )
        return [
            User(
                id=r["id"],
                username=r["username"],
                password_hash=r["password_hash"],
                full_name=r["full_name"],
                role=r["role"],
                created_at=r["created_at"],
                updated_at=r["updated_at"]
            )
            for r in rows
        ]
