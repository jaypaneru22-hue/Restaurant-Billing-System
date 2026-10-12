"""Profile service for managing user details, passwords, and preferences (Q08-F5)."""
from typing import Optional, Tuple, Dict, Any
from decimal import Decimal
from repositories.user_repository import UserRepository
from repositories.settings_repository import SettingsRepository
from utils.security import verify_password, hash_password, validate_password_strength
from utils.validators import validate_tax_rate
from utils.logger import logger


class ProfileService:
    def __init__(
        self,
        user_repo: Optional[UserRepository] = None,
        settings_repo: Optional[SettingsRepository] = None
    ):
        self.user_repo = user_repo or UserRepository()
        self.settings_repo = settings_repo or SettingsRepository()

    def get_profile_data(self, user_id: int) -> Optional[Dict[str, Any]]:
        """Retrieves combined user account information and settings."""
        user = self.user_repo.get_by_id(user_id)
        if not user:
            return None
        settings = self.settings_repo.get_by_user_id(user_id)
        return {
            "id": user.id,
            "username": user.username,
            "full_name": user.full_name,
            "role": user.role,
            "created_at": user.created_at,
            "theme": settings.theme,
            "currency": settings.currency,
            "default_tax_rate": settings.default_tax_rate
        }

    def update_profile(self, user_id: int, full_name: str) -> Tuple[bool, str]:
        """Updates user's display name."""
        if not full_name or not full_name.strip():
            return False, "Full name cannot be empty."
        clean_name = full_name.strip()
        if len(clean_name) < 2 or len(clean_name) > 60:
            return False, "Full name must be between 2 and 60 characters."

        success = self.user_repo.update_profile(user_id, clean_name)
        if success:
            logger.info(f"Profile updated for user id={user_id}: full_name='{clean_name}'")
            return True, "Profile details updated successfully."
        return False, "Failed to update profile."

    def change_password(
        self,
        user_id: int,
        current_password: str,
        new_password: str,
        confirm_password: str
    ) -> Tuple[bool, str]:
        """Validates current credentials and updates password with a fresh PBKDF2 hash."""
        if not current_password or not current_password.strip():
            return False, "Current password is required."
        if not new_password or not new_password.strip():
            return False, "New password is required."
        if new_password != confirm_password:
            return False, "New password and confirmation password do not match."
        if current_password == new_password:
            return False, "New password cannot be identical to current password."

        valid_strength, strength_msg = validate_password_strength(new_password)
        if not valid_strength:
            return False, strength_msg

        user = self.user_repo.get_by_id(user_id)
        if not user:
            return False, "User not found."

        if not verify_password(current_password, user.password_hash):
            return False, "Current password is incorrect."

        new_hash = hash_password(new_password)
        success = self.user_repo.update_password(user_id, new_hash)
        if success:
            logger.info(f"Password changed successfully for user id={user_id}")
            return True, "Password changed successfully."
        return False, "Failed to update password."

    def update_preferences(self, user_id: int, theme: str, default_tax_rate_input: str | float | Decimal) -> Tuple[bool, str]:
        """Updates and persists theme and default tax preferences."""
        valid_tax, tax_msg, tax_rate = validate_tax_rate(default_tax_rate_input)
        if not valid_tax:
            return False, tax_msg

        clean_theme = theme.lower().strip()
        if clean_theme not in ["dark", "light"]:
            return False, "Invalid theme selection. Must be 'dark' or 'light'."

        success = self.settings_repo.update_settings(user_id, clean_theme, tax_rate)
        if success:
            logger.info(f"Preferences updated for user id={user_id}: theme='{clean_theme}', tax={tax_rate}%")
            return True, "Preferences updated successfully."
        return False, "Failed to update preferences."


# Global profile service instance
profile_service = ProfileService()
