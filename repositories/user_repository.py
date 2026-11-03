"""Repository for user persistence and credential storage."""
from typing import Optional, List
from datetime import datetime
from database.db import DatabaseManager, db
from models.user import User
from utils.logger import logger


class UserRepository:
    def __init__(self, db_manager: DatabaseManager = db):
        self.db = db_manager

    def _row_to_user(self, row) -> Optional[User]:
        if not row:
            return None
        # Handle backward compatibility if is_active or last_login columns are absent
        is_active = bool(row["is_active"]) if "is_active" in row.keys() else True
        last_login = row["last_login"] if "last_login" in row.keys() else None
        return User(
            id=row["id"],
            username=row["username"],
            password_hash=row["password_hash"],
            full_name=row["full_name"],
            role=row["role"],
            is_active=is_active,
            last_login=last_login,
            created_at=row["created_at"],
            updated_at=row["updated_at"]
        )

    def get_by_id(self, user_id: int) -> Optional[User]:
        row = self.db.fetchone(
            "SELECT * FROM users WHERE id = ?;",
            (user_id,)
        )
        return self._row_to_user(row)

    def get_by_username(self, username: str) -> Optional[User]:
        row = self.db.fetchone(
            "SELECT * FROM users WHERE username = ?;",
            (username.strip(),)
        )
        return self._row_to_user(row)

    def create(self, username: str, password_hash: str, full_name: str, role: str = "CASHIER", is_active: bool = True) -> User:
        with self.db.transaction() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """INSERT INTO users (username, password_hash, full_name, role, is_active)
                   VALUES (?, ?, ?, ?, ?);""",
                (username.strip(), password_hash, full_name.strip(), role.upper(), 1 if is_active else 0)
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

    def update_staff(self, user_id: int, full_name: str, role: str, is_active: bool) -> bool:
        """Admin update of staff details, role, and operational status."""
        with self.db.transaction() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """UPDATE users
                   SET full_name = ?, role = ?, is_active = ?, updated_at = CURRENT_TIMESTAMP
                   WHERE id = ?;""",
                (full_name.strip(), role.upper(), 1 if is_active else 0, user_id)
            )
            return cursor.rowcount > 0

    def toggle_status(self, user_id: int, is_active: bool) -> bool:
        """Activates or deactivates a user account."""
        with self.db.transaction() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """UPDATE users
                   SET is_active = ?, updated_at = CURRENT_TIMESTAMP
                   WHERE id = ?;""",
                (1 if is_active else 0, user_id)
            )
            return cursor.rowcount > 0

    def reset_password(self, user_id: int, new_password_hash: str) -> bool:
        return self.update_password(user_id, new_password_hash)

    def delete(self, user_id: int) -> bool:
        """Deletes user if not the last active administrator."""
        with self.db.transaction() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT role FROM users WHERE id = ?;", (user_id,))
            user_row = cursor.fetchone()
            if not user_row:
                return False
            if user_row["role"] == "ADMIN":
                cursor.execute("SELECT COUNT(*) AS c FROM users WHERE role = 'ADMIN';")
                admin_count = cursor.fetchone()["c"]
                if admin_count <= 1:
                    raise ValueError("Cannot delete the only administrative account.")
            cursor.execute("DELETE FROM users WHERE id = ?;", (user_id,))
            return cursor.rowcount > 0

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

    def update_last_login(self, user_id: int, timestamp: Optional[str] = None) -> bool:
        """Updates the last_login timestamp for a user after successful authentication."""
        if not timestamp:
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        with self.db.transaction() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """UPDATE users SET last_login = ?, updated_at = CURRENT_TIMESTAMP
                   WHERE id = ?;""",
                (timestamp, user_id)
            )
            logger.info(f"Updated last_login for user_id={user_id} to '{timestamp}'")
            return cursor.rowcount > 0

    def list_all(self) -> List[User]:
        rows = self.db.fetchall(
            "SELECT * FROM users ORDER BY id ASC;"
        )
        return [self._row_to_user(r) for r in rows]


# Global user repository instance
user_repository = UserRepository()
