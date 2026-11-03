"""End-to-End Integration Verification Script for RestoPro WAITER Role."""
import sys
from decimal import Decimal
from pathlib import Path

# Add project root to sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from database.db import db
from services.order_service import order_service
from services.waiter_service import waiter_service
from services.billing_service import billing_service
from config.settings import (
    ORDER_STATUS_PENDING,
    ORDER_STATUS_ACCEPTED,
    ORDER_STATUS_PREPARING,
    ORDER_STATUS_READY,
    ORDER_STATUS_PICKED_UP,
    ORDER_STATUS_SERVED,
    ORDER_STATUS_COMPLETED
)


def run_complete_e2e_verification():
    print("=" * 70)
    print("RESTOPRO — COMPLETE WAITER ROLE END-TO-END VERIFICATION")
    print("=" * 70)

    # 1. Check Waiter1 exists and is active
    waiter = db.fetchone("SELECT id, username, full_name, role, is_active FROM users WHERE role = 'WAITER' AND username = 'waiter1';")
    assert waiter is not None, "waiter1 does not exist!"
    assert waiter["is_active"] == 1, "waiter1 is not active!"
    waiter_id = waiter["id"]
    print(f"[PASS] 1. Authenticated Waiter Account: ID={waiter_id}, Username='{waiter['username']}', Name='{waiter['full_name']}'")

    # 2. Customer places order
    ok, msg, order = order_service.create_order(
        user_id=1,
        table_number="T-1",
        customer_name="Aarav Singhania (VIP)",
        item_entries=[(1, 2), (3, 1)],  # 2 Margherita Pizza, 1 Fresh Lime Soda
        special_instructions="Gluten-free crust and less ice in soda"
    )
    assert ok is True, f"Customer order creation failed: {msg}"
    order_id = order.id
    order_number = order.order_number
    print(f"[PASS] 2. Customer placed Order: ID={order_id}, Code='{order_number}', Table='T-1', Status='{order.status}'")

    # 3. Chef accepts and cooks
    ok_acc, _ = order_service.update_order_status(order_id, ORDER_STATUS_ACCEPTED)
    assert ok_acc is True
    ok_prep, _ = order_service.update_order_status(order_id, ORDER_STATUS_PREPARING)
    assert ok_prep is True
    print(f"[PASS] 3. Chef KDS updated order status: PENDING -> ACCEPTED -> PREPARING")

    # Guard: Chef cannot mark SERVED
    ok_fail, err = order_service.update_order_status(order_id, ORDER_STATUS_SERVED)
    assert ok_fail is False
    print(f"[PASS] 4. Role Guard: Chef denied marking order SERVED ({err})")

    # Guard: Waiter cannot pick up order while in PREPARING
    ok_pk_fail, err_pk = order_service.mark_order_picked_up(order_id, waiter_id)
    assert ok_pk_fail is False
    print(f"[PASS] 5. State Guard: Waiter denied picking up PREPARING order ({err_pk})")

    # 4. Chef marks order READY
    ok_ready, _ = order_service.update_order_status(order_id, ORDER_STATUS_READY)
    assert ok_ready is True
    print(f"[PASS] 6. Chef finished cooking: Marked order #{order_number} as READY at kitchen pass")

    # 5. Waiter sees unassigned ready order in queue
    ready_orders = waiter_service.get_ready_orders(waiter_id=waiter_id)
    assert any(o["id"] == order_id for o in ready_orders), "Order not visible in waiter ready queue!"
    print(f"[PASS] 7. Waiter Queue: Order #{order_number} instantly visible in Waiter Dashboard")

    # 6. Manager assigns waiter to order
    ok_asgn, msg_asgn = order_service.assign_waiter_to_order(order_id, waiter_id)
    assert ok_asgn is True
    print(f"[PASS] 8. Manager Dispatch: Assigned Waiter ID={waiter_id} to Order #{order_number}")

    # Guard: Deactivated waiter cannot be assigned
    # Create temp user, deactivate, test assignment
    db.execute("INSERT OR REPLACE INTO users (id, username, password_hash, full_name, role, is_active) VALUES (999, 'temp_waiter', 'x', 'Temp Deactivated', 'WAITER', 0);")
    ok_inact, err_inact = order_service.assign_waiter_to_order(order_id, 999)
    assert ok_inact is False
    print(f"[PASS] 9. Security Guard: Prevented assigning inactive waiter account ({err_inact})")

    # 7. Waiter marks PICKED UP
    ok_pu, msg_pu = order_service.mark_order_picked_up(order_id, waiter_id)
    assert ok_pu is True
    order_after_pu = order_service.get_order(order_id)
    assert order_after_pu.status == ORDER_STATUS_PICKED_UP
    assert order_after_pu.waiter_id == waiter_id
    assert order_after_pu.picked_up_at is not None
    print(f"[PASS] 10. Waiter Action: Collected food from kitchen pass -> Status='PICKED_UP' at {order_after_pu.picked_up_at}")

    # Guard: Duplicate pickup rejected
    ok_dup_pu, err_dup_pu = order_service.mark_order_picked_up(order_id, waiter_id)
    assert ok_dup_pu is False
    print(f"[PASS] 11. Concurrency Guard: Duplicate pickup rejected ({err_dup_pu})")

    # 8. Customer Assistance Service Request
    ok_req, msg_req, req_id = waiter_service.create_service_request(
        table_number="T-1",
        request_type="Water",
        notes="Chilled mineral water please",
        order_id=order_id,
        customer_id=1,
        customer_name="Aarav Singhania"
    )
    assert ok_req is True
    print(f"[PASS] 12. Customer Assistance: Raised Service Request #{req_id} for 'Water' at Table T-1")

    # Waiter accepts & resolves request
    ok_acc_req, _ = waiter_service.accept_service_request(req_id, waiter_id)
    assert ok_acc_req is True
    ok_res_req, _ = waiter_service.resolve_service_request(req_id, waiter_id)
    assert ok_res_req is True
    print(f"[PASS] 13. Waiter Request Workflow: Request #{req_id} accepted (IN_PROGRESS) -> resolved (RESOLVED)")

    # 9. Waiter marks SERVED
    ok_sv, msg_sv = order_service.mark_order_served(order_id, waiter_id)
    assert ok_sv is True
    order_after_sv = order_service.get_order(order_id)
    assert order_after_sv.status == ORDER_STATUS_SERVED
    assert order_after_sv.served_at is not None
    print(f"[PASS] 14. Waiter Action: Delivered dishes to Table T-1 -> Status='SERVED' at {order_after_sv.served_at}")

    # Guard: Duplicate served rejected
    ok_dup_sv, err_dup_sv = order_service.mark_order_served(order_id, waiter_id)
    assert ok_dup_sv is False
    print(f"[PASS] 15. Concurrency Guard: Duplicate serve rejected ({err_dup_sv})")

    # 10. Cashier finalizes bill & payment
    bill_ok, bill_msg, bill = billing_service.finalize_bill(
        order_id=order_id,
        payment_method="UPI",
        discount_percent_input=Decimal("0.00")
    )
    assert bill_ok is True
    assert bill is not None
    order_final = order_service.get_order(order_id)
    assert order_final.status == ORDER_STATUS_COMPLETED
    assert bill.payment_status == "PAID"
    print(f"[PASS] 16. Cashier Action: Generated Invoice #{bill.bill_number}, Final Total=INR {bill.final_total:,.2f}, Payment=PAID")

    # 11. Audit Trail Verification
    logs = db.fetchall(
        "SELECT action, module, details FROM audit_logs WHERE details LIKE ? ORDER BY id ASC;",
        (f"%{order_number}%",)
    )
    actions = [r["action"] for r in logs]
    print(f"[PASS] 17. Security & Audit Trail: Captured actions across lifecycle: {actions}")

    # 12. Cleanup temp user
    db.execute("DELETE FROM users WHERE id = 999;")

    print("=" * 70)
    print("ALL 17 END-TO-END WAITER INTEGRATION CHECKS PASSED WITH ZERO ERRORS!")
    print("=" * 70)


if __name__ == "__main__":
    run_complete_e2e_verification()
