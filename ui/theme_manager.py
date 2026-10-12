"""Theme manager for CustomTkinter appearance and dynamic palette switching."""
from typing import Callable, List, Optional
import customtkinter as ctk
from config.settings import THEME_PALETTES, DEFAULT_THEME
from repositories.settings_repository import SettingsRepository
from utils.logger import logger


class ThemeManager:
    """Manages active application theme, color palettes, and subscriber notifications."""

    def __init__(self, settings_repo: Optional[SettingsRepository] = None):
        self.settings_repo = settings_repo or SettingsRepository()
        self._current_theme: str = DEFAULT_THEME
        self._listeners: List[Callable[[str], None]] = []

    @property
    def current_theme(self) -> str:
        return self._current_theme

    def get_palette(self) -> dict:
        """Returns the color dictionary for the active theme."""
        return THEME_PALETTES.get(self._current_theme, THEME_PALETTES["dark"])

    def subscribe(self, listener: Callable[[str], None]) -> None:
        """Subscribes a callback that is invoked whenever the theme changes."""
        if listener not in self._listeners:
            self._listeners.append(listener)

    def unsubscribe(self, listener: Callable[[str], None]) -> None:
        """Removes a registered theme change listener."""
        if listener in self._listeners:
            self._listeners.remove(listener)

    def apply_theme(self, theme_name: str, user_id: Optional[int] = None) -> None:
        """Sets appearance mode, updates state, persists preference, and notifies listeners."""
        clean_theme = theme_name.lower().strip()
        if clean_theme not in ["dark", "light"]:
            clean_theme = "dark"

        self._current_theme = clean_theme
        try:
            ctk.set_appearance_mode(clean_theme)
        except Exception as e:
            logger.debug(f"GUI appearance mode set (headless or non-tk): {e}")

        if user_id:
            try:
                self.settings_repo.update_theme(user_id, clean_theme)
            except Exception as e:
                logger.error(f"Failed to persist theme to database: {e}")

        # Notify subscribers
        for listener in self._listeners:
            try:
                listener(self._current_theme)
            except Exception as e:
                logger.error(f"Error notifying theme listener: {e}")

    def toggle_theme(self, user_id: Optional[int] = None) -> str:
        """Toggles between Dark Mode and Light Mode."""
        new_theme = "light" if self._current_theme == "dark" else "dark"
        self.apply_theme(new_theme, user_id=user_id)
        logger.info(f"Theme toggled to '{new_theme}'.")
        return new_theme


# Global Theme Manager instance
theme_manager = ThemeManager()
