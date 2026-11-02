"""Unit and integration tests for Customer Dining Portal and data isolation."""
import pytest
from decimal import Decimal
from repositories.user_repository import UserRepository
from repositories.order_repository import OrderRepository
from repositories.menu_repository import MenuRepository
from services.auth_service import AuthService
from services.order_service import OrderService


@pytest.fixture
def customer_env(clean_db_manager):
    db = clean_db_manager
    user_repo = UserRepository(db)
    auth_svc = AuthService(user_repo=user_repo)
    menu_repo = MenuRepository(db)
    order_repo = OrderRepository(db)
    order_svc = OrderService(order_repo=order_repo, menu_repo=menu_repo)

    dish = menu_repo.create("Virgin Mojito Test", "Beverages", Decimal("110.00"))

    return db, auth_svc, order_svc, dish


def test_customer_registration_and_authentication(customer_env):
    """Verifies that a customer can register an account and sign in with role CUSTOMER."""
    db, auth_svc, _, _ = customer_env

    # 1. Register new customer
    ok, msg, user = auth_svc.register_customer(
        username="guest_sarah",
        password="Password123!",
        full_name="Sarah Jenkins"
    )
    assert ok is True
    assert user is not None
    assert user.role == "CUSTOMER"
    assert user.username == "guest_sarah"
    assert user.full_name == "Sarah Jenkins"

    # 2. Duplicate registration rejection
    ok_dup, msg_dup, _ = auth_svc.register_customer(
        username="guest_sarah",
        password="DifferentPass123!",
        full_name="Sarah Dup"
    )
    assert ok_dup is False
    assert "already registered" in msg_dup.lower()

    # 3. Log out and log back in
    auth_svc.logout()
    assert auth_svc.is_authenticated() is False

    ok_login, msg_login, login_user = auth_svc.login("guest_sarah", "Password123!")
    assert ok_login is True
    assert login_user.role == "CUSTOMER"


def test_customer_order_data_isolation(customer_env):
    """Verifies that Customer A can only query their own orders and not Customer B's orders."""
    db, auth_svc, order_svc, dish = customer_env

    # Register two distinct customers
    _, _, cust_a = auth_svc.register_customer("customer_a", "Pass123!", "Alice Smith")
    _, _, cust_b = auth_svc.register_customer("customer_b", "Pass123!", "Bob Jones")

    # Alice places an order
    _, _, ord_a = order_svc.create_order(cust_a.id, "T1", "Alice Smith", [(dish.id, 1)])

    # Bob places an order
    _, _, ord_b = order_svc.create_order(cust_b.id, "T2", "Bob Jones", [(dish.id, 2)])

    # Query orders isolated by user_id = cust_a.id
    alice_orders = db.fetchall("SELECT id, order_number FROM orders WHERE user_id = ?;", (cust_a.id,))
    alice_order_ids = [r["id"] for r in alice_orders]

    assert ord_a.id in alice_order_ids
    assert ord_b.id not in alice_order_ids

    # Query orders isolated by user_id = cust_b.id
    bob_orders = db.fetchall("SELECT id, order_number FROM orders WHERE user_id = ?;", (cust_b.id,))
    bob_order_ids = [r["id"] for r in bob_orders]

    assert ord_b.id in bob_order_ids
    assert ord_a.id not in bob_order_ids
