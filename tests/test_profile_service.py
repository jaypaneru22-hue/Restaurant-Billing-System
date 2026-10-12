"""Unit tests for ProfileService (Feature 5: User Profile Settings)."""
import pytest
from decimal import Decimal
from database.db import DatabaseManager
from database.migrations import initialize_database
from repositories.user_repository import UserRepository
from repositories.settings_repository import SettingsRepository
from services.profile_service import ProfileService
from utils.security import verify_password


@pytest.fixture
def profile_fixture(tmp_path):
    db_file = tmp_path / "profile_test.db"
    db_manager = DatabaseManager(db_file)
    initialize_database(db_manager)
    u_repo = UserRepository(db_manager)
    s_repo = SettingsRepository(db_manager)
    service = ProfileService(u_repo, s_repo)
    return service, u_repo, s_repo


def test_get_profile_data(profile_fixture):
    service, _, _ = profile_fixture
    data = service.get_profile_data(1)
    assert data is not None
    assert data["username"] == "admin"
    assert data["role"] == "ADMIN"
    assert "theme" in data
    assert "currency" in data


def test_update_profile_name(profile_fixture):
    service, u_repo, _ = profile_fixture
    ok, msg = service.update_profile(1, "Jay Paneru (Lead Admin)")
    assert ok is True
    user = u_repo.get_by_id(1)
    assert user.full_name == "Jay Paneru (Lead Admin)"

    ok_empty, _ = service.update_profile(1, "")
    assert ok_empty is False


def test_change_password_success(profile_fixture):
    service, u_repo, _ = profile_fixture
    ok, msg = service.change_password(
        user_id=1,
        current_password="Admin@123",
        new_password="NewSecurePass456",
        confirm_password="NewSecurePass456"
    )
    assert ok is True
    user = u_repo.get_by_id(1)
    assert verify_password("NewSecurePass456", user.password_hash) is True


def test_change_password_wrong_current(profile_fixture):
    service, _, _ = profile_fixture
    ok, msg = service.change_password(1, "IncorrectCurrent", "NewPass123", "NewPass123")
    assert ok is False
    assert "Current password is incorrect" in msg


def test_change_password_mismatch(profile_fixture):
    service, _, _ = profile_fixture
    ok, msg = service.change_password(1, "Admin@123", "NewPass123", "DifferentPass123")
    assert ok is False
    assert "do not match" in msg


def test_update_preferences(profile_fixture):
    service, _, s_repo = profile_fixture
    ok, msg = service.update_preferences(1, "light", "6.5")
    assert ok is True

    settings = s_repo.get_by_user_id(1)
    assert settings.theme == "light"
    assert settings.default_tax_rate == Decimal("6.50")
