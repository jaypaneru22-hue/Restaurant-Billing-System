"""Repository for managing independent customer and user session tokens."""
from typing import Optional, Dict, Any, List
from datetime import datetime
from database.db import DatabaseManager, db
from utils.logger import logger


class SessionRepository:
    """Handles persistence, verification, and revocation of multi-device session tokens."""

    def __init__(self, db_manager: DatabaseManager = db):
        self.db = db_manager

    def create_session(
        self,
        token: str,
        user_id: int,
        expires_at: str,
        device_info: str = "",
        ip_address: str = ""
    ) -> Dict[str, Any]:
        """Atomically stores a newly minted session token."""
        query = """
            INSERT INTO customer_sessions (token, user_id, device_info, ip_address, expires_at, is_active)
            VALUES (?, ?, ?, ?, ?, 1);
        """
        self.db.execute(query, (token, user_id, device_info, ip_address, expires_at))
        return {
            "token": token,
            "user_id": user_id,
            "device_info": device_info,
            "ip_address": ip_address,
            "expires_at": expires_at,
            "is_active": 1
        }

    def get_session(self, token: str) -> Optional[Dict[str, Any]]:
        """Retrieves session record if active and not expired."""
        now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        query = """
            SELECT s.id, s.token, s.user_id, s.device_info, s.ip_address, s.created_at, s.expires_at, s.is_active,
                   u.username, u.full_name, u.role, u.is_active as user_active
            FROM customer_sessions s
            JOIN users u ON s.user_id = u.id
            WHERE s.token = ? AND s.is_active = 1 AND s.expires_at > ? AND u.is_active = 1;
        """
        row = self.db.fetchone(query, (token.strip(), now_str))
        if not row:
            return None
        return dict(row)

    def invalidate_session(self, token: str) -> bool:
        """Revokes a specific session token (single device logout)."""
        query = "UPDATE customer_sessions SET is_active = 0 WHERE token = ?;"
        count = self.db.execute(query, (token.strip(),))
        logger.info(f"Invalidated session token {token[:8]}...")
        return count > 0

    def invalidate_all_for_user(self, user_id: int) -> int:
        """Revokes all active sessions for a user across all devices."""
        query = "UPDATE customer_sessions SET is_active = 0 WHERE user_id = ? AND is_active = 1;"
        count = self.db.execute(query, (user_id,))
        logger.info(f"Invalidated {count} active session(s) for user ID {user_id}")
        return count

    def cleanup_expired(self) -> int:
        """Deactivates all past-due sessions."""
        now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        query = "UPDATE customer_sessions SET is_active = 0 WHERE expires_at <= ? AND is_active = 1;"
        return self.db.execute(query, (now_str,))
