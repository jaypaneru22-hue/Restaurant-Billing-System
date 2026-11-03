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
from utils.logger import logger


class WaiterDashboardFrame(ctk.CTkFrame):
    """Dedicated operational dashboard for floor waiters to manage ready pickups, serving, and tables."""

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
        self.current_filter = initial_filter  # ALL, READY, PICKED_UP, SERVED, TABLES, HISTORY
        self._auto_refresh_id: Optional[str] = None
        self._is_active: bool = True
        self._poll_interval_ms: int = 4000

        # Smart in-place cache
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
            text="Pick up ready dishes from the kitchen pass, serve dining tables, and monitor guest orders.",
            font=ctk.CTkFont(size=11),
            text_color=palette["text_secondary"]
        ).pack(anchor="w", pady=(2, 0))

        # Controls
        ctrl_box = ctk.CTkFrame(header, fg_color="transparent")
        ctrl_box.pack(side="right")

        ctk.CTkButton(
            ctrl_box,
            text="🔄 Refresh",
            font=ctk.CTkFont(size=11, weight="bold"),
            fg_color=palette["accent"],
            hover_color=palette["accent_hover"],
            height=32,
            width=100,
            command=lambda: self._refresh_waiter_data(is_periodic=False)
        ).pack(side="right")

        # -------------------------------------------------------------
        # NEW READY ORDERS ALERT BANNER (Visible when dishes await pickup)
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
        # SUMMARY KPI METRICS BAR
        # -------------------------------------------------------------
        self.kpi_container = ctk.CTkFrame(self, fg_color="transparent")
        self.kpi_container.pack(fill="x", padx=20, pady=(0, 10))

        self.kpi_labels = {}
        kpi_defs = [
            ("ready", "Ready for Pickup", "🔔", "#EF4444"),
            ("transit", "In Transit (Picked Up)", "🚶", "#F59E0B"),
            ("served", "Served Today", "✅", "#10B981"),
            ("tables", "Assigned Tables", "🪑", palette["accent"])
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
            card.pack(side="left", fill="x", expand=True, padx=4)
            card.pack_propagate(False)

            inner = ctk.CTkFrame(card, fg_color="transparent")
            inner.pack(fill="both", expand=True, padx=12, pady=8)

            left = ctk.CTkFrame(inner, fg_color="transparent")
            left.pack(side="left")
            ctk.CTkLabel(left, text=title, font=ctk.CTkFont(size=10), text_color=palette["text_secondary"]).pack(anchor="w")
            val_lbl = ctk.CTkLabel(left, text="0", font=ctk.CTkFont(size=16, weight="bold"), text_color=color)
            val_lbl.pack(anchor="w")
            self.kpi_labels[key] = val_lbl

            ctk.CTkLabel(inner, text=icon, font=ctk.CTkFont(size=20)).pack(side="right")

        # -------------------------------------------------------------
        # FILTER TABS BAR
        # -------------------------------------------------------------
        filter_bar = ctk.CTkFrame(self, fg_color=palette["bg_card"], corner_radius=10, border_width=1, border_color=palette["border"])
        filter_bar.pack(fill="x", padx=20, pady=(0, 10))

        filter_inner = ctk.CTkFrame(filter_bar, fg_color="transparent")
        filter_inner.pack(fill="x", padx=10, pady=8)

        ctk.CTkLabel(filter_inner, text="Service Queue:", font=ctk.CTkFont(size=11, weight="bold"), text_color=palette["text_secondary"]).pack(side="left", padx=(4, 10))

        self.filter_buttons = {}
        filters = [
            ("ALL", "📋 All Active Tasks"),
            ("READY", "🔔 Ready to Pick Up"),
            ("PICKED_UP", "🚶 In Transit"),
            ("SERVED", "✅ Served Today"),
            ("TABLES", "🪑 My Assigned Tables"),
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
            btn.pack(side="left", padx=3)
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

    def _fetch_queue_data(self) -> Tuple[List[Dict], List[Dict], List[Dict], List[Dict]]:
        """Queries ready, in-transit, served, and assigned tables."""
        ready_orders = self.waiter_svc.get_ready_orders()
        transit_orders = self.waiter_svc.get_picked_up_orders(waiter_id=self.waiter_id)
        served_orders = self.waiter_svc.get_served_orders(waiter_id=self.waiter_id, limit=30)
        history_orders = self.waiter_svc.get_serving_history(waiter_id=self.waiter_id, limit=50)
        return ready_orders, transit_orders, served_orders, history_orders

    def _refresh_waiter_data(self, is_periodic: bool = False):
        """Differential smart refresh that avoids unnecessary UI destruction."""
        if not self._is_active or not self.winfo_exists():
            return

        ready_orders, transit_orders, served_orders, history_orders = self._fetch_queue_data()
        assigned_tables = self.waiter_svc.get_assigned_tables(self.waiter_id)
        palette = theme_manager.get_palette()

        # Update KPI Counts
        if "ready" in self.kpi_labels and self.kpi_labels["ready"].winfo_exists():
            self.kpi_labels["ready"].configure(text=str(len(ready_orders)))
        if "transit" in self.kpi_labels and self.kpi_labels["transit"].winfo_exists():
            self.kpi_labels["transit"].configure(text=str(len(transit_orders)))
        if "served" in self.kpi_labels and self.kpi_labels["served"].winfo_exists():
            self.kpi_labels["served"].configure(text=str(len(served_orders)))
        if "tables" in self.kpi_labels and self.kpi_labels["tables"].winfo_exists():
            self.kpi_labels["tables"].configure(text=str(len(assigned_tables)))

        # Update or toggle alert banner
        if len(ready_orders) > 0:
            if not self.alert_banner.winfo_ismapped():
                self.alert_banner.pack(fill="x", padx=20, pady=(0, 10), before=self.kpi_container)
            self.alert_banner_lbl.configure(
                text=f"🔔 {len(ready_orders)} ORDER(S) WAITING AT KITCHEN PASS: Please pick up and deliver immediately!"
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

        # Prepare orders list for order views
        if self.current_filter == "ALL":
            active_list = ready_orders + transit_orders
        elif self.current_filter == "READY":
            active_list = ready_orders
        elif self.current_filter == "PICKED_UP":
            active_list = transit_orders
        elif self.current_filter == "SERVED":
            active_list = served_orders
        elif self.current_filter == "HISTORY":
            active_list = history_orders
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
            tbl = o["table_number"] or "Takeaway"
            cust = o["customer_name"] or "Guest"
            special = (o.get("special_instructions") or "").strip()
            waiter_disp = o.get("waiter_name") or "Unassigned"

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
            pill_color = "#DCFCE7", "#15803D" if st in ("SERVED", "COMPLETED") else (
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

            ctk.CTkLabel(meta, text=f"Guest: {cust}", font=ctk.CTkFont(size=10), text_color=palette["text_secondary"]).pack(side="right")

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
            for it in items:
                it_row = ctk.CTkFrame(items_box, fg_color="transparent")
                it_row.pack(fill="x", padx=8, pady=2)
                ctk.CTkLabel(
                    it_row,
                    text=f"▫ {it.quantity}x  {it.item_name}",
                    font=ctk.CTkFont(size=11, weight="bold"),
                    text_color=palette["text_primary"]
                ).pack(side="left")

            # Action Button Row
            btn_row = ctk.CTkFrame(card, fg_color="transparent")
            btn_row.pack(fill="x", padx=12, pady=(0, 10))

            if st == "READY":
                ctk.CTkButton(
                    btn_row,
                    text="🚶 Mark as Picked Up",
                    font=ctk.CTkFont(size=11, weight="bold"),
                    height=30,
                    fg_color="#F59E0B",
                    hover_color="#D97706",
                    command=lambda i=oid: self._action_pick_up(i)
                ).pack(fill="x")
            elif st == "PICKED_UP":
                ctk.CTkButton(
                    btn_row,
                    text="✅ Mark as Served",
                    font=ctk.CTkFont(size=11, weight="bold"),
                    height=30,
                    fg_color="#10B981",
                    hover_color="#059669",
                    command=lambda i=oid: self._action_mark_served(i)
                ).pack(fill="x")
            elif st in ("SERVED", "COMPLETED"):
                ctk.CTkLabel(
                    btn_row,
                    text="✓ Delivered to Table (Awaiting Counter Billing)",
                    font=ctk.CTkFont(size=10, weight="bold"),
                    text_color="#10B981"
                ).pack(anchor="center", pady=4)

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

            card = ctk.CTkFrame(grid, fg_color=palette["bg_card"], corner_radius=10, border_width=1, border_color=palette["border"])
            card.grid(row=row_idx, column=col_idx, sticky="nsew", padx=6, pady=6)

            c_box = ctk.CTkFrame(card, fg_color="transparent")
            c_box.pack(fill="both", expand=True, padx=12, pady=12)

            ctk.CTkLabel(c_box, text=tbl_num, font=ctk.CTkFont(size=18, weight="bold"), text_color=palette["accent"]).pack(anchor="w")
            ctk.CTkLabel(c_box, text=f"Zone: {zone}  •  Seats: {cap}", font=ctk.CTkFont(size=11), text_color=palette["text_secondary"]).pack(anchor="w", pady=(2, 6))

            status_color = "#10B981" if status == "VACANT" else ("#EF4444" if status == "OCCUPIED" else "#F59E0B")
            ctk.CTkLabel(c_box, text=f"Status: {status}", font=ctk.CTkFont(size=11, weight="bold"), text_color=status_color).pack(anchor="w")

            if onum:
                ctk.CTkLabel(c_box, text=f"Active Order: {onum}", font=ctk.CTkFont(size=10, weight="bold"), text_color=palette["text_primary"]).pack(anchor="w", pady=(4, 0))

    def _action_pick_up(self, order_id: int):
        """Action: Waiter picks up READY order from kitchen pass."""
        ok, msg = self.order_svc.mark_order_picked_up(order_id, self.waiter_id)
        if ok:
            self._rendered_signature = ()
            self._refresh_waiter_data(is_periodic=False)

    def _action_mark_served(self, order_id: int):
        """Action: Waiter delivers order to table."""
        ok, msg = self.order_svc.mark_order_served(order_id, self.waiter_id)
        if ok:
            self._rendered_signature = ()
            self._refresh_waiter_data(is_periodic=False)
