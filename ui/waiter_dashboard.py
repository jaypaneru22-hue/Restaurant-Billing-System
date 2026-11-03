"""Waiter Floor Service & Live Serving Dispatch Dashboard."""
from typing import Optional, Callable, List, Dict, Tuple
from datetime import datetime
import customtkinter as ctk

from ui.theme_manager import theme_manager
from database.db import db
from services.order_service import OrderService, order_service
from services.waiter_service import WaiterService, waiter_service
from services.auth_service import AuthService, auth_service
from repositories.order_repository import OrderRepository
from utils.window_utils import center_dialog
from utils.logger import logger


class OrderDetailDialog(ctk.CTkToplevel):
    """Modal dialog displaying comprehensive line-item details and chef notes for a dish ticket."""

    def __init__(self, master, order_data: Dict, order_svc: OrderService = order_service, **kwargs):
        super().__init__(master, **kwargs)
        self.order_data = order_data
        self.order_svc = order_svc

        self.title(f"Order #{order_data['order_number']} — Details")
        self.resizable(False, False)
        center_dialog(self, master, target_width=520, target_height=560, min_width=480, min_height=500)
        self.grab_set()

        self._build_ui()

    def _build_ui(self):
        palette = theme_manager.get_palette()
        self.configure(fg_color=palette["bg_primary"])

        # Header
        head = ctk.CTkFrame(self, fg_color="transparent")
        head.pack(fill="x", padx=20, pady=(16, 8))

        ctk.CTkLabel(
            head,
            text=f"📋 Order Details — #{self.order_data['order_number']}",
            font=ctk.CTkFont(size=16, weight="bold"),
            text_color=palette.get("heading", palette["text_primary"])
        ).pack(side="left")

        st = self.order_data.get("status", "READY")
        st_colors = {
            "READY": ("#FEE2E2", "#B91C1C"),
            "PICKED_UP": ("#FEF3C7", "#B45309"),
            "SERVED": ("#DCFCE7", "#15803D"),
            "COMPLETED": ("#E0E7FF", "#3730A3")
        }
        bg, fg = st_colors.get(st, ("#F1F5F9", "#475569"))
        pill = ctk.CTkFrame(head, fg_color=bg, corner_radius=6)
        pill.pack(side="right")
        ctk.CTkLabel(pill, text=st, font=ctk.CTkFont(size=10, weight="bold"), text_color=fg).pack(padx=8, pady=2)

        # Meta summary card
        meta = ctk.CTkFrame(self, fg_color=palette["bg_card"], corner_radius=8, border_width=1, border_color=palette["border"])
        meta.pack(fill="x", padx=20, pady=(0, 10))

        tbl = self.order_data.get("table_number") or "Takeaway"
        cust = self.order_data.get("customer_name") or "Guest Diner"
        server = self.order_data.get("waiter_name") or "Unassigned"
        created = self.order_data.get("created_at") or "Unknown"

        ctk.CTkLabel(meta, text=f"🪑 Table / Station: {tbl}", font=ctk.CTkFont(size=11, weight="bold"), text_color=palette["text_primary"]).grid(row=0, column=0, sticky="w", padx=12, pady=(8, 2))
        ctk.CTkLabel(meta, text=f"👤 Guest: {cust}", font=ctk.CTkFont(size=11), text_color=palette["text_secondary"]).grid(row=0, column=1, sticky="w", padx=12, pady=(8, 2))
        ctk.CTkLabel(meta, text=f"🚶 Assigned Server: {server}", font=ctk.CTkFont(size=11), text_color=palette["text_secondary"]).grid(row=1, column=0, sticky="w", padx=12, pady=(2, 8))
        ctk.CTkLabel(meta, text=f"🕒 Placed: {created}", font=ctk.CTkFont(size=11), text_color=palette["text_secondary"]).grid(row=1, column=1, sticky="w", padx=12, pady=(2, 8))

        # Special Kitchen Notes if any
        notes = (self.order_data.get("special_instructions") or "").strip()
        if notes:
            n_box = ctk.CTkFrame(self, fg_color="#451A03", corner_radius=6, border_width=1, border_color="#F59E0B")
            n_box.pack(fill="x", padx=20, pady=(0, 10))
            ctk.CTkLabel(n_box, text=f"📝 Kitchen Instructions:\n{notes}", font=ctk.CTkFont(size=11, weight="bold"), text_color="#FCD34D", justify="left").pack(padx=12, pady=6, anchor="w")

        # Line items container
        items_frame = ctk.CTkScrollableFrame(self, fg_color=palette["bg_secondary"], corner_radius=8, height=220)
        items_frame.pack(fill="both", expand=True, padx=20, pady=(0, 12))

        order_repo = OrderRepository(db)
        items = order_repo.get_order_items(self.order_data["id"])

        subtotal = 0.0
        for it in items:
            i_row = ctk.CTkFrame(items_frame, fg_color="transparent")
            i_row.pack(fill="x", padx=8, pady=4)

            ctk.CTkLabel(i_row, text=f"{it.quantity}x  {it.item_name}", font=ctk.CTkFont(size=12, weight="bold"), text_color=palette["text_primary"]).pack(side="left")
            line_tot = float(it.line_total)
            subtotal += line_tot
            ctk.CTkLabel(i_row, text=f"₹{line_tot:,.2f}", font=ctk.CTkFont(size=12), text_color=palette["text_secondary"]).pack(side="right")

        # Bottom Subtotal & Close
        bot = ctk.CTkFrame(self, fg_color="transparent")
        bot.pack(fill="x", padx=20, pady=(0, 16))

        ctk.CTkLabel(
            bot,
            text=f"Total Items: {len(items)}  |  Ticket Value: ₹{subtotal:,.2f}",
            font=ctk.CTkFont(size=12, weight="bold"),
            text_color=palette["accent"]
        ).pack(side="left")

        ctk.CTkButton(
            bot,
            text="Close (Esc)",
            font=ctk.CTkFont(size=11, weight="bold"),
            fg_color=palette["bg_card"],
            text_color=palette["text_primary"],
            hover_color=palette["border"],
            height=32,
            width=90,
            command=self.destroy
        ).pack(side="right")

        self.bind("<Escape>", lambda e: self.destroy())


class ServedConfirmDialog(ctk.CTkToplevel):
    """Confirmation modal prior to marking an order as served."""

    def __init__(self, master, order_number: str, table_number: str, on_confirm: Callable[[], None], **kwargs):
        super().__init__(master, **kwargs)
        self.on_confirm = on_confirm

        self.title("Confirm Food Delivery")
        self.resizable(False, False)
        center_dialog(self, master, target_width=420, target_height=220, min_width=380, min_height=200)
        self.grab_set()

        palette = theme_manager.get_palette()
        self.configure(fg_color=palette["bg_primary"])

        card = ctk.CTkFrame(self, fg_color=palette["bg_card"], corner_radius=10, border_width=1, border_color=palette["border"])
        card.pack(fill="both", expand=True, padx=16, pady=16)

        ctk.CTkLabel(
            card,
            text="✅ Confirm Delivery to Table",
            font=ctk.CTkFont(size=15, weight="bold"),
            text_color=palette.get("heading", palette["text_primary"])
        ).pack(anchor="w", padx=16, pady=(14, 6))

        ctk.CTkLabel(
            card,
            text=f"Have all prepared dishes for Order #{order_number}\nbeen delivered to {table_number}?",
            font=ctk.CTkFont(size=12),
            text_color=palette["text_secondary"],
            justify="left"
        ).pack(anchor="w", padx=16, pady=(0, 16))

        btn_row = ctk.CTkFrame(card, fg_color="transparent")
        btn_row.pack(fill="x", padx=16, pady=(0, 12))

        ctk.CTkButton(
            btn_row,
            text="Cancel",
            font=ctk.CTkFont(size=11, weight="bold"),
            fg_color=palette["bg_secondary"],
            text_color=palette["text_primary"],
            hover_color=palette["border"],
            height=32,
            width=90,
            command=self.destroy
        ).pack(side="left")

        ctk.CTkButton(
            btn_row,
            text="Yes, Mark as Served",
            font=ctk.CTkFont(size=11, weight="bold"),
            fg_color="#10B981",
            hover_color="#059669",
            text_color="#FFFFFF",
            height=32,
            width=150,
            command=self._handle_confirm
        ).pack(side="right")

    def _handle_confirm(self):
        self.destroy()
        self.on_confirm()


class WaiterProfileDialog(ctk.CTkToplevel):
    """Displays authenticated staff profile, shift info, and server telemetry."""

    def __init__(self, master, waiter_id: int, auth_svc: AuthService = auth_service, waiter_svc: WaiterService = waiter_service, **kwargs):
        super().__init__(master, **kwargs)
        self.waiter_id = waiter_id
        self.auth_svc = auth_svc
        self.waiter_svc = waiter_svc

        self.title("RestoPro — Floor Server Profile")
        self.resizable(False, False)
        center_dialog(self, master, target_width=440, target_height=420, min_width=400, min_height=380)
        self.grab_set()

        self._build_ui()

    def _build_ui(self):
        palette = theme_manager.get_palette()
        self.configure(fg_color=palette["bg_primary"])

        curr_user = self.auth_svc.current_user

        card = ctk.CTkFrame(self, fg_color=palette["bg_card"], corner_radius=10, border_width=1, border_color=palette["border"])
        card.pack(fill="both", expand=True, padx=16, pady=16)

        ctk.CTkLabel(
            card,
            text="👤 Floor Server Identity",
            font=ctk.CTkFont(size=16, weight="bold"),
            text_color=palette.get("heading", palette["text_primary"])
        ).pack(anchor="w", padx=16, pady=(16, 10))

        # Avatar Pill
        avatar_box = ctk.CTkFrame(card, fg_color=palette["bg_secondary"], corner_radius=8)
        avatar_box.pack(fill="x", padx=16, pady=(0, 12))

        ctk.CTkLabel(
            avatar_box,
            text=f"Server: {curr_user.full_name if curr_user else 'Floor Waiter'}",
            font=ctk.CTkFont(size=13, weight="bold"),
            text_color=palette["text_primary"]
        ).pack(anchor="w", padx=12, pady=(10, 2))

        ctk.CTkLabel(
            avatar_box,
            text=f"Username: {curr_user.username if curr_user else 'waiter1'}  •  Role: WAITER",
            font=ctk.CTkFont(size=11),
            text_color=palette["accent"]
        ).pack(anchor="w", padx=12, pady=(0, 10))

        # Stats
        telemetry = self.waiter_svc.get_waiter_telemetry(self.waiter_id)
        stat_frame = ctk.CTkFrame(card, fg_color="transparent")
        stat_frame.pack(fill="x", padx=16, pady=(0, 12))

        rows = [
            ("Assigned Tables:", f"{telemetry.get('tables_count', 0)} active tables"),
            ("Orders In Service:", f"{telemetry.get('transit_count', 0)} orders"),
            ("Served Orders Today:", f"{telemetry.get('served_count', 0)} orders delivered"),
            ("Pending Table Requests:", f"{telemetry.get('requests_count', 0)} requests"),
            ("Assigned Shift:", "Floor Service — Shift A (Full Day)"),
            ("Account Status:", "Active & Authenticated (Database Verified)")
        ]

        for idx, (label, val) in enumerate(rows):
            r = ctk.CTkFrame(stat_frame, fg_color="transparent")
            r.pack(fill="x", pady=2)
            ctk.CTkLabel(r, text=label, font=ctk.CTkFont(size=11, weight="bold"), text_color=palette["text_secondary"]).pack(side="left")
            ctk.CTkLabel(r, text=val, font=ctk.CTkFont(size=11), text_color=palette["text_primary"]).pack(side="right")

        ctk.CTkButton(
            card,
            text="Close (Esc)",
            font=ctk.CTkFont(size=11, weight="bold"),
            fg_color=palette["accent"],
            hover_color=palette["accent_hover"],
            height=32,
            command=self.destroy
        ).pack(side="bottom", fill="x", padx=16, pady=16)

        self.bind("<Escape>", lambda e: self.destroy())


class WaiterDashboardFrame(ctk.CTkFrame):
    """Dedicated operational dashboard for floor waiters to manage ready pickups, serving, customer requests, and tables."""

    def __init__(
        self,
        master,
        waiter_id: Optional[int] = None,
        initial_filter: str = "ALL",
        order_svc: OrderService = order_service,
        waiter_svc: WaiterService = waiter_service,
        auth_svc: AuthService = auth_service,
        **kwargs
    ):
        super().__init__(master, **kwargs)
        self.waiter_id = waiter_id or (auth_svc.current_user.id if auth_svc.current_user else 1)
        self.order_svc = order_svc
        self.waiter_svc = waiter_svc
        self.auth_svc = auth_svc
        self.current_filter = initial_filter  # ALL, READY, PICKED_UP, SERVED, TABLES, REQUESTS, HISTORY
        self._auto_refresh_id: Optional[str] = None
        self._is_active: bool = True
        self._poll_interval_ms: int = 4000
        self._history_search_query: str = ""

        # Differential cache
        self._rendered_signature: Tuple = ()
        self._card_timer_labels: Dict[int, Tuple[ctk.CTkLabel, float]] = {}

        theme_manager.subscribe(self.on_theme_changed)
        self._build_ui()
        self._refresh_waiter_data(is_periodic=False)
        self._schedule_refresh()

    def destroy(self):
        """Cancels all active refresh timers and cleans up listeners."""
        self._is_active = False
        if self._auto_refresh_id is not None:
            try:
                self.after_cancel(self._auto_refresh_id)
            except Exception:
                pass
            self._auto_refresh_id = None
        theme_manager.unsubscribe(self.on_theme_changed)
        super().destroy()

    def on_theme_changed(self, _theme: str):
        if self._is_active and self.winfo_exists():
            palette = theme_manager.get_palette()
            self.configure(fg_color=palette["bg_primary"])
            self._rendered_signature = ()
            self._refresh_waiter_data(is_periodic=False)

    def _schedule_refresh(self):
        """Ensures exactly ONE active refresh scheduler is queued."""
        if not self._is_active or not self.winfo_exists():
            return
        if self._auto_refresh_id is not None:
            try:
                self.after_cancel(self._auto_refresh_id)
            except Exception:
                pass
            self._auto_refresh_id = None
        self._auto_refresh_id = self.after(self._poll_interval_ms, self._on_auto_refresh_tick)

    def _on_auto_refresh_tick(self):
        """Periodic auto-refresh callback with error boundary."""
        self._auto_refresh_id = None
        if not self._is_active or not self.winfo_exists():
            return
        try:
            self._refresh_waiter_data(is_periodic=True)
        except Exception as e:
            logger.error(f"Error during Waiter Dashboard periodic refresh: {e}")
        finally:
            if self._is_active and self.winfo_exists():
                self._schedule_refresh()

    def _build_ui(self):
        palette = theme_manager.get_palette()
        self.configure(fg_color=palette["bg_primary"])

        curr_user = self.auth_svc.current_user
        waiter_name = curr_user.full_name if curr_user else "Floor Waiter"

        # -------------------------------------------------------------
        # TOP HEADER
        # -------------------------------------------------------------
        header = ctk.CTkFrame(self, fg_color="transparent")
        header.pack(fill="x", padx=20, pady=(15, 8))

        title_box = ctk.CTkFrame(header, fg_color="transparent")
        title_box.pack(side="left")

        ctk.CTkLabel(
            title_box,
            text=f"🍽️ Waiter Floor Service — {waiter_name}",
            font=ctk.CTkFont(size=20, weight="bold"),
            text_color=palette.get("heading", palette["text_primary"])
        ).pack(anchor="w")

        ctk.CTkLabel(
            title_box,
            text="Pick up ready dishes from kitchen pass, attend guest table requests, and deliver food.",
            font=ctk.CTkFont(size=11),
            text_color=palette["text_secondary"]
        ).pack(anchor="w", pady=(2, 0))

        # Controls
        ctrl_box = ctk.CTkFrame(header, fg_color="transparent")
        ctrl_box.pack(side="right")

        ctk.CTkButton(
            ctrl_box,
            text="👤 My Profile",
            font=ctk.CTkFont(size=11, weight="bold"),
            fg_color=palette["bg_card"],
            text_color=palette["text_primary"],
            hover_color=palette["border"],
            height=32,
            width=90,
            command=self._open_profile_dialog
        ).pack(side="left", padx=(0, 8))

        ctk.CTkButton(
            ctrl_box,
            text="🔄 Refresh",
            font=ctk.CTkFont(size=11, weight="bold"),
            fg_color=palette["accent"],
            hover_color=palette["accent_hover"],
            height=32,
            width=90,
            command=lambda: self._refresh_waiter_data(is_periodic=False)
        ).pack(side="left")

        # -------------------------------------------------------------
        # NEW READY ORDERS ALERT BANNER
        # -------------------------------------------------------------
        self.alert_banner = ctk.CTkFrame(self, fg_color="#451A03", corner_radius=8, border_width=1, border_color="#F59E0B")
        self.alert_banner_lbl = ctk.CTkLabel(
            self.alert_banner,
            text="🔔 DISHES WAITING AT KITCHEN PASS: Orders marked READY require immediate pickup!",
            font=ctk.CTkFont(size=11, weight="bold"),
            text_color="#FCD34D"
        )
        self.alert_banner_lbl.pack(padx=14, pady=8)

        # -------------------------------------------------------------
        # SUMMARY KPI METRICS BAR (5 Live Metrics)
        # -------------------------------------------------------------
        self.kpi_container = ctk.CTkFrame(self, fg_color="transparent")
        self.kpi_container.pack(fill="x", padx=20, pady=(0, 10))

        self.kpi_labels = {}
        kpi_defs = [
            ("ready", "Ready for Pickup", "🔔", "#EF4444"),
            ("transit", "In Service (Picked Up)", "🚶", "#F59E0B"),
            ("served", "Served Orders Today", "✅", "#10B981"),
            ("tables", "Assigned Tables", "🪑", palette["accent"]),
            ("requests", "Customer Requests", "🛎️", "#EC4899")
        ]

        for key, title, icon, color in kpi_defs:
            card = ctk.CTkFrame(
                self.kpi_container,
                fg_color=palette["bg_card"],
                corner_radius=8,
                border_width=1,
                border_color=palette["border"],
                height=65
            )
            card.pack(side="left", fill="x", expand=True, padx=3)
            card.pack_propagate(False)

            inner = ctk.CTkFrame(card, fg_color="transparent")
            inner.pack(fill="both", expand=True, padx=10, pady=8)

            left = ctk.CTkFrame(inner, fg_color="transparent")
            left.pack(side="left")
            ctk.CTkLabel(left, text=title, font=ctk.CTkFont(size=10), text_color=palette["text_secondary"]).pack(anchor="w")
            val_lbl = ctk.CTkLabel(left, text="0", font=ctk.CTkFont(size=15, weight="bold"), text_color=color)
            val_lbl.pack(anchor="w")
            self.kpi_labels[key] = val_lbl

            ctk.CTkLabel(inner, text=icon, font=ctk.CTkFont(size=18)).pack(side="right")

        # -------------------------------------------------------------
        # FILTER TABS BAR
        # -------------------------------------------------------------
        filter_bar = ctk.CTkFrame(self, fg_color=palette["bg_card"], corner_radius=10, border_width=1, border_color=palette["border"])
        filter_bar.pack(fill="x", padx=20, pady=(0, 10))

        filter_inner = ctk.CTkFrame(filter_bar, fg_color="transparent")
        filter_inner.pack(fill="x", padx=10, pady=8)

        ctk.CTkLabel(filter_inner, text="Floor Queue:", font=ctk.CTkFont(size=11, weight="bold"), text_color=palette["text_secondary"]).pack(side="left", padx=(4, 10))

        self.filter_buttons = {}
        filters = [
            ("ALL", "📋 All Active Tasks"),
            ("READY", "🔔 Ready to Pick Up"),
            ("PICKED_UP", "🚶 In Transit"),
            ("SERVED", "✅ Served Today"),
            ("TABLES", "🪑 My Assigned Tables"),
            ("REQUESTS", "🛎️ Customer Requests"),
            ("HISTORY", "📜 Serving History")
        ]

        for code, label in filters:
            btn = ctk.CTkButton(
                filter_inner,
                text=label,
                font=ctk.CTkFont(size=10, weight="bold"),
                height=28,
                fg_color=palette["accent"] if code == self.current_filter else palette["bg_secondary"],
                text_color="#FFFFFF" if code == self.current_filter else palette["text_primary"],
                hover_color=palette["accent_hover"],
                command=lambda c=code: self._set_filter(c)
            )
            btn.pack(side="left", padx=2)
            self.filter_buttons[code] = btn

        # -------------------------------------------------------------
        # MAIN SCROLLABLE CONTENT CONTAINER
        # -------------------------------------------------------------
        self.scroll_container = ctk.CTkScrollableFrame(
            self,
            fg_color="transparent",
            scrollbar_button_color=palette.get("sidebar_hover", "#292938")
        )
        self.scroll_container.pack(fill="both", expand=True, padx=20, pady=(0, 15))

    def _open_profile_dialog(self):
        WaiterProfileDialog(self, waiter_id=self.waiter_id, auth_svc=self.auth_svc, waiter_svc=self.waiter_svc)

    def _set_filter(self, filter_code: str):
        if self.current_filter == filter_code:
            return
        self.current_filter = filter_code
        palette = theme_manager.get_palette()
        for c, btn in self.filter_buttons.items():
            if c == filter_code:
                btn.configure(fg_color=palette["accent"], text_color="#FFFFFF")
            else:
                btn.configure(fg_color=palette["bg_secondary"], text_color=palette["text_primary"])
        self._rendered_signature = ()
        self._refresh_waiter_data(is_periodic=False)

    def _fetch_queue_data(self) -> Tuple[List[Dict], List[Dict], List[Dict], List[Dict], List[Dict], List[Dict]]:
        """Queries ready, in-transit, served, assigned tables, requests, and history."""
        ready_orders = [dict(o) for o in self.waiter_svc.get_ready_orders(waiter_id=self.waiter_id)]
        transit_orders = [dict(o) for o in self.waiter_svc.get_picked_up_orders(waiter_id=self.waiter_id)]
        served_orders = [dict(o) for o in self.waiter_svc.get_served_orders(waiter_id=self.waiter_id, limit=30)]
        assigned_tables = [dict(t) for t in self.waiter_svc.get_assigned_tables(waiter_id=self.waiter_id)]
        requests = [dict(r) for r in self.waiter_svc.get_service_requests(waiter_id=self.waiter_id, limit=40)]
        history_orders = [dict(h) for h in self.waiter_svc.get_serving_history(
            waiter_id=self.waiter_id,
            search_query=self._history_search_query if self._history_search_query else None,
            limit=50
        )]
        return ready_orders, transit_orders, served_orders, assigned_tables, requests, history_orders

    def _refresh_waiter_data(self, is_periodic: bool = False):
        """Differential UI updater preserving scroll and active input focus."""
        if not self._is_active or not self.winfo_exists():
            return

        ready_orders, transit_orders, served_orders, assigned_tables, requests, history_orders = self._fetch_queue_data()

        # Update KPI labels
        if "ready" in self.kpi_labels:
            self.kpi_labels["ready"].configure(text=str(len(ready_orders)))
        if "transit" in self.kpi_labels:
            self.kpi_labels["transit"].configure(text=str(len(transit_orders)))
        if "served" in self.kpi_labels:
            self.kpi_labels["served"].configure(text=str(len(served_orders)))
        if "tables" in self.kpi_labels:
            self.kpi_labels["tables"].configure(text=str(len(assigned_tables)))
        if "requests" in self.kpi_labels:
            pending_reqs = sum(1 for r in requests if r["status"] in ("PENDING", "IN_PROGRESS"))
            self.kpi_labels["requests"].configure(text=str(pending_reqs))

        # Alert banner visibility
        if ready_orders:
            if not self.alert_banner.winfo_ismapped():
                self.alert_banner.pack(fill="x", padx=20, pady=(0, 10), before=self.kpi_container)
            self.alert_banner_lbl.configure(
                text=f"🔔 {len(ready_orders)} ORDER(S) WAITING AT KITCHEN PASS: Please pick up and deliver to tables immediately!"
            )
        else:
            if self.alert_banner.winfo_ismapped():
                self.alert_banner.pack_forget()

        # Route by filter
        if self.current_filter == "TABLES":
            current_signature = ("TABLES", theme_manager.current_theme, tuple(t["table_number"] for t in assigned_tables))
            if is_periodic and current_signature == self._rendered_signature:
                return
            self._render_assigned_tables(assigned_tables, current_signature)
            return

        if self.current_filter == "REQUESTS":
            current_signature = ("REQUESTS", theme_manager.current_theme, tuple((r["id"], r["status"]) for r in requests))
            if is_periodic and current_signature == self._rendered_signature:
                return
            self._render_service_requests(requests, current_signature)
            return

        if self.current_filter == "HISTORY":
            current_signature = ("HISTORY", theme_manager.current_theme, self._history_search_query, tuple(o["id"] for o in history_orders))
            if is_periodic and current_signature == self._rendered_signature:
                return
            self._render_serving_history(history_orders, current_signature)
            return

        # Prepare orders list for order views
        if self.current_filter == "ALL":
            active_list = ready_orders + transit_orders
        elif self.current_filter == "READY":
            active_list = ready_orders
        elif self.current_filter == "PICKED_UP":
            active_list = transit_orders
        elif self.current_filter == "SERVED":
            active_list = served_orders
        else:
            active_list = ready_orders

        # Normalize sqlite3.Row objects to standard dicts
        active_list = [dict(o) for o in active_list]

        current_signature = (
            self.current_filter,
            theme_manager.current_theme,
            tuple((o["id"], o["status"], o.get("waiter_id")) for o in active_list)
        )

        # FAST PATH: Steady-state timer updates
        if is_periodic and current_signature == self._rendered_signature:
            for o in active_list:
                oid = o["id"]
                if oid in self._card_timer_labels:
                    lbl, _ = self._card_timer_labels[oid]
                    if lbl.winfo_exists():
                        el = float(o.get("elapsed_ready_mins") or o.get("elapsed_transit_mins") or 0.0)
                        lbl.configure(text=f"⏱️ {int(el)}m ago" if el >= 1.0 else "⏱️ Just now")
            return

        # STRUCTURAL PATH
        self._render_order_cards(active_list, current_signature)

    def _render_order_cards(self, orders: List[Dict], signature: Tuple):
        """Renders order task cards while preserving scroll position."""
        scroll_y = 0.0
        try:
            if hasattr(self.scroll_container, "_parent_canvas"):
                scroll_y = self.scroll_container._parent_canvas.yview()[0]
        except Exception:
            scroll_y = 0.0

        for w in self.scroll_container.winfo_children():
            w.destroy()

        self._rendered_signature = signature
        self._card_timer_labels.clear()
        palette = theme_manager.get_palette()

        if not orders:
            empty = ctk.CTkFrame(self.scroll_container, fg_color=palette["bg_card"], corner_radius=10, border_width=1, border_color=palette["border"])
            empty.pack(fill="x", padx=10, pady=40)
            ctk.CTkLabel(
                empty,
                text="🎉 No pending orders in this queue! All tasks are clear.",
                font=ctk.CTkFont(size=13, weight="bold"),
                text_color=palette["success"]
            ).pack(padx=20, pady=30)
            return

        # 3-column ticket grid
        grid = ctk.CTkFrame(self.scroll_container, fg_color="transparent")
        grid.pack(fill="both", expand=True)
        grid.grid_columnconfigure((0, 1, 2), weight=1, uniform="waiter_grid")

        order_repo = OrderRepository(db)

        for idx, o in enumerate(orders):
            row_idx = idx // 3
            col_idx = idx % 3

            oid = o["id"]
            st = o["status"]
            onum = o["order_number"]
            tbl = o.get("table_number") or "Takeaway"
            cust = o.get("customer_name") or "Guest"
            special = (o.get("special_instructions") or "").strip()
            waiter_disp = o.get("waiter_name") or "Unassigned Queue"
            is_unassigned = o.get("waiter_id") is None

            # Elapsed timer calculation
            if st == "READY":
                el = float(o.get("elapsed_ready_mins") or 0.0)
                timer_str = f"⏱️ Ready {int(el)}m ago" if el >= 1.0 else "⏱️ Ready Just now"
                border_col = "#EF4444" if el > 5.0 else palette["border"]
            elif st == "PICKED_UP":
                el = float(o.get("elapsed_transit_mins") or 0.0)
                timer_str = f"🚶 Picked Up {int(el)}m ago" if el >= 1.0 else "🚶 Picked Up Just now"
                border_col = "#F59E0B"
            else:
                el = 0.0
                timer_str = f"✓ {st}"
                border_col = palette["border"]

            card = ctk.CTkFrame(
                grid,
                fg_color=palette["bg_card"],
                corner_radius=10,
                border_width=2 if st in ("READY", "PICKED_UP") else 1,
                border_color=border_col
            )
            card.grid(row=row_idx, column=col_idx, sticky="nsew", padx=6, pady=6)

            # Header
            c_header = ctk.CTkFrame(card, fg_color="transparent")
            c_header.pack(fill="x", padx=12, pady=(10, 4))

            ctk.CTkLabel(
                c_header,
                text=f"{onum}  •  {tbl}",
                font=ctk.CTkFont(size=13, weight="bold"),
                text_color=palette.get("heading", palette["text_primary"])
            ).pack(side="left")

            # Status pill
            pill_color = ("#DCFCE7", "#15803D") if st in ("SERVED", "COMPLETED") else (
                ("#FEF3C7", "#B45309") if st == "PICKED_UP" else ("#FEE2E2", "#B91C1C")
            )
            pill = ctk.CTkFrame(c_header, fg_color=pill_color[0], corner_radius=6)
            pill.pack(side="right")
            ctk.CTkLabel(pill, text=st, font=ctk.CTkFont(size=9, weight="bold"), text_color=pill_color[1]).pack(padx=6, pady=2)

            # Metadata Row
            meta = ctk.CTkFrame(card, fg_color="transparent")
            meta.pack(fill="x", padx=12, pady=(0, 6))

            lbl_t = ctk.CTkLabel(meta, text=timer_str, font=ctk.CTkFont(size=10, weight="bold"), text_color="#EF4444" if (st == "READY" and el > 5.0) else palette["text_secondary"])
            lbl_t.pack(side="left")
            self._card_timer_labels[oid] = (lbl_t, el)

            server_badge_col = "#F59E0B" if is_unassigned else palette["text_secondary"]
            ctk.CTkLabel(meta, text=f"Guest: {cust}  |  {waiter_disp}", font=ctk.CTkFont(size=10), text_color=server_badge_col).pack(side="right")

            # Special Notes Banner
            if special:
                s_box = ctk.CTkFrame(card, fg_color=palette["bg_secondary"], corner_radius=6, border_width=1, border_color="#F59E0B")
                s_box.pack(fill="x", padx=12, pady=(0, 6))
                ctk.CTkLabel(
                    s_box,
                    text=f"📝 {special}",
                    font=ctk.CTkFont(size=10, weight="bold"),
                    text_color="#F59E0B",
                    wraplength=230,
                    justify="left"
                ).pack(padx=8, pady=4, anchor="w")

            # Items Checklist
            items_box = ctk.CTkFrame(card, fg_color=palette["bg_secondary"], corner_radius=6)
            items_box.pack(fill="x", padx=12, pady=(0, 8))

            items = order_repo.get_order_items(oid)
            for it in items[:4]:  # Show first 4 items, full in modal
                it_row = ctk.CTkFrame(items_box, fg_color="transparent")
                it_row.pack(fill="x", padx=8, pady=1)
                ctk.CTkLabel(
                    it_row,
                    text=f"▫ {it.quantity}x  {it.item_name}",
                    font=ctk.CTkFont(size=10, weight="bold"),
                    text_color=palette["text_primary"]
                ).pack(side="left")

            if len(items) > 4:
                ctk.CTkLabel(items_box, text=f"... +{len(items)-4} more items", font=ctk.CTkFont(size=9, slant="italic"), text_color=palette["text_secondary"]).pack(padx=8, pady=(0, 2), anchor="w")

            # Action Buttons Row
            btn_row = ctk.CTkFrame(card, fg_color="transparent")
            btn_row.pack(fill="x", padx=12, pady=(0, 10))

            ctk.CTkButton(
                btn_row,
                text="🔍 View Details",
                font=ctk.CTkFont(size=10, weight="bold"),
                height=28,
                width=85,
                fg_color=palette["bg_secondary"],
                hover_color=palette["border"],
                text_color=palette["text_primary"],
                command=lambda od=o: OrderDetailDialog(self, order_data=od, order_svc=self.order_svc)
            ).pack(side="left", padx=(0, 6))

            if st == "READY":
                ctk.CTkButton(
                    btn_row,
                    text="🚶 Mark as Picked Up",
                    font=ctk.CTkFont(size=10, weight="bold"),
                    height=28,
                    fg_color="#F59E0B",
                    hover_color="#D97706",
                    command=lambda i=oid: self._action_pick_up(i)
                ).pack(side="right", fill="x", expand=True)
            elif st == "PICKED_UP":
                ctk.CTkButton(
                    btn_row,
                    text="✅ Mark as Served",
                    font=ctk.CTkFont(size=10, weight="bold"),
                    height=28,
                    fg_color="#10B981",
                    hover_color="#059669",
                    command=lambda i=oid, num=onum, tb=tbl: self._action_mark_served_confirm(i, num, tb)
                ).pack(side="right", fill="x", expand=True)
            elif st in ("SERVED", "COMPLETED"):
                ctk.CTkLabel(
                    btn_row,
                    text="✓ Delivered to Table",
                    font=ctk.CTkFont(size=10, weight="bold"),
                    text_color="#10B981"
                ).pack(side="right", padx=6)

        # Restore scroll position
        try:
            if hasattr(self.scroll_container, "_parent_canvas") and scroll_y > 0.0:
                self.scroll_container._parent_canvas.yview_moveto(scroll_y)
        except Exception:
            pass

    def _render_assigned_tables(self, tables: List[Dict], signature: Tuple):
        """Renders assigned tables management view."""
        for w in self.scroll_container.winfo_children():
            w.destroy()

        self._rendered_signature = signature
        palette = theme_manager.get_palette()

        if not tables:
            empty = ctk.CTkFrame(self.scroll_container, fg_color=palette["bg_card"], corner_radius=10, border_width=1, border_color=palette["border"])
            empty.pack(fill="x", padx=10, pady=40)
            ctk.CTkLabel(
                empty,
                text="ℹ️ No tables currently assigned to you. Speak to your manager to allocate floor zones.",
                font=ctk.CTkFont(size=13, weight="bold"),
                text_color=palette["text_secondary"]
            ).pack(padx=20, pady=30)
            return

        grid = ctk.CTkFrame(self.scroll_container, fg_color="transparent")
        grid.pack(fill="both", expand=True)
        grid.grid_columnconfigure((0, 1, 2, 3), weight=1)

        for idx, t in enumerate(tables):
            row_idx = idx // 4
            col_idx = idx % 4

            tbl_num = t["table_number"]
            zone = t["zone"]
            cap = t["capacity"]
            status = t["status"]
            onum = t.get("order_number")
            ostatus = t.get("order_status")
            cust = t.get("active_customer_name")
            req_cnt = t.get("pending_requests_count", 0)

            border_col = "#EC4899" if req_cnt > 0 else (palette["accent"] if onum else palette["border"])
            card = ctk.CTkFrame(grid, fg_color=palette["bg_card"], corner_radius=10, border_width=2 if req_cnt > 0 else 1, border_color=border_col)
            card.grid(row=row_idx, column=col_idx, sticky="nsew", padx=6, pady=6)

            c_box = ctk.CTkFrame(card, fg_color="transparent")
            c_box.pack(fill="both", expand=True, padx=12, pady=12)

            t_top = ctk.CTkFrame(c_box, fg_color="transparent")
            t_top.pack(fill="x")
            ctk.CTkLabel(t_top, text=tbl_num, font=ctk.CTkFont(size=18, weight="bold"), text_color=palette["accent"]).pack(side="left")

            status_color = "#10B981" if status == "VACANT" else ("#EF4444" if status == "OCCUPIED" else "#F59E0B")
            ctk.CTkLabel(t_top, text=status, font=ctk.CTkFont(size=10, weight="bold"), text_color=status_color).pack(side="right")

            ctk.CTkLabel(c_box, text=f"Zone: {zone}  •  Seats: {cap}", font=ctk.CTkFont(size=11), text_color=palette["text_secondary"]).pack(anchor="w", pady=(2, 4))

            if cust:
                ctk.CTkLabel(c_box, text=f"👤 Guest: {cust}", font=ctk.CTkFont(size=10), text_color=palette["text_primary"]).pack(anchor="w")

            if onum:
                ctk.CTkLabel(c_box, text=f"Active Order: {onum} ({ostatus})", font=ctk.CTkFont(size=10, weight="bold"), text_color=palette["accent"]).pack(anchor="w", pady=(2, 0))

            if req_cnt > 0:
                r_badge = ctk.CTkFrame(c_box, fg_color="#FCE7F3", corner_radius=6)
                r_badge.pack(fill="x", pady=(6, 0))
                ctk.CTkLabel(r_badge, text=f"🛎️ {req_cnt} Guest Request Pending", font=ctk.CTkFont(size=10, weight="bold"), text_color="#BE185D").pack(padx=6, pady=2)

    def _render_service_requests(self, requests: List[Dict], signature: Tuple):
        """Renders the Customer Assistance / Service Requests queue."""
        for w in self.scroll_container.winfo_children():
            w.destroy()

        self._rendered_signature = signature
        palette = theme_manager.get_palette()

        if not requests:
            empty = ctk.CTkFrame(self.scroll_container, fg_color=palette["bg_card"], corner_radius=10, border_width=1, border_color=palette["border"])
            empty.pack(fill="x", padx=10, pady=40)
            ctk.CTkLabel(
                empty,
                text="🎉 No pending customer service requests! All guest tables are satisfied.",
                font=ctk.CTkFont(size=13, weight="bold"),
                text_color=palette["success"]
            ).pack(padx=20, pady=30)
            return

        grid = ctk.CTkFrame(self.scroll_container, fg_color="transparent")
        grid.pack(fill="both", expand=True)
        grid.grid_columnconfigure((0, 1), weight=1)

        req_icons = {
            "Water": "💧",
            "Extra Cutlery": "🍴",
            "Napkins": "🧻",
            "Additional Assistance": "🙋",
            "Other Customer Request": "📝"
        }

        for idx, req in enumerate(requests):
            row_idx = idx // 2
            col_idx = idx % 2

            rid = req["id"]
            tbl = req["table_number"]
            cust = req.get("customer_name") or "Guest Diner"
            rtype = req["request_type"]
            notes = req.get("notes") or ""
            st = req["status"]
            elapsed = float(req.get("elapsed_mins") or 0.0)

            icon = req_icons.get(rtype, "🛎️")
            card_border = "#EF4444" if (st == "PENDING" and elapsed > 3.0) else (
                "#F59E0B" if st == "IN_PROGRESS" else ("#10B981" if st == "RESOLVED" else palette["border"])
            )

            card = ctk.CTkFrame(grid, fg_color=palette["bg_card"], corner_radius=10, border_width=1, border_color=card_border)
            card.grid(row=row_idx, column=col_idx, sticky="nsew", padx=6, pady=6)

            inner = ctk.CTkFrame(card, fg_color="transparent")
            inner.pack(fill="both", expand=True, padx=12, pady=10)

            # Top row
            top = ctk.CTkFrame(inner, fg_color="transparent")
            top.pack(fill="x")

            ctk.CTkLabel(top, text=f"{icon} {rtype} — {tbl}", font=ctk.CTkFont(size=14, weight="bold"), text_color=palette.get("heading", palette["text_primary"])).pack(side="left")

            st_colors = {
                "PENDING": ("#FEE2E2", "#B91C1C"),
                "IN_PROGRESS": ("#FEF3C7", "#B45309"),
                "RESOLVED": ("#DCFCE7", "#15803D")
            }
            bg, fg = st_colors.get(st, ("#F1F5F9", "#475569"))
            pill = ctk.CTkFrame(top, fg_color=bg, corner_radius=6)
            pill.pack(side="right")
            ctk.CTkLabel(pill, text=st, font=ctk.CTkFont(size=9, weight="bold"), text_color=fg).pack(padx=6, pady=2)

            # Meta row
            meta = ctk.CTkFrame(inner, fg_color="transparent")
            meta.pack(fill="x", pady=(4, 6))

            el_str = f"⏱️ Requested {int(elapsed)}m ago" if elapsed >= 1.0 else "⏱️ Requested Just now"
            ctk.CTkLabel(meta, text=el_str, font=ctk.CTkFont(size=10, weight="bold"), text_color="#EF4444" if elapsed > 3.0 and st == "PENDING" else palette["text_secondary"]).pack(side="left")
            ctk.CTkLabel(meta, text=f"Guest: {cust}", font=ctk.CTkFont(size=10), text_color=palette["text_secondary"]).pack(side="right")

            if notes:
                ctk.CTkLabel(inner, text=f'"{notes}"', font=ctk.CTkFont(size=11, slant="italic"), text_color=palette["text_primary"], wraplength=400, justify="left").pack(anchor="w", pady=(0, 6))

            # Action Buttons
            btn_box = ctk.CTkFrame(inner, fg_color="transparent")
            btn_box.pack(fill="x", pady=(4, 0))

            if st == "PENDING":
                ctk.CTkButton(
                    btn_box,
                    text="Accept Request",
                    font=ctk.CTkFont(size=10, weight="bold"),
                    fg_color="#F59E0B",
                    hover_color="#D97706",
                    height=28,
                    command=lambda i=rid: self._action_accept_request(i)
                ).pack(side="left", padx=(0, 6))
            elif st == "IN_PROGRESS":
                ctk.CTkButton(
                    btn_box,
                    text="✅ Mark as Resolved",
                    font=ctk.CTkFont(size=10, weight="bold"),
                    fg_color="#10B981",
                    hover_color="#059669",
                    height=28,
                    command=lambda i=rid: self._action_resolve_request(i)
                ).pack(side="left", padx=(0, 6))
            elif st == "RESOLVED":
                ctk.CTkLabel(btn_box, text="✓ Request Completed", font=ctk.CTkFont(size=10, weight="bold"), text_color="#10B981").pack(side="left")

    def _render_serving_history(self, history: List[Dict], signature: Tuple):
        """Renders detailed serving history table with search query filtering."""
        for w in self.scroll_container.winfo_children():
            w.destroy()

        self._rendered_signature = signature
        palette = theme_manager.get_palette()

        # Search Bar
        search_bar = ctk.CTkFrame(self.scroll_container, fg_color=palette["bg_card"], corner_radius=8, border_width=1, border_color=palette["border"])
        search_bar.pack(fill="x", padx=10, pady=(0, 10))

        s_inner = ctk.CTkFrame(search_bar, fg_color="transparent")
        s_inner.pack(fill="x", padx=12, pady=8)

        ctk.CTkLabel(s_inner, text="🔍 Search History:", font=ctk.CTkFont(size=11, weight="bold"), text_color=palette["text_secondary"]).pack(side="left", padx=(0, 8))

        self.ent_search = ctk.CTkEntry(
            s_inner,
            placeholder_text="Filter by Order #, Table, or Customer name...",
            font=ctk.CTkFont(size=11),
            height=28,
            width=280
        )
        self.ent_search.pack(side="left", padx=(0, 8))
        if self._history_search_query:
            self.ent_search.insert(0, self._history_search_query)

        ctk.CTkButton(
            s_inner,
            text="Search",
            font=ctk.CTkFont(size=10, weight="bold"),
            height=28,
            width=70,
            command=self._apply_history_search
        ).pack(side="left", padx=(0, 4))

        ctk.CTkButton(
            s_inner,
            text="Clear",
            font=ctk.CTkFont(size=10),
            height=28,
            width=60,
            fg_color=palette["bg_secondary"],
            text_color=palette["text_primary"],
            command=self._clear_history_search
        ).pack(side="left")

        if not history:
            empty = ctk.CTkFrame(self.scroll_container, fg_color=palette["bg_card"], corner_radius=10, border_width=1, border_color=palette["border"])
            empty.pack(fill="x", padx=10, pady=40)
            ctk.CTkLabel(
                empty,
                text="ℹ️ No historical serving records matching this criteria.",
                font=ctk.CTkFont(size=13, weight="bold"),
                text_color=palette["text_secondary"]
            ).pack(padx=20, pady=30)
            return

        for o in history:
            row = ctk.CTkFrame(self.scroll_container, fg_color=palette["bg_card"], corner_radius=8, border_width=1, border_color=palette["border"])
            row.pack(fill="x", padx=10, pady=3)

            r_in = ctk.CTkFrame(row, fg_color="transparent")
            r_in.pack(fill="x", padx=14, pady=8)

            left = ctk.CTkFrame(r_in, fg_color="transparent")
            left.pack(side="left")

            ctk.CTkLabel(
                left,
                text=f"Order #{o['order_number']}  •  Table: {o['table_number']}  •  Guest: {o['customer_name'] or 'Guest'}",
                font=ctk.CTkFont(size=12, weight="bold"),
                text_color=palette["text_primary"]
            ).pack(anchor="w")

            dur = o.get("serving_duration_mins")
            dur_str = f"{dur} mins" if dur is not None and float(dur) >= 0 else "N/A"
            ctk.CTkLabel(
                left,
                text=f"Served at: {o['served_at'] or o['created_at']}  |  Service Duration: {dur_str}  |  Server: {o.get('waiter_name') or 'Floor Waiter'}",
                font=ctk.CTkFont(size=10),
                text_color=palette["text_secondary"]
            ).pack(anchor="w", pady=(1, 0))

            right = ctk.CTkFrame(r_in, fg_color="transparent")
            right.pack(side="right")

            st = o["status"]
            st_color = "#10B981" if st == "COMPLETED" else "#6366F1"
            pill = ctk.CTkFrame(right, fg_color=palette["bg_secondary"], corner_radius=6)
            pill.pack(side="right")
            ctk.CTkLabel(pill, text=st, font=ctk.CTkFont(size=10, weight="bold"), text_color=st_color).pack(padx=8, pady=2)

    def _apply_history_search(self):
        self._history_search_query = self.ent_search.get().strip()
        self._rendered_signature = ()
        self._refresh_waiter_data(is_periodic=False)

    def _clear_history_search(self):
        self._history_search_query = ""
        self.ent_search.delete(0, "end")
        self._rendered_signature = ()
        self._refresh_waiter_data(is_periodic=False)

    def _action_pick_up(self, order_id: int):
        """Action: Waiter picks up READY order from kitchen pass."""
        ok, msg = self.order_svc.mark_order_picked_up(order_id, self.waiter_id)
        if ok:
            self._rendered_signature = ()
            self._refresh_waiter_data(is_periodic=False)

    def _action_mark_served_confirm(self, order_id: int, order_number: str, table_number: str):
        """Opens confirmation modal before submitting served status."""
        ServedConfirmDialog(
            self,
            order_number=order_number,
            table_number=table_number,
            on_confirm=lambda: self._action_mark_served(order_id)
        )

    def _action_mark_served(self, order_id: int):
        """Action: Waiter delivers order to table."""
        ok, msg = self.order_svc.mark_order_served(order_id, self.waiter_id)
        if ok:
            self._rendered_signature = ()
            self._refresh_waiter_data(is_periodic=False)

    def _action_accept_request(self, request_id: int):
        """Action: Waiter accepts customer assistance request."""
        ok, msg = self.waiter_svc.accept_service_request(request_id, self.waiter_id)
        if ok:
            self._rendered_signature = ()
            self._refresh_waiter_data(is_periodic=False)

    def _action_resolve_request(self, request_id: int):
        """Action: Waiter marks customer assistance request as resolved."""
        ok, msg = self.waiter_svc.resolve_service_request(request_id, self.waiter_id)
        if ok:
            self._rendered_signature = ()
            self._refresh_waiter_data(is_periodic=False)
