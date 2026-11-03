"""Authentication and session management service."""
from typing import Optional, Tuple
from datetime import datetime
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

    def is_manager(self) -> bool:
        return self._current_user is not None and self._current_user.is_manager()

    def is_cashier(self) -> bool:
        return self._current_user is not None and self._current_user.is_cashier()

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

        if not user.is_active:
            logger.warning(f"Login rejected: account '{username}' is deactivated.")
            return False, "Account deactivated. Contact system administrator.", None

        # Record latest successful login timestamp in the database
        now_ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self.user_repo.update_last_login(user.id, now_ts)
        user.last_login = now_ts

        self._current_user = user
        logger.info(f"Successful login for user '{username}' (role: {user.role}, last_login: {now_ts})")
        return True, "Login successful.", user

    def register_customer(self, username: str, password: str, full_name: str) -> Tuple[bool, str, Optional[User]]:
        """Registers a new dining customer and establishes active session."""
        valid_user, err_msg = validate_username(username)
        if not valid_user:
            return False, err_msg, None

        if not password or len(password.strip()) < 6:
            return False, "Password must be at least 6 characters.", None

        if not full_name or not full_name.strip():
            return False, "Full name cannot be empty.", None

        existing = self.user_repo.get_by_username(username.strip())
        if existing:
            return False, "Username is already registered. Please choose another or sign in.", None

        from utils.security import hash_password
        pwd_hash = hash_password(password.strip())
        user = self.user_repo.create(
            username=username.strip(),
            password_hash=pwd_hash,
            full_name=full_name.strip(),
            role="CUSTOMER"
        )
        # Record initial login session for newly registered customer
        now_ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self.user_repo.update_last_login(user.id, now_ts)
        user.last_login = now_ts

        self._current_user = user
        logger.info(f"New customer registered & session started: '{username}' (id={user.id}, last_login: {now_ts})")
        return True, "Customer registration successful.", user

    def logout(self) -> None:
        """Clears active user session."""
        if self._current_user:
            logger.info(f"User '{self._current_user.username}' logged out.")
        self._current_user = None


# Global auth service instance
auth_service = AuthService()
