"""Manager Active Orders Live Floor & Kitchen Monitor."""
from typing import Callable, Optional
from datetime import datetime
import customtkinter as ctk

from ui.theme_manager import theme_manager
from database.db import db
from repositories.order_repository import OrderRepository
from repositories.billing_repository import BillingRepository
from utils.logger import logger


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

    def on_theme_changed(self, _theme: str):
        if self.winfo_exists():
            palette = theme_manager.get_palette()
            self.configure(fg_color=palette["bg_primary"])
            self._load_active_orders()

    def _build_ui(self):
        palette = theme_manager.get_palette()
        self.configure(fg_color=palette["bg_primary"])

        # Header Frame
        header = ctk.CTkFrame(self, fg_color="transparent")
        header.pack(fill="x", padx=20, pady=(15, 8))

        title_box = ctk.CTkFrame(header, fg_color="transparent")
        title_box.pack(side="left")

        ctk.CTkLabel(
            title_box,
            text="⚡ Live Active Orders & Kitchen Display",
            font=ctk.CTkFont(size=20, weight="bold"),
            text_color=palette.get("heading", palette["text_primary"])
        ).pack(anchor="w")

        ctk.CTkLabel(
            title_box,
            text="Real-time kitchen order dispatch, course progression, and table delivery tracking.",
            font=ctk.CTkFont(size=11),
            text_color=palette["text_secondary"]
        ).pack(anchor="w", pady=(2, 0))

        # Right header controls
        ctrl_box = ctk.CTkFrame(header, fg_color="transparent")
        ctrl_box.pack(side="right")

        ctk.CTkButton(
            ctrl_box,
            text="🔄 Refresh Floor",
            font=ctk.CTkFont(size=11, weight="bold"),
            fg_color=palette["accent"],
            hover_color=palette["accent_hover"],
            height=32,
            width=120,
            command=self._load_active_orders
        ).pack(side="right", padx=4)

        # KPI Summary Cards
        self.kpi_container = ctk.CTkFrame(self, fg_color="transparent")
        self.kpi_container.pack(fill="x", padx=20, pady=(0, 10))

        # Filter Pills Bar
        filter_bar = ctk.CTkFrame(self, fg_color="transparent")
        filter_bar.pack(fill="x", padx=20, pady=(0, 10))

        self.filter_buttons = {}
        for key, label in [
            ("ALL", "All Active Orders"),
            ("PENDING", "🟡 In Queue / Pending"),
            ("PREPARING", "👨‍🍳 In Preparation"),
            ("READY", "🔔 Ready to Serve"),
            ("COMPLETED", "✅ Settle Pending")
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
            btn.pack(side="left", padx=4)
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

        # Query active orders (status in PENDING, PREPARING, READY, or COMPLETED without settled bill)
        try:
            rows = db.fetchall("""
                SELECT o.id, o.order_number, o.table_number, o.customer_name, o.status, o.created_at,
                       u.full_name as server_name,
                       (SELECT COUNT(*) FROM order_items WHERE order_id = o.id) as item_count,
                       (SELECT SUM(line_total) FROM order_items WHERE order_id = o.id) as total_val,
                       (SELECT id FROM bills WHERE order_id = o.id) as bill_id
                FROM orders o
                LEFT JOIN users u ON o.user_id = u.id
                WHERE o.status != 'CANCELLED'
                ORDER BY o.id DESC LIMIT 40;
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

        # Render KPI Cards
        for widget in self.kpi_container.winfo_children():
            widget.destroy()

        kpi_specs = [
            ("Active Unsettled", str(total_active), "⚡", "#3B82F6"),
            ("Kitchen Queue", str(pending_cnt), "🟡", "#F59E0B"),
            ("Cooking / Prep", str(preparing_cnt), "👨‍🍳", "#EC4899"),
            ("Ready to Serve", str(ready_cnt), "🔔", "#10B981"),
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
            ctk.CTkLabel(left, text=val, font=ctk.CTkFont(size=16, weight="bold"), text_color=palette.get("heading", palette["text_primary"])).pack(anchor="w")

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

            if self.current_filter == "ALL":
                if not has_bill:
                    filtered.append(o)
            elif self.current_filter == "PENDING" and st == "PENDING":
                filtered.append(o)
            elif self.current_filter == "PREPARING" and st == "PREPARING":
                filtered.append(o)
            elif self.current_filter == "READY" and st == "READY":
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

        # Render 2-column or 3-column grid of Order Cards
        grid_frame = ctk.CTkFrame(self.scroll_container, fg_color="transparent")
        grid_frame.pack(fill="both", expand=True)
        grid_frame.columnconfigure((0, 1), weight=1)

        status_colors = {
            "PENDING": ("#FEF3C7", "#D97706"),
            "PREPARING": ("#FCE7F3", "#DB2777"),
            "READY": ("#D1FAE5", "#059669"),
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
            total_val = ord_row["total_val"] or 0.0

            card = ctk.CTkFrame(
                grid_frame,
                fg_color=palette["bg_card"],
                corner_radius=10,
                border_width=1,
                border_color=palette["border"]
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

            # Sub-info: Customer & Server
            meta_box = ctk.CTkFrame(card, fg_color="transparent")
            meta_box.pack(fill="x", padx=12, pady=(0, 6))
            ctk.CTkLabel(
                meta_box,
                text=f"Guest: {cust}  |  Server: {server}  |  Ordered: {created[-8:]}",
                font=ctk.CTkFont(size=10),
                text_color=palette["text_secondary"]
            ).pack(anchor="w")

            # Fetch line items for this order
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

            if st == "PENDING":
                ctk.CTkButton(
                    btn_box,
                    text="👨‍🍳 Prep",
                    font=ctk.CTkFont(size=10, weight="bold"),
                    height=26,
                    width=65,
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
                    width=65,
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
                    width=65,
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
