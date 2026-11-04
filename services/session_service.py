"""Session service managing independent, cryptographically secure multi-user session tokens."""
import secrets
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from models.user import User
from repositories.session_repository import SessionRepository
from repositories.user_repository import UserRepository
from utils.logger import logger


class SessionService:
    """Manages independent customer and staff sessions with no shared global state."""

    def __init__(
        self,
        session_repo: Optional[SessionRepository] = None,
        user_repo: Optional[UserRepository] = None,
        default_expiry_hours: int = 24
    ):
        self.session_repo = session_repo or SessionRepository()
        self.user_repo = user_repo or UserRepository()
        self.default_expiry_hours = default_expiry_hours

    def create_session(
        self,
        user_id: int,
        device_info: str = "",
        ip_address: str = "",
        expiry_hours: Optional[int] = None
    ) -> str:
        """Issues a new independent session token for a customer device."""
        token = secrets.token_urlsafe(32)
        hours = expiry_hours or self.default_expiry_hours
        expires_at = (datetime.now() + timedelta(hours=hours)).strftime("%Y-%m-%d %H:%M:%S")

        self.session_repo.create_session(
            token=token,
            user_id=user_id,
            expires_at=expires_at,
            device_info=device_info,
            ip_address=ip_address
        )
        logger.info(f"Created session token {token[:8]}... for user {user_id} on '{device_info or 'device'}' (expires {expires_at})")
        return token

    def authenticate_token(self, token: Optional[str]) -> Optional[User]:
        """Validates session token and returns the authenticated User instance.

        Guarantees strict isolation: returns a fresh User context per token,
        never relying on or modifying any global current_user variable.
        """
        if not token or not token.strip():
            return None

        clean_token = token.strip()
        if clean_token.startswith("Bearer "):
            clean_token = clean_token[7:].strip()

        session = self.session_repo.get_session(clean_token)
        if not session:
            return None

        # Return authenticated User representation
        return User(
            id=session["user_id"],
            username=session["username"],
            password_hash="",  # Redacted
            full_name=session["full_name"],
            role=session["role"],
            is_active=bool(session["user_active"])
        )

    def logout_token(self, token: Optional[str]) -> bool:
        """Revokes the specific device session token without affecting any other sessions."""
        if not token or not token.strip():
            return False

        clean_token = token.strip()
        if clean_token.startswith("Bearer "):
            clean_token = clean_token[7:].strip()

        return self.session_repo.invalidate_session(clean_token)

    def logout_all_devices(self, user_id: int) -> int:
        """Revokes all active sessions for this user across every device."""
        return self.session_repo.invalidate_all_for_user(user_id)


# Global default instance
session_service = SessionService()
