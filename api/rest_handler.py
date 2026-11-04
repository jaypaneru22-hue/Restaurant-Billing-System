"""REST API Request Dispatcher and Endpoints for Multi-Device Customer Access."""
import json
import urllib.parse
from decimal import Decimal
from typing import Dict, Any, Tuple, Optional, List

from services.auth_service import AuthService, auth_service
from services.session_service import SessionService, session_service
from services.menu_service import MenuService, menu_service
from services.cart_service import CartService, cart_service
from services.order_service import OrderService, order_service
from services.billing_service import BillingService, billing_service
from models.user import User
from database.db import db
from utils.logger import logger


class DecimalJSONEncoder(json.JSONEncoder):
    """Encodes Decimal instances cleanly for JSON responses."""
    def default(self, obj):
        if isinstance(obj, Decimal):
            return str(obj)
        return super().default(obj)


class RestAPIHandler:
    """Dispatches REST API calls with strict customer session authentication and data isolation."""

    def __init__(
        self,
        auth_svc: AuthService = auth_service,
        session_svc: SessionService = session_service,
        menu_svc: MenuService = menu_service,
        cart_svc: CartService = cart_service,
        order_svc: OrderService = order_service,
        billing_svc: BillingService = billing_service,
        db_mgr: Optional[Any] = None
    ):
        self.auth_svc = auth_svc
        self.session_svc = session_svc
        self.menu_svc = menu_svc
        self.cart_svc = cart_svc
        self.order_svc = order_svc
        self.billing_svc = billing_svc
        self.db = db_mgr or self.order_svc.order_repo.db

    def handle_request(
        self,
        method: str,
        path: str,
        headers: Dict[str, str],
        body_bytes: bytes,
        client_address: Tuple[str, int]
    ) -> Tuple[int, Dict[str, str], bytes]:
        """Routes HTTP request to corresponding controller and returns (status_code, headers, body)."""
        method = method.upper()
        parsed_url = urllib.parse.urlparse(path)
        route_path = parsed_url.path.rstrip("/")
        query_params = urllib.parse.parse_qs(parsed_url.query)

        # Base CORS headers for all responses
        res_headers = {
            "Content-Type": "application/json; charset=utf-8",
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Methods": "GET, POST, PUT, DELETE, OPTIONS",
            "Access-Control-Allow-Headers": "Authorization, Content-Type, Accept, X-Requested-With",
            "Access-Control-Max-Age": "86400"
        }

        # Handle CORS preflight
        if method == "OPTIONS":
            return 204, res_headers, b""

        # Parse JSON body if present
        body_json = {}
        if body_bytes:
            try:
                body_json = json.loads(body_bytes.decode("utf-8"))
            except Exception as e:
                return self._json_response(400, {"success": False, "error": f"Malformed JSON request body: {e}"}, res_headers)

        # Extract session token
        auth_header = headers.get("authorization", "") or headers.get("Authorization", "")
        # Also check cookie if header not provided
        if not auth_header and "cookie" in headers:
            cookies = headers["cookie"].split(";")
            for c in cookies:
                parts = c.strip().split("=", 1)
                if len(parts) == 2 and parts[0] == "session_token":
                    auth_header = parts[1]
                    break

        user = self.session_svc.authenticate_token(auth_header)
        client_ip = client_address[0] if client_address else ""
        user_agent = headers.get("user-agent", "") or headers.get("User-Agent", "Mobile/Browser")

        try:
            # 1. System Health
            if route_path in ("/api/health", "/api"):
                return self._json_response(200, {
                    "status": "healthy",
                    "system": "RestoPro Restaurant Management Platform",
                    "version": "2.0-MultiUser",
                    "active_sessions_supported": True
                }, res_headers)

            # 2. Authentication Routes
            if route_path == "/api/auth/register" and method == "POST":
                return self._handle_register(body_json, user_agent, client_ip, res_headers)

            if route_path == "/api/auth/login" and method == "POST":
                return self._handle_login(body_json, user_agent, client_ip, res_headers)

            if route_path == "/api/auth/logout" and method == "POST":
                if auth_header:
                    self.session_svc.logout_token(auth_header)
                return self._json_response(200, {"success": True, "message": "Logged out successfully."}, res_headers)

            if route_path == "/api/auth/me" and method == "GET":
                if not user:
                    return self._json_response(401, {"success": False, "error": "Authentication required."}, res_headers)
                return self._json_response(200, {
                    "success": True,
                    "user": {
                        "id": user.id,
                        "username": user.username,
                        "full_name": user.full_name,
                        "role": user.role
                    }
                }, res_headers)

            # 3. Menu Catalog (Publicly browseable)
            if route_path == "/api/menu" and method == "GET":
                category = query_params.get("category", [None])[0]
                available_only = query_params.get("available_only", ["true"])[0].lower() == "true"
                if category and category != "All":
                    items = self.menu_svc.get_items_by_category(category)
                    if available_only:
                        items = [it for it in items if it.is_available]
                else:
                    items = self.menu_svc.get_all_items(available_only=available_only)
                categories = self.menu_svc.get_categories()
                items_data = [
                    {
                        "id": it.id,
                        "name": it.name,
                        "category": it.category,
                        "price": it.price,
                        "is_available": it.is_available
                    }
                    for it in items
                ]
                return self._json_response(200, {
                    "success": True,
                    "categories": categories,
                    "items": items_data,
                    "count": len(items_data)
                }, res_headers)

            # 4. Tables List
            if route_path == "/api/tables" and method == "GET":
                tables_rows = self.db.fetchall("SELECT table_number, zone, capacity, status FROM restaurant_tables ORDER BY zone, table_number;")
                tables = [{"table_number": r["table_number"], "zone": r["zone"], "capacity": r["capacity"], "status": r["status"]} for r in tables_rows]
                return self._json_response(200, {"success": True, "tables": tables}, res_headers)

            # -------------------------------------------------------------
            # CUSTOMER-AUTHENTICATED ROUTES
            # -------------------------------------------------------------
            if not user:
                return self._json_response(401, {
                    "success": False,
                    "error": "Authentication required. Please sign in or register to access this endpoint."
                }, res_headers)

            # 5. Customer Cart Endpoints (Strictly isolated by user.id)
            if route_path == "/api/cart" and method == "GET":
                cart = self.cart_svc.get_cart_summary(user.id)
                return self._json_response(200, {"success": True, "cart": cart}, res_headers)

            if route_path == "/api/cart/add" and method == "POST":
                item_id = int(body_json.get("menu_item_id", 0))
                qty = int(body_json.get("quantity", 1))
                instr = str(body_json.get("special_instructions", ""))
                ok, msg = self.cart_svc.add_to_cart(user.id, item_id, qty, instr)
                cart = self.cart_svc.get_cart_summary(user.id)
                return self._json_response(200 if ok else 400, {"success": ok, "message": msg, "cart": cart}, res_headers)

            if route_path == "/api/cart/update" and method == "POST":
                item_id = int(body_json.get("menu_item_id", 0))
                qty = int(body_json.get("quantity", 0))
                ok, msg = self.cart_svc.update_cart_item(user.id, item_id, qty)
                cart = self.cart_svc.get_cart_summary(user.id)
                return self._json_response(200 if ok else 400, {"success": ok, "message": msg, "cart": cart}, res_headers)

            if route_path == "/api/cart/remove" and method == "POST":
                item_id = int(body_json.get("menu_item_id", 0))
                ok, msg = self.cart_svc.remove_from_cart(user.id, item_id)
                cart = self.cart_svc.get_cart_summary(user.id)
                return self._json_response(200 if ok else 400, {"success": ok, "message": msg, "cart": cart}, res_headers)

            if route_path == "/api/cart/clear" and method in ("POST", "DELETE"):
                ok, msg = self.cart_svc.clear_cart(user.id)
                cart = self.cart_svc.get_cart_summary(user.id)
                return self._json_response(200, {"success": ok, "message": msg, "cart": cart}, res_headers)

            # 6. Orders Endpoints
            if route_path == "/api/orders/checkout" and method == "POST":
                return self._handle_checkout(user, body_json, res_headers)

            if route_path == "/api/orders" and method == "GET":
                # Returns strictly authenticated customer's own orders
                limit = int(query_params.get("limit", [50])[0])
                orders = self.order_svc.get_customer_orders(user_id=user.id, limit=limit)
                orders_data = [self._format_order_summary(o) for o in orders]
                return self._json_response(200, {"success": True, "orders": orders_data, "count": len(orders_data)}, res_headers)

            # Dynamic order route: /api/orders/{id} and /api/orders/{id}/track
            if route_path.startswith("/api/orders/"):
                sub_parts = route_path[len("/api/orders/"):].split("/")
                order_id_str = sub_parts[0]
                if order_id_str.isdigit():
                    order_id = int(order_id_str)
                    if len(sub_parts) == 1 and method == "GET":
                        return self._handle_get_order(user, order_id, res_headers)
                    if len(sub_parts) == 2 and sub_parts[1] == "track" and method == "GET":
                        return self._handle_track_order(user, order_id, res_headers)

            # 7. Customer Service Requests (Call waiter)
            if route_path == "/api/service-requests" and method == "POST":
                table = str(body_json.get("table_number", "Table 1")).strip()
                req_type = str(body_json.get("request_type", "ASSISTANCE")).upper()
                notes = str(body_json.get("notes", "")).strip()
                order_id = body_json.get("order_id")
                req_id = self.db.execute(
                    """INSERT INTO service_requests (table_number, order_id, customer_id, customer_name, request_type, notes, status)
                       VALUES (?, ?, ?, ?, ?, ?, 'PENDING');""",
                    (table, order_id, user.id, user.full_name, req_type, notes)
                )
                return self._json_response(201, {
                    "success": True,
                    "request_id": req_id,
                    "message": f"Waiter summoned for {req_type.lower()} at {table}."
                }, res_headers)

            if route_path == "/api/service-requests" and method == "GET":
                rows = self.db.fetchall(
                    """SELECT id, table_number, request_type, notes, status, created_at, resolved_at
                       FROM service_requests WHERE customer_id = ? ORDER BY id DESC LIMIT 20;""",
                    (user.id,)
                )
                reqs = [dict(r) for r in rows]
                return self._json_response(200, {"success": True, "requests": reqs}, res_headers)

            # 8. Feedback & NPS
            if route_path == "/api/feedback" and method == "POST":
                order_id = body_json.get("order_id")
                rating = int(body_json.get("rating", 5))
                food_quality = int(body_json.get("food_quality", rating))
                service_speed = int(body_json.get("service_speed", rating))
                ambience = int(body_json.get("ambience", rating))
                comments = str(body_json.get("comments", "")).strip()
                nps = int(body_json.get("nps_score", 10))

                fb_id = self.db.execute(
                    """INSERT INTO customer_feedback (order_id, customer_name, rating, food_quality, service_speed, ambience, comments, nps_score)
                       VALUES (?, ?, ?, ?, ?, ?, ?, ?);""",
                    (order_id, user.full_name, rating, food_quality, service_speed, ambience, comments, nps)
                )
                return self._json_response(201, {"success": True, "feedback_id": fb_id, "message": "Thank you for your feedback!"}, res_headers)

            # Route not matched
            return self._json_response(404, {"success": False, "error": f"Endpoint not found: {method} {route_path}"}, res_headers)

        except Exception as e:
            logger.error(f"Unhandled error handling API request {method} {route_path}: {e}", exc_info=True)
            return self._json_response(500, {"success": False, "error": f"Internal server error: {e}"}, res_headers)

    # -------------------------------------------------------------
    # Helper Controllers
    # -------------------------------------------------------------
    def _handle_register(self, data: dict, user_agent: str, client_ip: str, headers: dict) -> Tuple[int, dict, bytes]:
        username = str(data.get("username", "")).strip()
        password = str(data.get("password", "")).strip()
        full_name = str(data.get("full_name", "")).strip() or username

        ok, msg, new_user = self.auth_svc.register_customer(username, password, full_name)
        if not ok or not new_user:
            return self._json_response(400, {"success": False, "error": msg}, headers)

        token = self.session_svc.create_session(new_user.id, device_info=user_agent, ip_address=client_ip)
        return self._json_response(201, {
            "success": True,
            "message": "Customer registered successfully.",
            "token": token,
            "user": {
                "id": new_user.id,
                "username": new_user.username,
                "full_name": new_user.full_name,
                "role": new_user.role
            }
        }, headers)

    def _handle_login(self, data: dict, user_agent: str, client_ip: str, headers: dict) -> Tuple[int, dict, bytes]:
        username = str(data.get("username", "")).strip()
        password = str(data.get("password", "")).strip()

        ok, msg, authenticated_user = self.auth_svc.login(username, password)
        if not ok or not authenticated_user:
            return self._json_response(401, {"success": False, "error": msg}, headers)

        token = self.session_svc.create_session(authenticated_user.id, device_info=user_agent, ip_address=client_ip)
        return self._json_response(200, {
            "success": True,
            "message": "Login successful.",
            "token": token,
            "user": {
                "id": authenticated_user.id,
                "username": authenticated_user.username,
                "full_name": authenticated_user.full_name,
                "role": authenticated_user.role
            }
        }, headers)

    def _handle_checkout(self, user: User, data: dict, headers: dict) -> Tuple[int, dict, bytes]:
        table_number = str(data.get("table_number", "Takeaway")).strip()
        special_instructions = str(data.get("special_instructions", "")).strip()

        # Item entries: if provided directly in payload, use them; otherwise, pull from server cart!
        direct_items = data.get("items")
        if direct_items and isinstance(direct_items, list):
            item_entries = [(int(it["menu_item_id"]), int(it["quantity"])) for it in direct_items]
        else:
            cart_items = self.cart_svc.cart_repo.get_cart_items(user.id)
            if not cart_items:
                return self._json_response(400, {"success": False, "error": "Your cart is empty. Please add items before placing order."}, headers)
            item_entries = [(it["menu_item_id"], it["quantity"]) for it in cart_items]

        ok, msg, order = self.order_svc.create_order(
            user_id=user.id,
            table_number=table_number,
            customer_name=user.full_name,
            item_entries=item_entries,
            special_instructions=special_instructions
        )

        if not ok or not order:
            return self._json_response(400, {"success": False, "error": msg}, headers)

        # Successfully placed: empty customer's cart
        self.cart_svc.clear_cart(user.id)

        # Mark table as OCCUPIED if dine-in table matches
        if table_number and table_number.lower() != "takeaway":
            try:
                self.db.execute(
                    "UPDATE restaurant_tables SET status = 'OCCUPIED', active_order_id = ? WHERE table_number = ?;",
                    (order.id, table_number)
                )
            except Exception:
                pass

        subtotal = sum((it.line_total for it in order.items), Decimal("0.00"))
        return self._json_response(201, {
            "success": True,
            "message": f"Order #{order.order_number} placed successfully and dispatched to kitchen!",
            "order": {
                "id": order.id,
                "order_number": order.order_number,
                "customer_name": order.customer_name,
                "table_number": order.table_number,
                "status": order.status,
                "created_at": order.created_at,
                "subtotal": subtotal,
                "items_count": len(order.items),
                "tracking_url": f"/api/orders/{order.id}/track"
            }
        }, headers)

    def _handle_get_order(self, user: User, order_id: int, headers: dict) -> Tuple[int, dict, bytes]:
        order = self.order_svc.get_order(order_id)
        if not order:
            return self._json_response(404, {"success": False, "error": "Order not found."}, headers)

        # Security check: Customer can ONLY view their own orders! Staff roles can view all.
        if user.role == "CUSTOMER" and order.user_id != user.id:
            return self._json_response(403, {"success": False, "error": "Access denied: you cannot view orders belonging to another customer."}, headers)

        return self._json_response(200, {"success": True, "order": self._format_order_detail(order)}, headers)

    def _handle_track_order(self, user: User, order_id: int, headers: dict) -> Tuple[int, dict, bytes]:
        # Query order with independent status resolution
        query = """
            SELECT o.id, o.order_number, o.user_id, o.table_number, o.customer_name,
                   o.status, o.created_at, o.updated_at, o.picked_up_at, o.served_at, o.special_instructions,
                   w.full_name as waiter_name,
                   b.id as bill_id, b.bill_number, b.final_total, b.payment_status, b.payment_method, b.billed_at,
                   (SELECT COUNT(*) FROM order_items WHERE order_id = o.id) as item_count,
                   (SELECT SUM(line_total) FROM order_items WHERE order_id = o.id) as subtotal
            FROM orders o
            LEFT JOIN users w ON o.waiter_id = w.id
            LEFT JOIN bills b ON o.id = b.order_id
            WHERE o.id = ?;
        """
        row = self.db.fetchone(query, (order_id,))
        if not row:
            return self._json_response(404, {"success": False, "error": "Order not found."}, headers)

        # Security isolation check:
        if user.role == "CUSTOMER" and row["user_id"] != user.id:
            return self._json_response(403, {"success": False, "error": "Access denied: cannot track order belonging to another customer."}, headers)

        raw_st = row["status"]

        # 1. Kitchen Status
        if raw_st in ("PENDING", "NEW"):
            kitchen_status = "RECEIVED"
            k_step = 1
        elif raw_st == "ACCEPTED":
            kitchen_status = "CONFIRMED"
            k_step = 2
        elif raw_st == "PREPARING":
            kitchen_status = "COOKING"
            k_step = 3
        elif raw_st in ("READY", "PICKED_UP", "SERVED", "COMPLETED"):
            kitchen_status = "READY"
            k_step = 4
        else:
            kitchen_status = raw_st
            k_step = 1

        # 2. Serving Status
        if row["served_at"] is not None or raw_st == "SERVED":
            serving_status = "SERVED"
            s_step = 3
        elif row["picked_up_at"] is not None or raw_st == "PICKED_UP":
            serving_status = "PICKED_UP"
            s_step = 2
        elif raw_st == "READY":
            serving_status = "READY_FOR_PICKUP"
            s_step = 1
        else:
            serving_status = "IN_KITCHEN"
            s_step = 0

        # 3. Billing & Payment Status
        has_bill = row["bill_id"] is not None
        bill_status = "SETTLED" if (has_bill and row["payment_status"] == "PAID") or raw_st == "COMPLETED" else ("GENERATED" if has_bill else "NOT_GENERATED")
        payment_status = "PAID" if (has_bill and row["payment_status"] == "PAID") else "PENDING"

        # Overall progress step (0 to 5)
        # 1: Placed, 2: Preparing, 3: Kitchen Ready, 4: Served, 5: Bill Settled
        if bill_status == "SETTLED":
            overall_step = 5
            headline = "Bill Settled • Thank you for dining with us!"
        elif serving_status == "SERVED":
            overall_step = 4
            headline = "Food Served • Enjoy your meal! (Proceed to cashier for bill settlement)"
        elif serving_status == "PICKED_UP":
            overall_step = 3.5
            headline = f"Order on the way! Floor server {row['waiter_name'] or 'staff'} is delivering to {row['table_number']}."
        elif kitchen_status == "READY":
            overall_step = 3
            headline = "Food Ready • Plated at the kitchen pass awaiting server pickup."
        elif kitchen_status == "COOKING":
            overall_step = 2
            headline = "Cooking in Kitchen • Chef is actively preparing your dishes."
        elif kitchen_status == "CONFIRMED":
            overall_step = 1.5
            headline = "Order Acknowledged • Queued for kitchen preparation."
        else:
            overall_step = 1
            headline = "Order Placed • Sent to kitchen queue."

        items = self.order_svc.order_repo.get_order_items(order_id)
        items_data = [{"name": it.item_name, "quantity": it.quantity, "line_total": it.line_total} for it in items]

        subtotal_dec = Decimal(str(row["subtotal"] or "0.00")).quantize(Decimal("0.01"))
        final_total_dec = Decimal(str(row["final_total"])).quantize(Decimal("0.01")) if row["final_total"] else subtotal_dec

        return self._json_response(200, {
            "success": True,
            "order_id": order_id,
            "order_number": row["order_number"],
            "table_number": row["table_number"],
            "customer_name": row["customer_name"],
            "created_at": row["created_at"],
            "headline": headline,
            "overall_step": overall_step,
            "lifecycle": {
                "kitchen_status": kitchen_status,
                "serving_status": serving_status,
                "billing_status": bill_status,
                "payment_status": payment_status
            },
            "timestamps": {
                "ordered_at": row["created_at"],
                "picked_up_at": row["picked_up_at"],
                "served_at": row["served_at"],
                "billed_at": row["billed_at"]
            },
            "bill": {
                "bill_number": row["bill_number"],
                "subtotal": subtotal_dec,
                "final_total": final_total_dec,
                "payment_method": row["payment_method"]
            } if has_bill else None,
            "waiter": row["waiter_name"] or "Floor Staff",
            "items": items_data,
            "subtotal": subtotal_dec
        }, headers)

    def _format_order_summary(self, o) -> dict:
        subtotal = sum((it.line_total for it in o.items), Decimal("0.00"))
        items_summary = ", ".join([f"{it.item_name} ×{it.quantity}" for it in o.items[:3]])
        if len(o.items) > 3:
            items_summary += f", +{len(o.items)-3} more"
        return {
            "id": o.id,
            "order_number": o.order_number,
            "table_number": o.table_number,
            "customer_name": o.customer_name,
            "status": o.status,
            "created_at": o.created_at,
            "items_count": len(o.items),
            "items_summary": items_summary,
            "subtotal": subtotal
        }

    def _format_order_detail(self, o) -> dict:
        subtotal = sum((it.line_total for it in o.items), Decimal("0.00"))
        return {
            "id": o.id,
            "order_number": o.order_number,
            "table_number": o.table_number,
            "customer_name": o.customer_name,
            "status": o.status,
            "special_instructions": o.special_instructions,
            "created_at": o.created_at,
            "updated_at": o.updated_at,
            "picked_up_at": o.picked_up_at,
            "served_at": o.served_at,
            "waiter_name": o.waiter_name,
            "subtotal": subtotal,
            "items": [
                {
                    "item_name": it.item_name,
                    "unit_price": it.unit_price,
                    "quantity": it.quantity,
                    "line_total": it.line_total
                }
                for it in o.items
            ]
        }

    def _json_response(self, status: int, payload: dict, base_headers: dict) -> Tuple[int, dict, bytes]:
        headers = dict(base_headers)
        body = json.dumps(payload, cls=DecimalJSONEncoder).encode("utf-8")
        headers["Content-Length"] = str(len(body))
        return status, headers, body


rest_api_handler = RestAPIHandler()
