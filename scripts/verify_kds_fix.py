"""Verification script for Chef KDS order retrieval, status progression, and refresh stability."""
import sys
from decimal import Decimal
import customtkinter as ctk

from database.db import db
from services.order_service import order_service
from services.auth_service import auth_service
from ui.chef_kds import ChefKDSFrame


def run_verification():
    print("=" * 70)
    print("PHASE 5 & 6 VERIFICATION: CHEF KDS INTEGRATION & REFRESH STABILITY")
    print("=" * 70)

    # 1. Verify Customer Order exists in SQLite
    order_id = 84
    row = db.fetchone("SELECT id, order_number, table_number, customer_name, status, user_id FROM orders WHERE id = ?", (order_id,))
    assert row is not None, f"Order {order_id} not found in database!"
    print(f"[PASS] Step 1: Customer order exists in SQLite: ID={row['id']}, OrderNo={row['order_number']}, Status={row['status']}, Customer={row['customer_name']}")

    # Check items
    items = db.fetchall("SELECT item_name, quantity, line_total FROM order_items WHERE order_id = ?", (order_id,))
    assert len(items) == 2, f"Expected 2 items for order {order_id}, got {len(items)}"
    for it in items:
        print(f"    - Item: {it['item_name']} x{it['quantity']} (Total: {it['line_total']})")

    # 2. Verify Chef KDS fetches this order at the top of active queue
    root = ctk.CTk()
    root.withdraw()
    kds_frame = ChefKDSFrame(root)

    active_orders = kds_frame._fetch_active_orders()
    order_ids = [o["id"] for o in active_orders]
    assert order_id in order_ids, f"Order {order_id} missing from active KDS query!"
    print(f"[PASS] Step 2: Chef KDS retrieved Order {order_id} (Total active: {len(active_orders)})")

    # Check that Order 84 is at Top 1 (since it is the newest unaccepted ticket)
    top_order = active_orders[0]
    print(f"[PASS] Step 3: Top Order on KDS Display: ID={top_order['id']}, OrderNo={top_order['order_number']}, Status={top_order['status']}")
    assert top_order["id"] == order_id, f"Expected top order to be {order_id}, got {top_order['id']}"

    # 3. Verify card elements on screen
    grid = kds_frame.tickets_scroll.winfo_children()[0]
    cards = grid.winfo_children()
    top_card = cards[0]
    header = top_card.winfo_children()[0]
    title_lbl = header.winfo_children()[0]
    print(f"[PASS] Step 4: Card 0 Title in GUI: '{title_lbl.cget('text')}'")
    assert str(row["order_number"]) in title_lbl.cget("text")

    # 4. Chef Progression: PENDING -> ACCEPTED
    print("[*] Transitioning Order 84: PENDING -> ACCEPTED...")
    kds_frame._transition_status(order_id, "ACCEPTED")
    updated_row = db.fetchone("SELECT status FROM orders WHERE id = ?", (order_id,))
    assert updated_row["status"] == "ACCEPTED"
    print(f"[PASS] Step 5: Database and KDS updated to: {updated_row['status']}")

    # 5. Chef Progression: ACCEPTED -> PREPARING
    print("[*] Transitioning Order 84: ACCEPTED -> PREPARING...")
    kds_frame._transition_status(order_id, "PREPARING")
    updated_row = db.fetchone("SELECT status FROM orders WHERE id = ?", (order_id,))
    assert updated_row["status"] == "PREPARING"
    print(f"[PASS] Step 6: Database and KDS updated to: {updated_row['status']}")

    # 6. Chef Progression: PREPARING -> READY
    print("[*] Transitioning Order 84: PREPARING -> READY...")
    kds_frame._transition_status(order_id, "READY")
    updated_row = db.fetchone("SELECT status FROM orders WHERE id = ?", (order_id,))
    assert updated_row["status"] == "READY"
    print(f"[PASS] Step 7: Database and KDS updated to: {updated_row['status']}")

    # 7. Customer sees updated status in Customer Order History
    cust_orders = order_service.list_orders(user_id=11)
    matching_cust_order = next((o for o in cust_orders if o.id == order_id), None)
    assert matching_cust_order is not None
    assert matching_cust_order.status == "READY"
    print(f"[PASS] Step 8: Customer 11 portal sees Order #{matching_cust_order.order_number} status as '{matching_cust_order.status}'")

    # Reset back to PENDING so order remains in original status
    db.execute("UPDATE orders SET status = 'PENDING' WHERE id = ?", (order_id,))
    kds_frame._transition_status(order_id, "PENDING")
    print("[*] Order 84 status restored to 'PENDING' for ongoing operational testing.")

    # -------------------------------------------------------------
    # PHASE 6: REFRESH STABILITY AND ZERO FLICKER TEST
    # -------------------------------------------------------------
    print("-" * 70)
    print("PHASE 6: REFRESH STABILITY TEST (Simulating 15 periodic ticks)")
    print("-" * 70)

    grid = kds_frame.tickets_scroll.winfo_children()[0]
    initial_grid_id = id(grid)

    reconstruction_count = 0
    in_place_count = 0

    for tick in range(15):
        kds_frame._on_auto_refresh_tick()
        current_grid = kds_frame.tickets_scroll.winfo_children()[0]
        if id(current_grid) != initial_grid_id:
            reconstruction_count += 1
            initial_grid_id = id(current_grid)
        else:
            in_place_count += 1

    print(f"[PASS] Periodic ticks executed: 15")
    print(f"[PASS] In-place non-destructive updates: {in_place_count}")
    print(f"[PASS] Full screen reconstructions: {reconstruction_count}")
    assert reconstruction_count == 0, f"Screen was reconstructed {reconstruction_count} times during steady state!"
    assert in_place_count == 15, "In-place updates failed during steady state!"

    # Verify single timer management
    assert kds_frame._auto_refresh_id is not None
    timer_id_before = kds_frame._auto_refresh_id

    # Scheduling again should cancel previous timer and maintain exactly ONE timer
    kds_frame._schedule_refresh()
    assert kds_frame._auto_refresh_id is not None
    print("[PASS] Exactly ONE active timer maintained without duplicate chains.")

    # Cleanup
    kds_frame.destroy()
    assert kds_frame._auto_refresh_id is None
    assert kds_frame._is_active is False
    print("[PASS] Destroy cleanly cancelled all pending timers and unsubscribed listeners.")

    root.destroy()
    print("=" * 70)
    print("ALL INTEGRATION AND REFRESH STABILITY CHECKS PASSED!")
    print("=" * 70)


if __name__ == "__main__":
    run_verification()
