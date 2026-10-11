"""Unit tests for MenuService CRUD, validations, and search."""
import pytest
from decimal import Decimal
from database.db import DatabaseManager
from database.migrations import initialize_database
from repositories.menu_repository import MenuRepository
from services.menu_service import MenuService


@pytest.fixture
def menu_fixture(tmp_path):
    db_file = tmp_path / "menu_test.db"
    db_manager = DatabaseManager(db_file)
    initialize_database(db_manager)
    repo = MenuRepository(db_manager)
    service = MenuService(repo)
    return service, repo


def test_add_menu_item_success(menu_fixture):
    service, _ = menu_fixture
    ok, msg, item = service.add_item("Tandoori Paneer Roll", "Starters", "190.00", True)
    assert ok is True
    assert item is not None
    assert item.name == "Tandoori Paneer Roll"
    assert item.price == Decimal("190.00")
    assert item.category == "Starters"
    assert item.is_available is True


def test_add_duplicate_menu_item_fails(menu_fixture):
    service, _ = menu_fixture
    service.add_item("Lemonade", "Beverages", "50.00")
    ok, msg, item = service.add_item("Lemonade", "Beverages", "60.00")
    assert ok is False
    assert "already exists" in msg
    assert item is None


def test_add_menu_item_invalid_price(menu_fixture):
    service, _ = menu_fixture
    ok, msg, item = service.add_item("Free Snack", "Starters", "0.00")
    assert ok is False
    assert "greater than zero" in msg
    assert item is None

    ok_neg, _, _ = service.add_item("Bad Price", "Starters", "-25.00")
    assert ok_neg is False


def test_update_menu_item(menu_fixture):
    service, _ = menu_fixture
    _, _, item = service.add_item("Veg Burger", "Starters", "120.00")
    ok, msg = service.update_item(item.id, "Deluxe Veg Burger", "Starters", "145.00", True)
    assert ok is True

    items = service.search_items("Deluxe Veg Burger")
    assert len(items) == 1
    assert items[0].price == Decimal("145.00")


def test_delete_menu_item(menu_fixture):
    service, _ = menu_fixture
    _, _, item = service.add_item("Seasonal Soup", "Starters", "110.00")
    ok, msg = service.delete_item(item.id)
    assert ok is True
    results = service.search_items("Seasonal Soup")
    assert len(results) == 0


def test_search_and_filter_menu_items(menu_fixture):
    service, _ = menu_fixture
    results = service.search_items("Chai", category="Beverages")
    assert len(results) >= 1
    assert "Chai" in results[0].name

    results_all = service.search_items("", category="Desserts")
    assert len(results_all) >= 1
    for r in results_all:
        assert r.category == "Desserts"
