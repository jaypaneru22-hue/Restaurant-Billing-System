"""Comprehensive concurrent multi-device testing for simultaneous customer access.

Executes all 15 scenarios mandated by RestoPro Multi-User Architecture:
1. Customer A registers and logs in (Mobile Safari).
2. Customer B registers and logs in (Mobile Chrome).
3. Customer C logs in from another device (Desktop Firefox).
4. Customer D logs in independently (iPad Tablet).
5. All four browse menu simultaneously in parallel threads.
6. All four add items to their own carts with verified isolation.
7. Simultaneous order placement without lock collisions or duplicate codes.
8. Unique Order IDs verification.
9. Correct customer ownership verification.
10. All orders reach Chef KDS active queue.
11. Waiter serving progression (READY -> PICKED_UP -> SERVED).
12. Cashier independent billing retrieval and settlement.
13. Strict security: customers cannot access each other's orders (403 Forbidden).
14. Session independence: logging out Customer A leaves B, C, D active.
15. Server restart and database persistence verification.
"""
import pytest
import json
import urllib.request
import urllib.error
import threading
from concurrent.futures import ThreadPoolExecutor
from decimal import Decimal

from database.db import DatabaseManager
from database.migrations import initialize_database
from repositories.order_repository import OrderRepository
from repositories.session_repository import SessionRepository
from repositories.cart_repository import CartRepository
from repositories.menu_repository import MenuRepository
from services.order_service import OrderService
from services.billing_service import BillingService
from services.menu_service import MenuService
from services.auth_service import AuthService
from services.session_service import SessionService
from services.cart_service import CartService
from api.rest_handler import RestAPIHandler
from api.http_server import ThreadedHTTPServer, RestoProHTTPRequestHandler


def _make_http_request(url, method="GET", data=None, token=None):
    """Helper to perform HTTP requests using standard library urllib."""
    headers = {
        "Content-Type": "application/json",
        "Accept": "application/json"
    }
    if token:
        headers["Authorization"] = f"Bearer {token}"

    req_data = json.dumps(data).encode("utf-8") if data is not None else None
    req = urllib.request.Request(url, data=req_data, headers=headers, method=method)

    try:
        with urllib.request.urlopen(req, timeout=10.0) as resp:
            status = resp.status
            body = json.loads(resp.read().decode("utf-8"))
            return status, body
    except urllib.error.HTTPError as e:
        status = e.code
        try:
            body = json.loads(e.read().decode("utf-8"))
        except Exception:
            body = {"error": str(e)}
        return status, body


@pytest.fixture(scope="module")
def multi_user_server(tmp_path_factory):
    """Spawns an isolated multi-threaded HTTP server backed by a temporary database."""
    temp_dir = tmp_path_factory.mktemp("multi_user_test")
    db_file = temp_dir / "concurrent_restaurant.db"
    db_mgr = DatabaseManager(db_file)
    initialize_database(db_mgr)

    # Wire services to isolated test DB
    session_repo = SessionRepository(db_mgr)
    session_svc = SessionService(session_repo=session_repo, user_repo=AuthService(user_repo=None).user_repo)
    session_svc.user_repo.db = db_mgr
    cart_repo = CartRepository(db_mgr)
    menu_repo = MenuRepository(db_mgr)
    cart_svc = CartService(cart_repo=cart_repo, menu_repo=menu_repo)
    order_repo = OrderRepository(db_mgr)
    order_svc = OrderService(order_repo=order_repo, menu_repo=menu_repo)
    billing_svc = BillingService(order_repo=order_repo)
    billing_svc.db = db_mgr
    billing_svc.billing_repo.db = db_mgr

    custom_handler = RestAPIHandler(
        auth_svc=AuthService(user_repo=session_svc.user_repo),
        session_svc=session_svc,
        menu_svc=MenuService(menu_repo=menu_repo),
        cart_svc=cart_svc,
        order_svc=order_svc,
        billing_svc=billing_svc
    )

    # Dynamic port binding
    class TestRequestHandler(RestoProHTTPRequestHandler):
        def _dispatch_api(self):
            content_length = int(self.headers.get("Content-Length", 0))
            body_bytes = self.rfile.read(content_length) if content_length > 0 else b""
            headers_dict = {k.lower(): v for k, v in self.headers.items()}

            status_code, response_headers, body = custom_handler.handle_request(
                method=self.command,
                path=self.path,
                headers=headers_dict,
                body_bytes=body_bytes,
                client_address=self.client_address
            )
            self.send_response(status_code)
            for h_name, h_val in response_headers.items():
                self.send_header(h_name, h_val)
            self.end_headers()
            if body:
                self.wfile.write(body)

    httpd = ThreadedHTTPServer(("127.0.0.1", 0), TestRequestHandler)
    assigned_port = httpd.server_address[1]
    server_url = f"http://127.0.0.1:{assigned_port}"

    server_thread = threading.Thread(target=httpd.serve_forever, daemon=True)
    server_thread.start()

    yield {
        "url": server_url,
        "db": db_mgr,
        "order_svc": order_svc,
        "billing_svc": billing_svc,
        "custom_handler": custom_handler,
        "httpd": httpd,
        "db_file": db_file
    }

    httpd.shutdown()


def test_e2e_simultaneous_multi_customer_workflow(multi_user_server):
    """Executes the full 15-step concurrency lifecycle across four independent customer devices."""
    base_url = multi_user_server["url"]
    order_svc = multi_user_server["order_svc"]
    billing_svc = multi_user_server["billing_svc"]

    # =========================================================================
    # STEPS 1 to 4: Independent Registrations & Logins (Customer A, B, C, D)
    # =========================================================================
    devices = [
        {"username": "cust_alice", "pass": "Alice@123", "name": "Alice M (iPhone)", "device": "iPhone 15 / Safari"},
        {"username": "cust_bob", "pass": "BobPass@123", "name": "Bob K (Android)", "device": "Pixel 8 / Chrome"},
        {"username": "cust_charlie", "pass": "Charlie@123", "name": "Charlie S (Laptop)", "device": "MacBook / Firefox"},
        {"username": "cust_diana", "pass": "Diana@123", "name": "Diana P (iPad)", "device": "iPad Pro / Safari"}
    ]

    tokens = {}
    users = {}

    for d in devices:
        status, body = _make_http_request(
            f"{base_url}/api/auth/register",
            method="POST",
            data={"username": d["username"], "password": d["pass"], "full_name": d["name"]}
        )
        assert status == 201, f"Failed registering {d['username']}: {body}"
        assert body["success"] is True
        assert "token" in body
        token = body["token"]
        tokens[d["username"]] = token
        users[d["username"]] = body["user"]

    # Verify all 4 tokens are mutually unique
    all_tokens = list(tokens.values())
    assert len(set(all_tokens)) == 4, "Tokens must be unique per customer device!"

    # Verify identity isolation on /api/auth/me
    for uname, tok in tokens.items():
        st, b = _make_http_request(f"{base_url}/api/auth/me", method="GET", token=tok)
        assert st == 200
        assert b["user"]["username"] == uname

    # =========================================================================
    # STEP 5: Simultaneous Menu Browsing
    # =========================================================================
    def browse_menu(tok):
        st, b = _make_http_request(f"{base_url}/api/menu", method="GET", token=tok)
        return st, len(b.get("items", []))

    with ThreadPoolExecutor(max_workers=4) as executor:
        futures = [executor.submit(browse_menu, tok) for tok in all_tokens]
        results = [f.result() for f in futures]

    for status_code, count in results:
        assert status_code == 200
        assert count >= 10, "Each customer must successfully retrieve the full menu catalog."

    # =========================================================================
    # STEP 6: Simultaneous Independent Cart Population
    # =========================================================================
    # Each customer adds a distinct dish to their cart:
    # Alice: Item 1 (qty 2)
    # Bob: Item 2 (qty 1)
    # Charlie: Item 3 (qty 3)
    # Diana: Item 4 (qty 1)
    dish_assignments = {
        "cust_alice": (1, 2),
        "cust_bob": (2, 1),
        "cust_charlie": (3, 3),
        "cust_diana": (4, 1)
    }

    def add_to_cart(uname):
        item_id, qty = dish_assignments[uname]
        tok = tokens[uname]
        st, b = _make_http_request(
            f"{base_url}/api/cart/add",
            method="POST",
            data={"menu_item_id": item_id, "quantity": qty},
            token=tok
        )
        return uname, st, b

    with ThreadPoolExecutor(max_workers=4) as executor:
        add_futures = [executor.submit(add_to_cart, u) for u in dish_assignments.keys()]
        add_results = [f.result() for f in add_futures]

    for uname, st, body in add_results:
        assert st == 200, f"Error adding to cart for {uname}: {body}"
        assert body["success"] is True

    # VERIFY CART ISOLATION: No customer sees another customer's items!
    for uname, tok in tokens.items():
        st, b = _make_http_request(f"{base_url}/api/cart", method="GET", token=tok)
        assert st == 200
        assigned_dish_id, assigned_qty = dish_assignments[uname]
        items = b["cart"]["items"]
        assert len(items) == 1, f"Expected 1 dish in {uname}'s cart, found {len(items)}"
        assert items[0]["menu_item_id"] == assigned_dish_id
        assert items[0]["quantity"] == assigned_qty

    # =========================================================================
    # STEPS 7 to 9: Simultaneous Order Checkout (At Least 2 Customers in Parallel)
    # =========================================================================
    table_assignments = {
        "cust_alice": ("Table 1", "Less oil please"),
        "cust_bob": ("Table 2", "Extra spicy"),
        "cust_charlie": ("Table 3", "Serve hot"),
        "cust_diana": ("Takeaway", "Pack separately")
    }

    def checkout_order(uname):
        tbl, note = table_assignments[uname]
        tok = tokens[uname]
        st, b = _make_http_request(
            f"{base_url}/api/orders/checkout",
            method="POST",
            data={"table_number": tbl, "special_instructions": note},
            token=tok
        )
        return uname, st, b

    # Execute all 4 checkouts in parallel
    with ThreadPoolExecutor(max_workers=4) as executor:
        order_futures = [executor.submit(checkout_order, u) for u in table_assignments.keys()]
        order_results = [f.result() for f in order_futures]

    order_ids = {}
    order_numbers = {}

    for uname, st, body in order_results:
        assert st == 201, f"Checkout failed for {uname}: {body}"
        assert body["success"] is True
        oid = body["order"]["id"]
        onum = body["order"]["order_number"]
        order_ids[uname] = oid
        order_numbers[uname] = onum

    # Step 8: Verify unique Order IDs and Order Numbers
    assert len(set(order_ids.values())) == 4, "All 4 orders must receive unique Order IDs!"
    assert len(set(order_numbers.values())) == 4, "All 4 orders must receive unique Order Numbers!"

    # Step 9: Verify correct customer ownership in the database
    for uname, oid in order_ids.items():
        expected_uid = users[uname]["id"]
        ord_obj = order_svc.get_order(oid)
        assert ord_obj is not None
        assert ord_obj.user_id == expected_uid, f"Order {oid} belongs to user {ord_obj.user_id}, expected {expected_uid}"
        assert ord_obj.customer_name == users[uname]["full_name"]

    # =========================================================================
    # STEP 10: Verify All Orders Reach Chef KDS
    # =========================================================================
    active_orders = order_svc.list_orders(status="PENDING")
    active_order_ids = {o.id for o in active_orders}
    for uname, oid in order_ids.items():
        assert oid in active_order_ids, f"Order {oid} from {uname} must appear in Chef KDS active queue."

    # =========================================================================
    # STEP 11: Waiter Progression (READY -> PICKED_UP -> SERVED)
    # =========================================================================
    # Chef marks Alice's order READY
    alice_oid = order_ids["cust_alice"]
    multi_user_server["db"].execute(
        "UPDATE orders SET status = 'READY', updated_at = CURRENT_TIMESTAMP WHERE id = ?;",
        (alice_oid,)
    )

    # Waiter picks it up
    multi_user_server["db"].execute(
        "UPDATE orders SET status = 'PICKED_UP', picked_up_at = CURRENT_TIMESTAMP, waiter_id = 1 WHERE id = ?;",
        (alice_oid,)
    )

    # Waiter marks SERVED
    multi_user_server["db"].execute(
        "UPDATE orders SET status = 'SERVED', served_at = CURRENT_TIMESTAMP WHERE id = ?;",
        (alice_oid,)
    )

    # Customer Alice checks her live tracking endpoint
    st_track, track_body = _make_http_request(
        f"{base_url}/api/orders/{alice_oid}/track",
        method="GET",
        token=tokens["cust_alice"]
    )
    assert st_track == 200
    assert track_body["lifecycle"]["kitchen_status"] == "READY"
    assert track_body["lifecycle"]["serving_status"] == "SERVED"
    assert track_body["overall_step"] >= 4

    # =========================================================================
    # STEP 12: Cashier Retrieves and Settles Order
    # =========================================================================
    unbilled_queue = order_svc.get_pending_billing_orders(filter_status="ALL_UNBILLED")
    unbilled_ids = [o["id"] for o in unbilled_queue]
    assert alice_oid in unbilled_ids, "SERVED order must appear in Cashier Pending Billing queue!"

    # Cashier generates and settles bill for Alice's order
    ok_bill, msg_bill, bill = billing_svc.finalize_bill(
        order_id=alice_oid,
        payment_method="UPI"
    )
    assert ok_bill is True
    assert bill is not None
    assert bill.order_id == alice_oid

    # Verify tracking updates for Alice to SETTLED / Step 5
    st_track2, track_body2 = _make_http_request(
        f"{base_url}/api/orders/{alice_oid}/track",
        method="GET",
        token=tokens["cust_alice"]
    )
    assert st_track2 == 200
    assert track_body2["lifecycle"]["billing_status"] == "SETTLED"
    assert track_body2["lifecycle"]["payment_status"] == "PAID"
    assert track_body2["overall_step"] == 5

    # =========================================================================
    # STEP 13: Strict Customer Data Isolation (403 Forbidden on Other Orders)
    # =========================================================================
    # Alice attempts to access Bob's order:
    bob_oid = order_ids["cust_bob"]
    st_illegal1, _ = _make_http_request(
        f"{base_url}/api/orders/{bob_oid}",
        method="GET",
        token=tokens["cust_alice"]
    )
    assert st_illegal1 == 403, "Customer A must NOT be permitted to view Customer B's order."

    # Diana attempts to track Charlie's order:
    charlie_oid = order_ids["cust_charlie"]
    st_illegal2, _ = _make_http_request(
        f"{base_url}/api/orders/{charlie_oid}/track",
        method="GET",
        token=tokens["cust_diana"]
    )
    assert st_illegal2 == 403, "Customer D must NOT be permitted to track Customer C's order."

    # =========================================================================
    # STEP 14: Logging Out One Customer Leaves Other Sessions Completely Active
    # =========================================================================
    # Alice logs out
    st_logout, _ = _make_http_request(
        f"{base_url}/api/auth/logout",
        method="POST",
        token=tokens["cust_alice"]
    )
    assert st_logout == 200

    # Alice's token is now revoked
    st_alice_check, _ = _make_http_request(
        f"{base_url}/api/auth/me",
        method="GET",
        token=tokens["cust_alice"]
    )
    assert st_alice_check == 401, "Revoked token must return 401."

    # Bob, Charlie, and Diana remain completely authenticated and active!
    for active_u in ("cust_bob", "cust_charlie", "cust_diana"):
        st_active, b_active = _make_http_request(
            f"{base_url}/api/auth/me",
            method="GET",
            token=tokens[active_u]
        )
        assert st_active == 200, f"{active_u}'s session was improperly terminated when Alice logged out!"
        assert b_active["user"]["username"] == active_u

    # =========================================================================
    # STEP 15: Database Persistence After Server Restart
    # =========================================================================
    # Shut down current server
    multi_user_server["httpd"].shutdown()

    # Create new server instance pointing to the exact same database file
    db_file = multi_user_server["db_file"]
    new_db_mgr = DatabaseManager(db_file)
    new_session_repo = SessionRepository(new_db_mgr)
    new_session_svc = SessionService(session_repo=new_session_repo)
    new_session_svc.user_repo.db = new_db_mgr
    new_order_repo = OrderRepository(new_db_mgr)
    new_order_svc = OrderService(order_repo=new_order_repo)

    new_handler = RestAPIHandler(
        auth_svc=AuthService(user_repo=new_session_svc.user_repo),
        session_svc=new_session_svc,
        order_svc=new_order_svc
    )

    class RestartHandler(RestoProHTTPRequestHandler):
        def _dispatch_api(self):
            content_length = int(self.headers.get("Content-Length", 0))
            body_bytes = self.rfile.read(content_length) if content_length > 0 else b""
            headers_dict = {k.lower(): v for k, v in self.headers.items()}
            status_code, response_headers, body = new_handler.handle_request(
                method=self.command,
                path=self.path,
                headers=headers_dict,
                body_bytes=body_bytes,
                client_address=self.client_address
            )
            self.send_response(status_code)
            for h_name, h_val in response_headers.items():
                self.send_header(h_name, h_val)
            self.end_headers()
            if body:
                self.wfile.write(body)

    new_httpd = ThreadedHTTPServer(("127.0.0.1", 0), RestartHandler)
    new_port = new_httpd.server_address[1]
    new_url = f"http://127.0.0.1:{new_port}"

    new_thread = threading.Thread(target=new_httpd.serve_forever, daemon=True)
    new_thread.start()

    try:
        # Verify Bob's persistent session token survives server restart
        st_restart, b_restart = _make_http_request(
            f"{new_url}/api/auth/me",
            method="GET",
            token=tokens["cust_bob"]
        )
        assert st_restart == 200
        assert b_restart["user"]["username"] == "cust_bob"

        # Verify Bob's order history survived server restart
        st_orders, b_orders = _make_http_request(
            f"{new_url}/api/orders",
            method="GET",
            token=tokens["cust_bob"]
        )
        assert st_orders == 200
        assert len(b_orders["orders"]) >= 1
        assert b_orders["orders"][0]["id"] == order_ids["cust_bob"]
    finally:
        new_httpd.shutdown()
