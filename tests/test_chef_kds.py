"""Unit and integration tests for Chef Kitchen Display System (KDS) and status pipeline."""
import pytest
from decimal import Decimal
from repositories.order_repository import OrderRepository
from repositories.menu_repository import MenuRepository
from services.order_service import OrderService


@pytest.fixture
def setup_kds_env(clean_db_manager):
    db = clean_db_manager
    order_repo = OrderRepository(db)
    menu_repo = MenuRepository(db)
    order_svc = OrderService(order_repo=order_repo, menu_repo=menu_repo)

    dish1 = menu_repo.create("Paneer Butter Masala Special", "Main Course", Decimal("280.00"))
    dish2 = menu_repo.create("Butter Naan Special", "Breads & Rice", Decimal("45.00"))

    return db, order_svc, dish1, dish2


def test_kds_status_pipeline_transitions(setup_kds_env):
    """Verifies that an order progresses through PENDING -> ACCEPTED -> PREPARING -> READY -> COMPLETED."""
    db, order_svc, dish1, dish2 = setup_kds_env

    # 1. Create order (Starts in PENDING)
    ok, msg, order = order_svc.create_order(
        user_id=1,
        table_number="T1",
        customer_name="Chef Test Guest",
        item_entries=[(dish1.id, 2), (dish2.id, 4)]
    )
    assert ok is True
    assert order is not None
    assert order.status == "PENDING"

    # 2. Transition: PENDING -> ACCEPTED
    ok, msg = order_svc.update_order_status(order.id, "ACCEPTED")
    assert ok is True
    updated = order_svc.get_order(order.id)
    assert updated.status == "ACCEPTED"

    # 3. Transition: ACCEPTED -> PREPARING
    ok, msg = order_svc.update_order_status(order.id, "PREPARING")
    assert ok is True
    updated = order_svc.get_order(order.id)
    assert updated.status == "PREPARING"

    # 4. Transition: PREPARING -> READY
    ok, msg = order_svc.update_order_status(order.id, "READY")
    assert ok is True
    updated = order_svc.get_order(order.id)
    assert updated.status == "READY"

    # 5. Transition: READY -> COMPLETED
    ok, msg = order_svc.update_order_status(order.id, "COMPLETED")
    assert ok is True
    updated = order_svc.get_order(order.id)
    assert updated.status == "COMPLETED"


def test_kds_order_filtering(setup_kds_env):
    """Verifies that the kitchen display filters orders by active statuses."""
    db, order_svc, dish1, _ = setup_kds_env

    # Create 3 orders with different statuses
    _, _, ord1 = order_svc.create_order(1, "T1", "Guest A", [(dish1.id, 1)])
    _, _, ord2 = order_svc.create_order(1, "T2", "Guest B", [(dish1.id, 1)])
    _, _, ord3 = order_svc.create_order(1, "T3", "Guest C", [(dish1.id, 1)])

    order_svc.update_order_status(ord2.id, "PREPARING")
    order_svc.update_order_status(ord3.id, "COMPLETED")

    active_orders = db.fetchall(
        "SELECT id, order_number, status FROM orders WHERE status != 'COMPLETED' ORDER BY created_at DESC;"
    )
    active_ids = [r["id"] for r in active_orders]

    assert ord1.id in active_ids
    assert ord2.id in active_ids
    assert ord3.id not in active_ids
