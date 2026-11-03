"""Manager Active Orders Live Floor & Kitchen Monitor."""
from typing import Callable, Optional, List, Dict
from datetime import datetime
import customtkinter as ctk

from ui.theme_manager import theme_manager
from database.db import db
from repositories.order_repository import OrderRepository
from repositories.billing_repository import BillingRepository
from services.order_service import order_service
from services.waiter_service import WaiterService, waiter_service
from utils.window_utils import center_dialog
from utils.logger import logger


class AssignWaiterDialog(ctk.CTkToplevel):
    """Modal dialog allowing Manager to assign or reassign a waiter to an active order."""

    def __init__(self, master, order_id: int, order_number: str, current_waiter_id: Optional[int], on_assigned: Callable, **kwargs):
        super().__init__(master, **kwargs)
        self.order_id = order_id
        self.order_number = order_number
        self.on_assigned = on_assigned

        self.title(f"Assign Waiter — {order_number}")
        self.resizable(False, False)
        center_dialog(self, master, target_width=380, target_height=280)
        self.grab_set()

        self._build_ui(current_waiter_id)

    def _build_ui(self, current_waiter_id: Optional[int]):
        palette = theme_manager.get_palette()
        self.configure(fg_color=palette["bg_primary"])

        ctk.CTkLabel(
            self,
            text=f"👤 Assign Waiter to Order #{self.order_number}",
            font=ctk.CTkFont(size=14, weight="bold"),
            text_color=palette.get("heading", palette["text_primary"])
        ).pack(anchor="w", padx=20, pady=(18, 4))

        ctk.CTkLabel(
            self,
            text="Select an active floor server responsible for delivering this order:",
            font=ctk.CTkFont(size=11),
            text_color=palette["text_secondary"]
        ).pack(anchor="w", padx=20, pady=(0, 14))

        waiters = waiter_service.get_all_waiters(active_only=True)
        self.waiter_map = {f"{w.full_name} (@{w.username})": w.id for w in waiters}
        options = ["None (Unassigned)"] + list(self.waiter_map.keys())

        initial_val = "None (Unassigned)"
        if current_waiter_id:
            m = next((w for w in waiters if w.id == current_waiter_id), None)
            if m:
                initial_val = f"{m.full_name} (@{m.username})"

        self.opt_var = ctk.StringVar(value=initial_val)
        self.menu = ctk.CTkOptionMenu(
            self,
            variable=self.opt_var,
            values=options,
            height=34,
            fg_color=palette["bg_secondary"],
            text_color=palette["text_primary"],
            button_color=palette["accent"]
        )
        self.menu.pack(fill="x", padx=20, pady=(0, 10))

        self.lbl_error = ctk.CTkLabel(self, text="", font=ctk.CTkFont(size=10, weight="bold"), text_color="#EF4444")
        self.lbl_error.pack(padx=20, pady=(0, 8))

        btn_row = ctk.CTkFrame(self, fg_color="transparent")
        btn_row.pack(fill="x", padx=20, pady=(0, 15))

        ctk.CTkButton(
            btn_row,
            text="Cancel",
            width=90,
            height=32,
            fg_color=palette["bg_secondary"],
            text_color=palette["text_primary"],
            command=self.destroy
        ).pack(side="right", padx=(8, 0))

        ctk.CTkButton(
            btn_row,
            text="💾 Save Assignment",
            width=130,
            height=32,
            font=ctk.CTkFont(size=11, weight="bold"),
            fg_color=palette["accent"],
            hover_color=palette["accent_hover"],
            command=self._handle_save
        ).pack(side="right")

    def _handle_save(self):
        sel_text = self.opt_var.get()
        selected_id = self.waiter_map.get(sel_text, None)
        ok, msg = order_service.assign_waiter_to_order(self.order_id, selected_id)
        if ok:
            try:
                db.execute(
                    "INSERT INTO audit_logs (username, action, module, details) VALUES ('manager', 'WAITER_ASSIGNED', 'OPERATIONS', ?);",
                    (f"Order #{self.order_number} assigned to server ID {selected_id}",)
                )
            except Exception:
                pass
            self.on_assigned()
            self.destroy()
        else:
            self.lbl_error.configure(text=msg)


class WaiterWorkloadDialog(ctk.CTkToplevel):
    """Modal displaying real-time floor staff allocation, assigned tables, and active delivery load."""

    def __init__(self, master, waiter_svc: WaiterService = waiter_service, **kwargs):
        super().__init__(master, **kwargs)
        self.waiter_svc = waiter_svc
        self.title("RestoPro — Floor Staff Workload Monitor")
        self.resizable(False, False)
        center_dialog(self, master, target_width=640, target_height=480, min_width=600, min_height=420)
        self.grab_set()
        self._build_ui()

    def _build_ui(self):
        palette = theme_manager.get_palette()
        self.configure(fg_color=palette["bg_primary"])

        card = ctk.CTkFrame(self, fg_color=palette["bg_card"], corner_radius=10, border_width=1, border_color=palette["border"])
        card.pack(fill="both", expand=True, padx=16, pady=16)

        head = ctk.CTkFrame(card, fg_color="transparent")
        head.pack(fill="x", padx=16, pady=(16, 10))

        ctk.CTkLabel(
            head,
            text="👥 Waiter Floor Allocation & Workload Monitor",
            font=ctk.CTkFont(size=16, weight="bold"),
            text_color=palette.get("heading", palette["text_primary"])
        ).pack(side="left")

        # Scrollable list
        scroll = ctk.CTkScrollableFrame(card, fg_color=palette["bg_secondary"], corner_radius=8, height=300)
        scroll.pack(fill="both", expand=True, padx=16, pady=(0, 14))

        summary = self.waiter_svc.get_waiter_workload_summary()
        if not summary:
            ctk.CTkLabel(
                scroll,
                text="ℹ️ No floor servers currently registered in the database.",
                font=ctk.CTkFont(size=12),
                text_color=palette["text_secondary"]
            ).pack(pady=40)
        else:
            for w in summary:
                row = ctk.CTkFrame(scroll, fg_color=palette["bg_card"], corner_radius=8, border_width=1, border_color=palette["border"])
                row.pack(fill="x", padx=8, pady=4)

                r_inner = ctk.CTkFrame(row, fg_color="transparent")
                r_inner.pack(fill="x", padx=12, pady=10)

                left = ctk.CTkFrame(r_inner, fg_color="transparent")
                left.pack(side="left")

                status_dot = "🟢" if w["is_active"] else "🔴"
                ctk.CTkLabel(
                    left,
                    text=f"{status_dot} {w['full_name']} (@{w['username']})",
                    font=ctk.CTkFont(size=13, weight="bold"),
                    text_color=palette["text_primary"]
                ).pack(anchor="w")

                status_text = "Active Account" if w["is_active"] else "Inactive / Deactivated"
                ctk.CTkLabel(
                    left,
                    text=f"Role: WAITER  |  Status: {status_text}",
                    font=ctk.CTkFont(size=10),
                    text_color=palette["text_secondary"]
                ).pack(anchor="w", pady=(1, 0))

                right = ctk.CTkFrame(r_inner, fg_color="transparent")
                right.pack(side="right")

                stats = [
                    (f"🪑 Tables: {w['assigned_tables']}", palette["accent"]),
                    (f"🚶 In Service: {w['in_transit']}", "#F59E0B"),
                    (f"✅ Served: {w['served_today']}", "#10B981"),
                    (f"🛎️ Requests: {w['open_requests']}", "#EC4899")
                ]
                for s_text, col in stats:
                    pill = ctk.CTkFrame(right, fg_color=palette["bg_secondary"], corner_radius=6)
                    pill.pack(side="left", padx=3)
                    ctk.CTkLabel(pill, text=s_text, font=ctk.CTkFont(size=10, weight="bold"), text_color=col).pack(padx=6, pady=2)

        ctk.CTkButton(
            card,
            text="Close (Esc)",
            font=ctk.CTkFont(size=11, weight="bold"),
            fg_color=palette["accent"],
            hover_color=palette["accent_hover"],
            height=32,
            command=self.destroy
        ).pack(side="bottom", fill="x", padx=16, pady=(0, 16))

        self.bind("<Escape>", lambda e: self.destroy())



class ManagerActiveOrdersFrame(ctk.CTkFrame):
    """Real-time active order monitor displaying live kitchen orders, table statuses, and quick workflow controls."""

    def __init__(self, master, on_settle_order: Optional[Callable[[int], None]] = None, **kwargs):
        super().__init__(master, **kwargs)
        self.on_settle_order = on_settle_order
        self.order_repo = OrderRepository(db)
        self.billing_repo = BillingRepository(db)
        self.current_filter = "ALL"

        theme_manager.subscribe(self.on_theme_changed)
        self._build_ui()
        self._load_active_orders()

    def destroy(self):
        theme_manager.unsubscribe(self.on_theme_changed)
        super().destroy()

    def on_theme_changed(self, theme_name: str):
        if self.winfo_exists():
            palette = theme_manager.get_palette()
            self.configure(fg_color=palette["bg_primary"])
            self._load_active_orders()

    def _build_ui(self):
        palette = theme_manager.get_palette()
        self.configure(fg_color=palette["bg_primary"])

        # Top Header Bar
        header = ctk.CTkFrame(self, fg_color="transparent")
        header.pack(fill="x", padx=20, pady=(15, 8))

        title_box = ctk.CTkFrame(header, fg_color="transparent")
        title_box.pack(side="left")

        ctk.CTkLabel(
            title_box,
            text="⚡ Live Active Orders & Floor Monitor",
            font=ctk.CTkFont(size=20, weight="bold"),
            text_color=palette.get("heading", palette["text_primary"])
        ).pack(anchor="w")

        ctk.CTkLabel(
            title_box,
            text="Real-time monitor of active table orders, kitchen ticket progression, and floor waiter assignments.",
            font=ctk.CTkFont(size=11),
            text_color=palette["text_secondary"]
        ).pack(anchor="w", pady=(2, 0))

        # Controls Right
        ctrl_box = ctk.CTkFrame(header, fg_color="transparent")
        ctrl_box.pack(side="right")

        ctk.CTkButton(
            ctrl_box,
            text="👥 Waiter Workload",
            font=ctk.CTkFont(size=11, weight="bold"),
            fg_color=palette["bg_card"],
            text_color=palette["text_primary"],
            hover_color=palette["border"],
            height=32,
            command=lambda: WaiterWorkloadDialog(self)
        ).pack(side="left", padx=(0, 8))

        ctk.CTkButton(
            ctrl_box,
            text="🔄 Refresh",
            font=ctk.CTkFont(size=11, weight="bold"),
            fg_color=palette["accent"],
            hover_color=palette["accent_hover"],
            height=32,
            width=100,
            command=self._load_active_orders
        ).pack(side="right")

        # KPI Metrics Summary Bar
        self.kpi_container = ctk.CTkFrame(self, fg_color="transparent")
        self.kpi_container.pack(fill="x", padx=20, pady=(0, 10))

        # Filter Segmented Tabs Bar
        filter_bar = ctk.CTkFrame(self, fg_color="transparent")
        filter_bar.pack(fill="x", padx=20, pady=(0, 10))

        self.filter_buttons = {}
        for key, label in [
            ("ALL", "📋 All Active"),
            ("PENDING", "🟡 In Kitchen"),
            ("PREPARING", "👨‍🍳 Cooking"),
            ("READY", "🔔 Ready to Serve"),
            ("DELAYED", "⚠️ Delayed Ready (>5m)"),
            ("PICKED_UP", "🚶 In Transit"),
            ("SERVED", "✅ Served"),
            ("COMPLETED", "💳 Settle Pending")
        ]:
            btn = ctk.CTkButton(
                filter_bar,
                text=label,
                font=ctk.CTkFont(size=11, weight="bold"),
                height=30,
                fg_color=palette["accent"] if key == self.current_filter else palette["bg_card"],
                text_color="#FFFFFF" if key == self.current_filter else palette["text_secondary"],
                border_width=1,
                border_color=palette["border"],
                hover_color=palette["accent_hover"],
                command=lambda k=key: self._set_filter(k)
            )
            btn.pack(side="left", padx=3)
            self.filter_buttons[key] = btn

        # Orders Scrollable Grid
        self.scroll_container = ctk.CTkScrollableFrame(
            self,
            fg_color="transparent",
            scrollbar_button_color=palette.get("sidebar_hover", "#245A9B")
        )
        self.scroll_container.pack(fill="both", expand=True, padx=20, pady=(0, 15))

    def _set_filter(self, filter_key: str):
        self.current_filter = filter_key
        palette = theme_manager.get_palette()
        for k, btn in self.filter_buttons.items():
            if k == filter_key:
                btn.configure(fg_color=palette["accent"], text_color="#FFFFFF")
            else:
                btn.configure(fg_color=palette["bg_card"], text_color=palette["text_secondary"])
        self._render_order_cards()

    def _load_active_orders(self):
        palette = theme_manager.get_palette()

        try:
            rows = db.fetchall("""
                SELECT o.id, o.order_number, o.table_number, o.customer_name, o.status, o.created_at, o.updated_at,
                       o.waiter_id, o.picked_up_at, o.served_at, o.special_instructions,
                       u.full_name as server_name,
                       w.full_name as waiter_name,
                       (SELECT COUNT(*) FROM order_items WHERE order_id = o.id) as item_count,
                       (SELECT SUM(line_total) FROM order_items WHERE order_id = o.id) as total_val,
                       (SELECT id FROM bills WHERE order_id = o.id) as bill_id,
                       (julianday('now', 'localtime') - julianday(o.updated_at)) * 24 * 60 as elapsed_ready_mins
                FROM orders o
                LEFT JOIN users u ON o.user_id = u.id
                LEFT JOIN users w ON o.waiter_id = w.id
                WHERE o.status != 'CANCELLED'
                ORDER BY o.id DESC LIMIT 50;
            """)
        except Exception as e:
            logger.error(f"Error querying active orders: {e}")
            rows = []

        self.all_orders = rows

        # Calculate counts
        total_active = len([r for r in rows if not r["bill_id"]])
        pending_cnt = len([r for r in rows if r["status"] == "PENDING"])
        preparing_cnt = len([r for r in rows if r["status"] == "PREPARING"])
        ready_cnt = len([r for r in rows if r["status"] == "READY"])
        delayed_cnt = len([r for r in rows if r["status"] == "READY" and float(r["elapsed_ready_mins"] or 0) >= 5.0])
        transit_cnt = len([r for r in rows if r["status"] == "PICKED_UP"])

        # Render KPI Cards
        for widget in self.kpi_container.winfo_children():
            widget.destroy()

        kpi_specs = [
            ("Active Unsettled", str(total_active), "⚡", "#3B82F6"),
            ("Kitchen Queue", str(pending_cnt), "🟡", "#F59E0B"),
            ("Cooking / Prep", str(preparing_cnt), "👨‍🍳", "#EC4899"),
            ("Ready to Serve", str(ready_cnt), "🔔", "#10B981"),
            ("Delayed Ready (>5m)", str(delayed_cnt), "⚠️", "#EF4444" if delayed_cnt > 0 else palette["text_secondary"]),
            ("In Transit", str(transit_cnt), "🚶", "#8B5CF6"),
        ]

        for title, val, icon, accent_col in kpi_specs:
            card = ctk.CTkFrame(
                self.kpi_container,
                fg_color=palette["bg_card"],
                corner_radius=8,
                border_width=1,
                border_color=palette["border"],
                height=65
            )
            card.pack(side="left", fill="x", expand=True, padx=4)
            card.pack_propagate(False)

            inner = ctk.CTkFrame(card, fg_color="transparent")
            inner.pack(fill="both", expand=True, padx=12, pady=8)

            left = ctk.CTkFrame(inner, fg_color="transparent")
            left.pack(side="left")
            ctk.CTkLabel(left, text=title, font=ctk.CTkFont(size=10), text_color=palette["text_secondary"]).pack(anchor="w")
            ctk.CTkLabel(left, text=val, font=ctk.CTkFont(size=16, weight="bold"), text_color=accent_col).pack(anchor="w")

            ctk.CTkLabel(inner, text=icon, font=ctk.CTkFont(size=18)).pack(side="right")

        self._render_order_cards()

    def _render_order_cards(self):
        palette = theme_manager.get_palette()

        for w in self.scroll_container.winfo_children():
            w.destroy()

        # Filter orders
        filtered = []
        for o in self.all_orders:
            st = o["status"]
            has_bill = bool(o["bill_id"])
            elapsed_ready = float(o["elapsed_ready_mins"] or 0.0)

            if self.current_filter == "ALL":
                if not has_bill:
                    filtered.append(o)
            elif self.current_filter == "PENDING" and st == "PENDING":
                filtered.append(o)
            elif self.current_filter == "PREPARING" and st == "PREPARING":
                filtered.append(o)
            elif self.current_filter == "READY" and st == "READY":
                filtered.append(o)
            elif self.current_filter == "DELAYED" and (st == "READY" and elapsed_ready >= 5.0):
                filtered.append(o)
            elif self.current_filter == "PICKED_UP" and st == "PICKED_UP":
                filtered.append(o)
            elif self.current_filter == "SERVED" and st == "SERVED":
                filtered.append(o)
            elif self.current_filter == "COMPLETED" and (st == "COMPLETED" or has_bill):
                filtered.append(o)

        if not filtered:
            empty_box = ctk.CTkFrame(self.scroll_container, fg_color=palette["bg_card"], corner_radius=10, border_width=1, border_color=palette["border"])
            empty_box.pack(fill="x", padx=10, pady=25)
            ctk.CTkLabel(
                empty_box,
                text="✨ No active orders matching the selected status filter.",
                font=ctk.CTkFont(size=13, weight="bold"),
                text_color=palette["text_secondary"]
            ).pack(padx=20, pady=30)
            return

        grid_frame = ctk.CTkFrame(self.scroll_container, fg_color="transparent")
        grid_frame.pack(fill="both", expand=True)
        grid_frame.columnconfigure((0, 1), weight=1)

        status_colors = {
            "PENDING": ("#FEF3C7", "#D97706"),
            "ACCEPTED": ("#EDE9FE", "#6D28D9"),
            "PREPARING": ("#FCE7F3", "#DB2777"),
            "READY": ("#D1FAE5", "#059669"),
            "PICKED_UP": ("#FEF3C7", "#B45309"),
            "SERVED": ("#DCFCE7", "#15803D"),
            "COMPLETED": ("#EEF2FF", "#4F46E5"),
            "CANCELLED": ("#FEE2E2", "#DC2626")
        }

        for idx, ord_row in enumerate(filtered):
            row_idx = idx // 2
            col_idx = idx % 2

            oid = ord_row["id"]
            onum = ord_row["order_number"]
            tbl = ord_row["table_number"] or "Takeaway"
            cust = ord_row["customer_name"] or "Guest"
            st = ord_row["status"]
            created = ord_row["created_at"] or ""
            server = ord_row["server_name"] or "Staff"
            waiter = ord_row["waiter_name"] or "Unassigned"
            total_val = ord_row["total_val"] or 0.0
            elapsed_ready = float(ord_row["elapsed_ready_mins"] or 0.0)
            is_delayed_ready = (st == "READY" and elapsed_ready >= 5.0)

            border_col = "#EF4444" if is_delayed_ready else palette["border"]

            card = ctk.CTkFrame(
                grid_frame,
                fg_color=palette["bg_card"],
                corner_radius=10,
                border_width=2 if is_delayed_ready else 1,
                border_color=border_col
            )
            card.grid(row=row_idx, column=col_idx, sticky="nsew", padx=6, pady=6)

            # Card Header
            c_header = ctk.CTkFrame(card, fg_color="transparent")
            c_header.pack(fill="x", padx=12, pady=(10, 6))

            ord_lbl = ctk.CTkLabel(
                c_header,
                text=f"{onum}  •  {tbl}",
                font=ctk.CTkFont(size=13, weight="bold"),
                text_color=palette.get("heading", palette["text_primary"])
            )
            ord_lbl.pack(side="left")

            s_bg, s_fg = status_colors.get(st, ("#F1F5F9", "#475569"))
            pill = ctk.CTkFrame(c_header, fg_color=s_bg, corner_radius=6)
            pill.pack(side="right")
            ctk.CTkLabel(pill, text=st, font=ctk.CTkFont(size=9, weight="bold"), text_color=s_fg).pack(padx=6, pady=2)

            if is_delayed_ready:
                del_pill = ctk.CTkFrame(c_header, fg_color="#FEE2E2", corner_radius=6)
                del_pill.pack(side="right", padx=(0, 6))
                ctk.CTkLabel(del_pill, text=f"⚠️ {int(elapsed_ready)}m unserved", font=ctk.CTkFont(size=9, weight="bold"), text_color="#EF4444").pack(padx=6, pady=2)

            # Sub-info: Customer, Server & Assigned Waiter
            meta_box = ctk.CTkFrame(card, fg_color="transparent")
            meta_box.pack(fill="x", padx=12, pady=(0, 6))
            ctk.CTkLabel(
                meta_box,
                text=f"Guest: {cust}  |  Server: {server}  |  Ordered: {created[-8:]}",
                font=ctk.CTkFont(size=10),
                text_color=palette["text_secondary"]
            ).pack(anchor="w")

            w_row = ctk.CTkFrame(card, fg_color="transparent")
            w_row.pack(fill="x", padx=12, pady=(0, 6))
            ctk.CTkLabel(
                w_row,
                text=f"Assigned Waiter: {waiter}",
                font=ctk.CTkFont(size=10, weight="bold"),
                text_color=palette["accent"] if ord_row["waiter_name"] else palette["text_secondary"]
            ).pack(side="left")

            # Fetch line items
            items_box = ctk.CTkFrame(card, fg_color=palette["bg_secondary"], corner_radius=6)
            items_box.pack(fill="x", padx=12, pady=(0, 8))

            items = self.order_repo.get_order_items(oid)
            for it in items[:4]:
                it_row = ctk.CTkFrame(items_box, fg_color="transparent")
                it_row.pack(fill="x", padx=8, pady=1)
                ctk.CTkLabel(it_row, text=f"{it.quantity}x {it.item_name}", font=ctk.CTkFont(size=11), text_color=palette["text_primary"]).pack(side="left")
                ctk.CTkLabel(it_row, text=f"₹{float(it.line_total):,.2f}", font=ctk.CTkFont(size=10), text_color=palette["text_secondary"]).pack(side="right")

            if len(items) > 4:
                ctk.CTkLabel(items_box, text=f"+ {len(items)-4} more dishes...", font=ctk.CTkFont(size=9, slant="italic"), text_color=palette["text_secondary"]).pack(anchor="w", padx=8, pady=(0, 2))

            # Actions Row
            act_row = ctk.CTkFrame(card, fg_color="transparent")
            act_row.pack(fill="x", padx=12, pady=(0, 10))

            ctk.CTkLabel(
                act_row,
                text=f"Total: ₹{float(total_val):,.2f}",
                font=ctk.CTkFont(size=12, weight="bold"),
                text_color=palette["accent"]
            ).pack(side="left")

            btn_box = ctk.CTkFrame(act_row, fg_color="transparent")
            btn_box.pack(side="right")

            # Reassign / Assign Waiter Button
            ctk.CTkButton(
                btn_box,
                text="👤 Assign Waiter",
                font=ctk.CTkFont(size=10, weight="bold"),
                height=26,
                fg_color=palette["bg_secondary"],
                hover_color=palette["border"],
                text_color=palette["text_primary"],
                command=lambda i=oid, num=onum, wid=ord_row["waiter_id"]: AssignWaiterDialog(
                    self, order_id=i, order_number=num, current_waiter_id=wid, on_assigned=self._load_active_orders
                )
            ).pack(side="left", padx=2)

            if st == "PENDING":
                ctk.CTkButton(
                    btn_box,
                    text="👨‍🍳 Prep",
                    font=ctk.CTkFont(size=10, weight="bold"),
                    height=26,
                    width=60,
                    fg_color="#F59E0B",
                    hover_color="#D97706",
                    command=lambda i=oid: self._update_order_status(i, "PREPARING")
                ).pack(side="left", padx=2)

            if st in ["PENDING", "PREPARING"]:
                ctk.CTkButton(
                    btn_box,
                    text="🔔 Ready",
                    font=ctk.CTkFont(size=10, weight="bold"),
                    height=26,
                    width=60,
                    fg_color="#10B981",
                    hover_color="#059669",
                    command=lambda i=oid: self._update_order_status(i, "READY")
                ).pack(side="left", padx=2)

            if not ord_row["bill_id"]:
                ctk.CTkButton(
                    btn_box,
                    text="💳 Settle",
                    font=ctk.CTkFont(size=10, weight="bold"),
                    height=26,
                    width=60,
                    fg_color=palette["accent"],
                    hover_color=palette["accent_hover"],
                    command=lambda i=oid: self._trigger_settle(i)
                ).pack(side="left", padx=2)

    def _update_order_status(self, order_id: int, new_status: str):
        try:
            db.execute("UPDATE orders SET status = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?;", (new_status, order_id))
            db.execute(
                """INSERT INTO audit_logs (username, action, module, details)
                   VALUES ('Manager', ?, 'FLOOR_ORDERS', ?);""",
                (f"SET_STATUS_{new_status}", f"Order #{order_id} status updated to {new_status}")
            )
            self._load_active_orders()
        except Exception as e:
            logger.error(f"Error updating order #{order_id} status: {e}")

    def _trigger_settle(self, order_id: int):
        if self.on_settle_order:
            self.on_settle_order(order_id)
