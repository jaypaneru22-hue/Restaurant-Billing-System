"""Unit tests for SettingsRepository and ThemeManager (Feature 3: Theme Toggle)."""
import pytest
from database.db import DatabaseManager
from database.migrations import initialize_database
from repositories.settings_repository import SettingsRepository
from ui.theme_manager import ThemeManager


@pytest.fixture
def theme_fixture(tmp_path):
    db_file = tmp_path / "theme_test.db"
    db_manager = DatabaseManager(db_file)
    initialize_database(db_manager)
    repo = SettingsRepository(db_manager)
    manager = ThemeManager(repo)
    return manager, repo


def test_theme_manager_default_and_palette(theme_fixture):
    manager, _ = theme_fixture
    assert manager.current_theme in ["dark", "light"]
    palette = manager.get_palette()
    assert "bg_primary" in palette
    assert "text_primary" in palette
    assert "accent" in palette


def test_theme_manager_toggle(theme_fixture):
    manager, _ = theme_fixture
    manager.apply_theme("dark")
    assert manager.current_theme == "dark"

    new_t = manager.toggle_theme()
    assert new_t == "light"
    assert manager.current_theme == "light"

    new_t2 = manager.toggle_theme()
    assert new_t2 == "dark"
    assert manager.current_theme == "dark"


def test_theme_manager_subscriber_notification(theme_fixture):
    manager, _ = theme_fixture
    events = []

    def on_change(theme_name):
        events.append(theme_name)

    manager.subscribe(on_change)
    manager.apply_theme("light")
    manager.apply_theme("dark")

    assert events == ["light", "dark"]


def test_settings_repository_persistence(theme_fixture):
    manager, repo = theme_fixture
    user_id = 1  # admin user seeded

    # Update theme via manager
    manager.apply_theme("light", user_id=user_id)

    # Fetch from repository directly
    settings = repo.get_by_user_id(user_id)
    assert settings.theme == "light"

    # Toggle back to dark
    manager.apply_theme("dark", user_id=user_id)
    settings_reloaded = repo.get_by_user_id(user_id)
    assert settings_reloaded.theme == "dark"
