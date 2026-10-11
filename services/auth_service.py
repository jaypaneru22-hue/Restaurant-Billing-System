"""Authentication and session management service."""
from typing import Optional, Tuple
from models.user import User
from repositories.user_repository import UserRepository
from utils.security import verify_password
from utils.validators import validate_username
from utils.logger import logger


class AuthService:
    def __init__(self, user_repo: Optional[UserRepository] = None):
        self.user_repo = user_repo or UserRepository()
        self._current_user: Optional[User] = None

    @property
    def current_user(self) -> Optional[User]:
        return self._current_user

    def is_authenticated(self) -> bool:
        return self._current_user is not None

    def is_admin(self) -> bool:
        return self._current_user is not None and self._current_user.is_admin()

    def login(self, username: str, password: str) -> Tuple[bool, str, Optional[User]]:
        """Authenticates user against stored PBKDF2 hash and establishes active session."""
        valid_user, err_msg = validate_username(username)
        if not valid_user:
            return False, err_msg, None

        if not password or not password.strip():
            return False, "Password cannot be empty.", None

        user = self.user_repo.get_by_username(username.strip())
        if not user:
            logger.warning(f"Failed login attempt: non-existent username '{username}'")
            return False, "Invalid username or password.", None

        if not verify_password(password, user.password_hash):
            logger.warning(f"Failed login attempt: incorrect password for username '{username}'")
            return False, "Invalid username or password.", None

        self._current_user = user
        logger.info(f"Successful login for user '{username}' (role: {user.role})")
        return True, "Login successful.", user

    def logout(self) -> None:
        """Clears active user session."""
        if self._current_user:
            logger.info(f"User '{self._current_user.username}' logged out.")
        self._current_user = None


# Global auth service instance
auth_service = AuthService()
