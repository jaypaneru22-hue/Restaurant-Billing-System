"""Chef Kitchen Display System (KDS) & Real-Time Kitchen Order Ticket (KOT) Dispatch."""
from typing import Optional, Callable, List, Dict, Tuple
from datetime import datetime
import time
import customtkinter as ctk

from ui.theme_manager import theme_manager
from database.db import db
from repositories.order_repository import OrderRepository
from utils.logger import logger


class ChefKDSFrame(ctk.CTkFrame):
    """Kitchen Display System for chefs and kitchen expeditor with real-time ticket progression."""

    def __init__(self, master, initial_filter: str = "ALL", order_repo: Optional[OrderRepository] = None, **kwargs):
        super().__init__(master, **kwargs)
        self.order_repo = order_repo or OrderRepository(db)
        self.current_filter = initial_filter  # ALL, PENDING, ACCEPTED, PREPARING, READY
        self._auto_refresh_id: Optional[str] = None
        self._is_active: bool = True
        self._poll_interval_ms: int = 4000  # 4 seconds poll interval (3-5s requirement)

        # Smart in-place diffing cache
        self._rendered_signature: Tuple = ()
        self._card_timer_labels: Dict[int, Tuple[ctk.CTkLabel, float]] = {}

        theme_manager.subscribe(self.on_theme_changed)
        self._build_ui()

        # Perform initial load (blocking UI construction), then schedule single active periodic refresh
        self._refresh_kds_data(is_periodic=False)
        self._schedule_refresh()

    def destroy(self):
        """Cancels all active refresh timers and unbinds events cleanly."""
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
            self._rendered_signature = ()  # Invalidate signature to force redraw with new palette
            self._refresh_kds_data(is_periodic=False)

    def _schedule_refresh(self):
        """Schedules exactly ONE pending refresh tick if screen remains active."""
        if not self._is_active or not self.winfo_exists():
            return

        # Cancel any stray existing timer to guarantee single-instance execution
        if self._auto_refresh_id is not None:
            try:
                self.after_cancel(self._auto_refresh_id)
            except Exception:
                pass
            self._auto_refresh_id = None

        self._auto_refresh_id = self.after(self._poll_interval_ms, self._on_auto_refresh_tick)

    def _on_auto_refresh_tick(self):
        """Periodic auto-refresh timer callback."""
        self._auto_refresh_id = None
        if not self._is_active or not self.winfo_exists():
            return

        try:
            self._refresh_kds_data(is_periodic=True)
        except Exception as e:
            logger.error(f"Error during KDS periodic refresh: {e}")
        finally:
            if self._is_active and self.winfo_exists():
                self._schedule_refresh()

    def _build_ui(self):
        palette = theme_manager.get_palette()
        self.configure(fg_color=palette["bg_primary"])

        # -------------------------------------------------------------
        # TOP HEADER
        # -------------------------------------------------------------
        header = ctk.CTkFrame(self, fg_color="transparent")
        header.pack(fill="x", padx=20, pady=(15, 8))

        title_box = ctk.CTkFrame(header, fg_color="transparent")
        title_box.pack(side="left")

        ctk.CTkLabel(
            title_box,
            text="👨‍🍳 Kitchen Display System (KDS)",
            font=ctk.CTkFont(size=20, weight="bold"),
            text_color=palette.get("heading", palette["text_primary"])
        ).pack(anchor="w")

        ctk.CTkLabel(
            title_box,
            text="Real-time Kitchen Order Tickets (KOT), prep timers, and order dispatch pass.",
            font=ctk.CTkFont(size=11),
            text_color=palette["text_secondary"]
        ).pack(anchor="w", pady=(2, 0))

        # Controls
        ctrl_box = ctk.CTkFrame(header, fg_color="transparent")
        ctrl_box.pack(side="right")

        self.btn_refresh = ctk.CTkButton(
            ctrl_box,
            text="🔄 Refresh KDS",
            font=ctk.CTkFont(size=11, weight="bold"),
            fg_color=palette["accent"],
            hover_color=palette["accent_hover"],
            height=32,
            width=120,
            command=lambda: self._refresh_kds_data(is_periodic=False)
        )
        self.btn_refresh.pack(side="right")

        # -------------------------------------------------------------
        # SUMMARY KPI METRICS BAR (Built once, updated in-place)
        # -------------------------------------------------------------
        self.kpi_container = ctk.CTkFrame(self, fg_color="transparent")
        self.kpi_container.pack(fill="x", padx=20, pady=(0, 10))

        self.kpi_labels = {}
        kpi_defs = [
            ("total", "Total Kitchen Tickets", "👨‍🍳", palette["accent"]),
            ("new", "New Unaccepted (KOT)", "📥", "#3B82F6"),
            ("prep", "Cooking In-Progress", "🔥", "#F59E0B"),
            ("ready", "Ready at Pass", "🔔", "#10B981")
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

        ctk.CTkLabel(filter_inner, text="Ticket Queue Filter:", font=ctk.CTkFont(size=11, weight="bold"), text_color=palette["text_secondary"]).pack(side="left", padx=(4, 10))

        self.filter_buttons = {}
        filters = [
            ("ALL", "📋 All Active"),
            ("PENDING", "📥 New Tickets"),
            ("ACCEPTED", "👍 Accepted"),
            ("PREPARING", "🔥 In Cooking"),
            ("READY", "🔔 Ready to Serve")
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
        # TICKETS GRID CONTAINER (SCROLLABLE)
        # -------------------------------------------------------------
        self.tickets_scroll = ctk.CTkScrollableFrame(
            self,
            fg_color="transparent",
            scrollbar_button_color=palette.get("sidebar_hover", "#292938")
        )
        self.tickets_scroll.pack(fill="both", expand=True, padx=20, pady=(0, 15))

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
        self._rendered_signature = ()  # Invalidate signature to force redraw for new filter
        self._refresh_kds_data(is_periodic=False)

    def _fetch_active_orders(self) -> List[Dict]:
        """Queries all active kitchen tickets from the database.

        Retrieves any order requiring preparation (initial incoming statuses:
        PENDING, NEW, RECEIVED, PENDING_ACCEPTANCE, or in-cooking/ready).
        Excludes only COMPLETED and CANCELLED orders.
        Orders are ordered with incoming unaccepted tickets first, and newest first within group.
        """
        sql = """
            SELECT o.id, o.order_number, o.table_number, o.customer_name, o.status,
                   o.created_at, o.special_instructions, u.username as server_name,
                   (julianday('now', 'localtime') - julianday(o.created_at)) * 24 * 60 as elapsed_mins
            FROM orders o
            LEFT JOIN users u ON o.user_id = u.id
            WHERE o.status NOT IN ('COMPLETED', 'CANCELLED')
            ORDER BY 
                CASE 
                    WHEN o.status IN ('PENDING', 'NEW', 'RECEIVED', 'PENDING_ACCEPTANCE') THEN 1
                    WHEN o.status = 'ACCEPTED' THEN 2
                    WHEN o.status = 'PREPARING' THEN 3
                    WHEN o.status = 'READY' THEN 4
                    ELSE 5
                END ASC,
                o.id DESC;
        """
        try:
            return self.order_repo.db.fetchall(sql)
        except Exception as e:
            logger.error(f"Error fetching KDS orders: {e}")
            return []

    def _refresh_kds_data(self, is_periodic: bool = False):
        """Refreshes KDS data without destroying and recreating the entire screen unnecessarily."""
        if not self._is_active or not self.winfo_exists():
            return

        all_active = self._fetch_active_orders()
        palette = theme_manager.get_palette()

        # Update KPI counts in-place
        total_active = len(all_active)
        new_cnt = len([o for o in all_active if o["status"] in ("PENDING", "NEW", "RECEIVED", "PENDING_ACCEPTANCE")])
        accepted_cnt = len([o for o in all_active if o["status"] == "ACCEPTED"])
        prep_cnt = len([o for o in all_active if o["status"] == "PREPARING"])
        ready_cnt = len([o for o in all_active if o["status"] == "READY"])

        if "total" in self.kpi_labels and self.kpi_labels["total"].winfo_exists():
            self.kpi_labels["total"].configure(text=str(total_active))
        if "new" in self.kpi_labels and self.kpi_labels["new"].winfo_exists():
            self.kpi_labels["new"].configure(text=str(new_cnt))
        if "prep" in self.kpi_labels and self.kpi_labels["prep"].winfo_exists():
            self.kpi_labels["prep"].configure(text=str(prep_cnt))
        if "ready" in self.kpi_labels and self.kpi_labels["ready"].winfo_exists():
            self.kpi_labels["ready"].configure(text=str(ready_cnt))

        # Filter tickets
        if self.current_filter == "ALL":
            filtered_tickets = all_active
        elif self.current_filter in ("PENDING", "NEW", "RECEIVED", "PENDING_ACCEPTANCE"):
            filtered_tickets = [o for o in all_active if o["status"] in ("PENDING", "NEW", "RECEIVED", "PENDING_ACCEPTANCE")]
        else:
            filtered_tickets = [o for o in all_active if o["status"] == self.current_filter]

        # Form signature representing structural ticket state
        current_signature = (
            self.current_filter,
            theme_manager.current_theme,
            tuple((o["id"], o["status"], o["special_instructions"] if "special_instructions" in o.keys() else "") for o in filtered_tickets)
        )

        # -------------------------------------------------------------
        # FAST PATH: If ticket list & statuses have not changed,
        # ONLY update the timer labels in-place. ZERO widget demolition!
        # -------------------------------------------------------------
        if is_periodic and current_signature == self._rendered_signature:
            for o in filtered_tickets:
                oid = o["id"]
                if oid in self._card_timer_labels:
                    lbl, _ = self._card_timer_labels[oid]
                    if lbl.winfo_exists():
                        elapsed = float(o["elapsed_mins"] or 0.0)
                        is_priority = elapsed > 15.0
                        time_text = f"⏱️ {int(elapsed)}m ago" if elapsed >= 1.0 else "⏱️ Just now"
                        if is_priority:
                            time_text += " ⚠️ HIGH WAIT"
                        timer_color = "#EF4444" if is_priority else palette["text_secondary"]
                        lbl.configure(text=time_text, text_color=timer_color)
            return

        # -------------------------------------------------------------
        # STRUCTURAL RECONSTRUCTION PATH (New order, status change, filter change)
        # Preserve scroll position across the update!
        # -------------------------------------------------------------
        scroll_y = 0.0
        try:
            if hasattr(self.tickets_scroll, "_parent_canvas"):
                scroll_y = self.tickets_scroll._parent_canvas.yview()[0]
        except Exception:
            scroll_y = 0.0

        # Clear scrollable frame widgets cleanly
        for w in self.tickets_scroll.winfo_children():
            w.destroy()

        self._rendered_signature = current_signature
        self._card_timer_labels.clear()

        if not filtered_tickets:
            empty = ctk.CTkFrame(self.tickets_scroll, fg_color=palette["bg_card"], corner_radius=10, border_width=1, border_color=palette["border"])
            empty.pack(fill="x", padx=10, pady=40)
            ctk.CTkLabel(
                empty,
                text="🎉 All kitchen tickets cleared! No active orders in this queue.",
                font=ctk.CTkFont(size=13, weight="bold"),
                text_color=palette["success"]
            ).pack(padx=20, pady=30)
            return

        # 3-column ticket grid
        grid_frame = ctk.CTkFrame(self.tickets_scroll, fg_color="transparent")
        grid_frame.pack(fill="both", expand=True)
        grid_frame.grid_columnconfigure((0, 1, 2), weight=1, uniform="kds_grid")

        for idx, o in enumerate(filtered_tickets):
            row_idx = idx // 3
            col_idx = idx % 3

            oid = o["id"]
            st = o["status"]
            onum = o["order_number"]
            tbl = o["table_number"] or "Takeaway"
            cust = o["customer_name"] or "Guest"
            server = o["server_name"] or "Customer App"
            created = o["created_at"] or ""
            special_notes = (o["special_instructions"] if "special_instructions" in o.keys() else "").strip()
            elapsed = float(o["elapsed_mins"] or 0.0)

            # High priority / long wait alert (>15 minutes)
            is_priority = elapsed > 15.0
            border_color = "#EF4444" if is_priority else palette["border"]

            card = ctk.CTkFrame(
                grid_frame,
                fg_color=palette["bg_card"],
                corner_radius=10,
                border_width=2 if is_priority else 1,
                border_color=border_color
            )
            card.grid(row=row_idx, column=col_idx, sticky="nsew", padx=6, pady=6)

            # Ticket Header: Order # + Table
            c_header = ctk.CTkFrame(card, fg_color="transparent")
            c_header.pack(fill="x", padx=12, pady=(10, 4))

            ctk.CTkLabel(
                c_header,
                text=f"{onum}  •  {tbl}",
                font=ctk.CTkFont(size=13, weight="bold"),
                text_color=palette.get("heading", palette["text_primary"])
            ).pack(side="left")

            # Status Pill
            st_colors = {
                "PENDING": ("#DBEAFE", "#1D4ED8"),
                "NEW": ("#DBEAFE", "#1D4ED8"),
                "RECEIVED": ("#DBEAFE", "#1D4ED8"),
                "PENDING_ACCEPTANCE": ("#DBEAFE", "#1D4ED8"),
                "ACCEPTED": ("#EDE9FE", "#6D28D9"),
                "PREPARING": ("#FEF3C7", "#B45309"),
                "READY": ("#DCFCE7", "#15803D")
            }
            s_bg, s_fg = st_colors.get(st, ("#F1F5F9", "#475569"))
            pill = ctk.CTkFrame(c_header, fg_color=s_bg, corner_radius=6)
            pill.pack(side="right")
            ctk.CTkLabel(pill, text=st, font=ctk.CTkFont(size=9, weight="bold"), text_color=s_fg).pack(padx=6, pady=2)

            # Metadata Row (Timer & Guest)
            meta_box = ctk.CTkFrame(card, fg_color="transparent")
            meta_box.pack(fill="x", padx=12, pady=(0, 6))

            time_text = f"⏱️ {int(elapsed)}m ago" if elapsed >= 1.0 else "⏱️ Just now"
            if is_priority:
                time_text += " ⚠️ HIGH WAIT"
            timer_color = "#EF4444" if is_priority else palette["text_secondary"]
            lbl_timer = ctk.CTkLabel(meta_box, text=time_text, font=ctk.CTkFont(size=10, weight="bold"), text_color=timer_color)
            lbl_timer.pack(side="left")
            self._card_timer_labels[oid] = (lbl_timer, elapsed)

            ctk.CTkLabel(meta_box, text=f"Guest: {cust}", font=ctk.CTkFont(size=10), text_color=palette["text_secondary"]).pack(side="right")

            # Special Kitchen Instructions Banner (if customer requested)
            if special_notes:
                note_box = ctk.CTkFrame(card, fg_color=palette["bg_secondary"], corner_radius=6, border_width=1, border_color="#F59E0B")
                note_box.pack(fill="x", padx=12, pady=(0, 6))
                ctk.CTkLabel(
                    note_box,
                    text=f"📝 Note: {special_notes}",
                    font=ctk.CTkFont(size=10, weight="bold"),
                    text_color="#F59E0B",
                    wraplength=240,
                    justify="left"
                ).pack(padx=8, pady=4, anchor="w")

            # Dish Items Checklist Box
            items_box = ctk.CTkFrame(card, fg_color=palette["bg_secondary"], corner_radius=6)
            items_box.pack(fill="x", padx=12, pady=(0, 8))

            items = self.order_repo.get_order_items(oid)
            for it in items:
                it_row = ctk.CTkFrame(items_box, fg_color="transparent")
                it_row.pack(fill="x", padx=8, pady=2)
                ctk.CTkLabel(
                    it_row,
                    text=f"▫ {it.quantity}x  {it.item_name}",
                    font=ctk.CTkFont(size=11, weight="bold"),
                    text_color=palette["text_primary"]
                ).pack(side="left")

            # Action Progression Buttons Row
            btn_row = ctk.CTkFrame(card, fg_color="transparent")
            btn_row.pack(fill="x", padx=12, pady=(0, 10))

            if st in ("PENDING", "NEW", "RECEIVED", "PENDING_ACCEPTANCE"):
                ctk.CTkButton(
                    btn_row,
                    text="👍 Accept KOT",
                    font=ctk.CTkFont(size=11, weight="bold"),
                    height=28,
                    fg_color="#3B82F6",
                    hover_color="#2563EB",
                    command=lambda i=oid: self._transition_status(i, "ACCEPTED")
                ).pack(fill="x")
            elif st == "ACCEPTED":
                ctk.CTkButton(
                    btn_row,
                    text="🔥 Start Preparing",
                    font=ctk.CTkFont(size=11, weight="bold"),
                    height=28,
                    fg_color="#F59E0B",
                    hover_color="#D97706",
                    command=lambda i=oid: self._transition_status(i, "PREPARING")
                ).pack(fill="x")
            elif st == "PREPARING":
                ctk.CTkButton(
                    btn_row,
                    text="🔔 Mark Ready for Pass",
                    font=ctk.CTkFont(size=11, weight="bold"),
                    height=28,
                    fg_color="#10B981",
                    hover_color="#059669",
                    command=lambda i=oid: self._transition_status(i, "READY")
                ).pack(fill="x")
            elif st == "READY":
                ctk.CTkLabel(
                    btn_row,
                    text="✓ Dish at Server Pass (Waiting Billing/Delivery)",
                    font=ctk.CTkFont(size=10, weight="bold"),
                    text_color="#10B981"
                ).pack(anchor="center", pady=4)

        # Restore scroll position if previously scrolled
        try:
            if hasattr(self.tickets_scroll, "_parent_canvas") and scroll_y > 0.0:
                self.tickets_scroll._parent_canvas.yview_moveto(scroll_y)
        except Exception:
            pass

    def _transition_status(self, order_id: int, target_status: str):
        """Transitions order status through KDS lifecycle and records audit trail."""
        try:
            self.order_repo.db.execute("UPDATE orders SET status = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?;", (target_status, order_id))
            self.order_repo.db.execute(
                """INSERT INTO audit_logs (username, action, module, details)
                   VALUES ('chef1', ?, 'CHEF_KDS', ?);""",
                (f"SET_STATUS_{target_status}", f"KDS transitioned Order #{order_id} to {target_status}")
            )
            # Invalidate signature to trigger immediate update and show new status
            self._rendered_signature = ()
            self._refresh_kds_data(is_periodic=False)
        except Exception as e:
            logger.error(f"Error transitioning order #{order_id} to {target_status}: {e}")
