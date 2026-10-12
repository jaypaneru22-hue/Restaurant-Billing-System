"""Repository for user settings and appearance preferences."""
from typing import Optional
from decimal import Decimal
from database.db import DatabaseManager, db
from models.user import UserSettings
from utils.logger import logger


class SettingsRepository:
    def __init__(self, db_manager: DatabaseManager = db):
        self.db = db_manager

    def get_by_user_id(self, user_id: int) -> UserSettings:
        """Retrieves settings for a user. If missing, inserts default row."""
        row = self.db.fetchone(
            "SELECT id, user_id, theme, currency, default_tax_rate, updated_at FROM user_settings WHERE user_id = ?;",
            (user_id,)
        )
        if not row:
            with self.db.transaction() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    """INSERT INTO user_settings (user_id, theme, currency, default_tax_rate)
                       VALUES (?, 'dark', '₹', 5.0);""",
                    (user_id,)
                )
                settings_id = cursor.lastrowid
            return UserSettings(
                id=settings_id,
                user_id=user_id,
                theme="dark",
                currency="₹",
                default_tax_rate=Decimal("5.0")
            )

        return UserSettings(
            id=row["id"],
            user_id=row["user_id"],
            theme=row["theme"],
            currency=row["currency"],
            default_tax_rate=Decimal(str(row["default_tax_rate"])),
            updated_at=row["updated_at"]
        )

    def update_theme(self, user_id: int, theme: str) -> bool:
        """Updates and persists the theme preference for a user."""
        clean_theme = theme.lower().strip()
        if clean_theme not in ["dark", "light"]:
            clean_theme = "dark"

        # Ensure record exists first
        self.get_by_user_id(user_id)

        with self.db.transaction() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """UPDATE user_settings
                   SET theme = ?, updated_at = CURRENT_TIMESTAMP
                   WHERE user_id = ?;""",
                (clean_theme, user_id)
            )
            logger.info(f"Persisted theme preference '{clean_theme}' for user id={user_id}")
            return cursor.rowcount > 0

    def update_settings(self, user_id: int, theme: str, default_tax_rate: Decimal) -> bool:
        """Updates full user preferences."""
        self.get_by_user_id(user_id)
        with self.db.transaction() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """UPDATE user_settings
                   SET theme = ?, default_tax_rate = ?, updated_at = CURRENT_TIMESTAMP
                   WHERE user_id = ?;""",
                (theme.lower(), str(default_tax_rate.quantize(Decimal("0.01"))), user_id)
            )
            return cursor.rowcount > 0
