"""Restaurant Table & Floor Layout Management Module (Phase E)."""
from typing import Optional, Callable, Dict, List
import customtkinter as ctk

from ui.theme_manager import theme_manager
from database.db import db
from utils.window_utils import center_dialog
from utils.logger import logger


class TableActionDialog(ctk.CTkToplevel):
    """Modal dialog allowing Manager or Floor Host to update table occupancy, assign reservations, or transfer tables."""

    def __init__(self, master, table_data: dict, on_saved: Callable, **kwargs):
        super().__init__(master, **kwargs)
        self.table = table_data
        self.on_saved = on_saved

        self.title(f"Manage Table {self.table['table_number']}")
        self.resizable(False, False)
        center_dialog(self, master, target_width=440, target_height=380, min_width=420, min_height=360)
        self.grab_set()

        self._build_ui()

    def _build_ui(self):
        palette = theme_manager.get_palette()
        self.configure(fg_color=palette["bg_primary"])

        ctk.CTkLabel(
            self,
            text=f"🪑 Table {self.table['table_number']} Operations",
            font=ctk.CTkFont(size=17, weight="bold"),
            text_color=palette.get("heading", palette["text_primary"])
        ).pack(padx=20, pady=(15, 2), anchor="w")

        ctk.CTkLabel(
            self,
            text=f"Zone: {self.table['zone']}  •  Capacity: {self.table['capacity']} Guests",
            font=ctk.CTkFont(size=11),
            text_color=palette["text_secondary"]
        ).pack(padx=20, pady=(0, 10), anchor="w")

        form = ctk.CTkFrame(self, fg_color=palette["bg_card"], corner_radius=10, border_width=1, border_color=palette["border"])
        form.pack(fill="both", expand=True, padx=20, pady=(0, 12))

        # Status Selector
        ctk.CTkLabel(form, text="Table Occupancy Status:", font=ctk.CTkFont(size=11, weight="bold"), text_color=palette["text_primary"]).pack(anchor="w", padx=14, pady=(12, 2))
        self.status_var = ctk.StringVar(value=self.table["status"])
        status_menu = ctk.CTkOptionMenu(
            form,
            variable=self.status_var,
            values=["VACANT", "OCCUPIED", "RESERVED", "BILL_REQUESTED", "CLEANING"],
            height=32,
            fg_color=palette["bg_secondary"],
            text_color=palette["text_primary"],
            button_color=palette["accent"]
        )
        status_menu.pack(fill="x", padx=14, pady=(0, 10))

        # Capacity edit
        ctk.CTkLabel(form, text="Seating Capacity:", font=ctk.CTkFont(size=11, weight="bold"), text_color=palette["text_primary"]).pack(anchor="w", padx=14, pady=(0, 2))
        self.entry_cap = ctk.CTkEntry(form, height=30, border_color=palette["border"])
        self.entry_cap.insert(0, str(self.table["capacity"]))
        self.entry_cap.pack(fill="x", padx=14, pady=(0, 10))

        # Error notification strip
        self.lbl_error = ctk.CTkLabel(form, text="", font=ctk.CTkFont(size=11, weight="bold"), text_color=palette["danger"], wraplength=380)
        self.lbl_error.pack(fill="x", padx=14, pady=(0, 4))

        # Button row
        btn_row = ctk.CTkFrame(self, fg_color="transparent")
        btn_row.pack(fill="x", padx=20, pady=(0, 14))

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
            text="💾 Save Changes",
            width=130,
            height=32,
            font=ctk.CTkFont(size=11, weight="bold"),
            fg_color=palette["accent"],
            hover_color=palette["accent_hover"],
            command=self._handle_save
        ).pack(side="right")

    def _handle_save(self):
        new_status = self.status_var.get()
        new_cap_str = self.entry_cap.get().strip()

        try:
            new_cap = int(new_cap_str)
            if new_cap < 1:
                raise ValueError
        except Exception:
            self.lbl_error.configure(text="Please enter a valid positive seating capacity.")
            return

        # Poka-Yoke Guard: Cannot mark VACANT if there is an active unsettled order on this table!
        if new_status == "VACANT":
            active_orders = db.fetchall(
                "SELECT id, order_number FROM orders WHERE table_number = ? AND status IN ('PENDING', 'ACCEPTED', 'PREPARING', 'READY');",
                (self.table["table_number"],)
            )
            if active_orders:
                self.lbl_error.configure(text=f"Cannot vacate table: Active Order #{active_orders[0]['order_number']} is still unsettled!")
                return

        try:
            db.execute(
                """UPDATE restaurant_tables
                   SET status = ?, capacity = ?, updated_at = CURRENT_TIMESTAMP
                   WHERE id = ?;""",
                (new_status, new_cap, self.table["id"])
            )
            db.execute(
                """INSERT INTO audit_logs (username, action, module, details)
                   VALUES ('FloorManager', 'UPDATE_TABLE_STATUS', 'TABLES', ?);""",
                (f"Table {self.table['table_number']} status updated to {new_status} (Cap: {new_cap})",)
            )
            self.on_saved()
            self.destroy()
        except Exception as e:
            self.lbl_error.configure(text=f"Database error: {e}")


class TableManagementFrame(ctk.CTkFrame):
    """Interactive restaurant floor layout with real-time occupancy and active order linking."""

    def __init__(self, master, on_open_order: Optional[Callable[[str], None]] = None, on_table_selected: Optional[Callable[[str], None]] = None, **kwargs):
        super().__init__(master, **kwargs)
        self.on_open_order = on_open_order or on_table_selected
        self.selected_zone = "ALL"

        theme_manager.subscribe(self.on_theme_changed)
        self._build_ui()
        self._load_tables()

    def destroy(self):
        theme_manager.unsubscribe(self.on_theme_changed)
        super().destroy()

    def on_theme_changed(self, _theme: str):
        if self.winfo_exists():
            palette = theme_manager.get_palette()
            self.configure(fg_color=palette["bg_primary"])
            self._load_tables()

    def _build_ui(self):
        palette = theme_manager.get_palette()
        self.configure(fg_color=palette["bg_primary"])

        # Header
        header = ctk.CTkFrame(self, fg_color="transparent")
        header.pack(fill="x", padx=20, pady=(15, 8))

        title_box = ctk.CTkFrame(header, fg_color="transparent")
        title_box.pack(side="left")

        ctk.CTkLabel(
            title_box,
            text="🪑 Table & Floor Management",
            font=ctk.CTkFont(size=20, weight="bold"),
            text_color=palette.get("heading", palette["text_primary"])
        ).pack(anchor="w")

        ctk.CTkLabel(
            title_box,
            text="Live floor plan, zone occupancy tracking, reservations, and active dining bill association.",
            font=ctk.CTkFont(size=11),
            text_color=palette["text_secondary"]
        ).pack(anchor="w", pady=(2, 0))

        # Controls
        ctk.CTkButton(
            header,
            text="🔄 Refresh Floor",
            font=ctk.CTkFont(size=11, weight="bold"),
            fg_color=palette["accent"],
            hover_color=palette["accent_hover"],
            height=32,
            width=120,
            command=self._load_tables
        ).pack(side="right")

        # Floor KPI cards
        self.kpi_container = ctk.CTkFrame(self, fg_color="transparent")
        self.kpi_container.pack(fill="x", padx=20, pady=(0, 10))

        # Zone filter tabs
        filter_bar = ctk.CTkFrame(self, fg_color=palette["bg_card"], corner_radius=10, border_width=1, border_color=palette["border"])
        filter_bar.pack(fill="x", padx=20, pady=(0, 10))

        f_inner = ctk.CTkFrame(filter_bar, fg_color="transparent")
        f_inner.pack(fill="x", padx=10, pady=8)

        ctk.CTkLabel(f_inner, text="Floor Zones:", font=ctk.CTkFont(size=11, weight="bold"), text_color=palette["text_secondary"]).pack(side="left", padx=(4, 10))

        self.zone_buttons = {}
        zones = ["ALL", "Main Dining", "Patio Garden", "Family Section", "Counter / Bar"]
        for z in zones:
            btn = ctk.CTkButton(
                f_inner,
                text=z if z != "ALL" else "🏢 All Zones",
                font=ctk.CTkFont(size=10, weight="bold"),
                height=28,
                fg_color=palette["accent"] if z == self.selected_zone else palette["bg_secondary"],
                text_color="#FFFFFF" if z == self.selected_zone else palette["text_primary"],
                hover_color=palette["accent_hover"],
                command=lambda z_val=z: self._select_zone(z_val)
            )
            btn.pack(side="left", padx=3)
            self.zone_buttons[z] = btn

        # Tables scroll
        self.tables_scroll = ctk.CTkScrollableFrame(
            self,
            fg_color="transparent",
            scrollbar_button_color=palette.get("sidebar_hover", "#292938")
        )
        self.tables_scroll.pack(fill="both", expand=True, padx=20, pady=(0, 15))

    def _select_zone(self, zone_name: str):
        self.selected_zone = zone_name
        palette = theme_manager.get_palette()
        for z, btn in self.zone_buttons.items():
            if z == zone_name:
                btn.configure(fg_color=palette["accent"], text_color="#FFFFFF")
            else:
                btn.configure(fg_color=palette["bg_secondary"], text_color=palette["text_primary"])
        self._load_tables()

    def _load_tables(self):
        palette = theme_manager.get_palette()

        try:
            sql = "SELECT id, table_number, zone, capacity, status, active_order_id, updated_at FROM restaurant_tables ORDER BY zone, table_number;"
            all_tables = db.fetchall(sql)
        except Exception as e:
            logger.error(f"Error querying restaurant_tables: {e}")
            all_tables = []

        total_cnt = len(all_tables)
        occupied_cnt = len([t for t in all_tables if t["status"] == "OCCUPIED"])
        vacant_cnt = len([t for t in all_tables if t["status"] == "VACANT"])
        reserved_cnt = len([t for t in all_tables if t["status"] == "RESERVED"])
        occupancy_rate = (occupied_cnt / total_cnt * 100) if total_cnt > 0 else 0.0

        # Update KPIs
        for w in self.kpi_container.winfo_children():
            w.destroy()

        kpis = [
            ("Total Tables", f"{total_cnt} Units", "🪑", palette["accent"]),
            ("Occupied (Dining)", f"{occupied_cnt} Tables", "👥", "#EF4444"),
            ("Vacant & Available", f"{vacant_cnt} Tables", "✅", "#10B981"),
            ("Occupancy Rate", f"{occupancy_rate:.1f}%", "📊", "#3B82F6")
        ]

        for title, val, icon, color in kpis:
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
            ctk.CTkLabel(left, text=val, font=ctk.CTkFont(size=16, weight="bold"), text_color=color).pack(anchor="w")

            ctk.CTkLabel(inner, text=icon, font=ctk.CTkFont(size=20)).pack(side="right")

        # Filter by zone
        if self.selected_zone == "ALL":
            tables_to_show = all_tables
        else:
            tables_to_show = [t for t in all_tables if t["zone"] == self.selected_zone]

        for w in self.tables_scroll.winfo_children():
            w.destroy()

        # Render Table Cards Grid (4 columns)
        grid = ctk.CTkFrame(self.tables_scroll, fg_color="transparent")
        grid.pack(fill="both", expand=True)
        grid.grid_columnconfigure((0, 1, 2, 3), weight=1, uniform="tbl_col")

        status_palettes = {
            "VACANT": ("#DCFCE7", "#15803D", "✅ Available"),
            "OCCUPIED": ("#FEE2E2", "#B91C1C", "👥 Dining"),
            "RESERVED": ("#FEF3C7", "#B45309", "📅 Reserved"),
            "BILL_REQUESTED": ("#EDE9FE", "#6D28D9", "💳 Bill Due"),
            "CLEANING": ("#E0F2FE", "#0369A1", "🧹 Cleaning")
        }

        for idx, t in enumerate(tables_to_show):
            row_idx = idx // 4
            col_idx = idx % 4

            st = t["status"]
            s_bg, s_fg, s_label = status_palettes.get(st, ("#F1F5F9", "#475569", st))

            card = ctk.CTkFrame(
                grid,
                fg_color=palette["bg_card"],
                corner_radius=10,
                border_width=1,
                border_color=palette["border"]
            )
            card.grid(row=row_idx, column=col_idx, sticky="nsew", padx=6, pady=6)

            # Header inside card
            c_head = ctk.CTkFrame(card, fg_color="transparent")
            c_head.pack(fill="x", padx=12, pady=(10, 4))

            ctk.CTkLabel(
                c_head,
                text=t["table_number"],
                font=ctk.CTkFont(size=15, weight="bold"),
                text_color=palette.get("heading", palette["text_primary"])
            ).pack(side="left")

            pill = ctk.CTkFrame(c_head, fg_color=s_bg, corner_radius=6)
            pill.pack(side="right")
            ctk.CTkLabel(pill, text=s_label, font=ctk.CTkFont(size=9, weight="bold"), text_color=s_fg).pack(padx=6, pady=2)

            # Metadata
            ctk.CTkLabel(
                card,
                text=f"Zone: {t['zone']}  •  Cap: {t['capacity']} Pax",
                font=ctk.CTkFont(size=10),
                text_color=palette["text_secondary"]
            ).pack(anchor="w", padx=12, pady=(0, 6))

            # Query active order for this table if any
            active_order = db.fetchone(
                "SELECT id, order_number, customer_name, status FROM orders WHERE table_number = ? AND status IN ('PENDING', 'ACCEPTED', 'PREPARING', 'READY');",
                (t["table_number"],)
            )

            ord_box = ctk.CTkFrame(card, fg_color=palette["bg_secondary"], corner_radius=6)
            ord_box.pack(fill="x", padx=12, pady=(0, 8))

            if active_order:
                ctk.CTkLabel(
                    ord_box,
                    text=f"Ticket: #{active_order['order_number']}",
                    font=ctk.CTkFont(size=10, weight="bold"),
                    text_color=palette["text_primary"]
                ).pack(anchor="w", padx=8, pady=(4, 0))
                ctk.CTkLabel(
                    ord_box,
                    text=f"Guest: {active_order['customer_name']} ({active_order['status']})",
                    font=ctk.CTkFont(size=9),
                    text_color=palette["accent"]
                ).pack(anchor="w", padx=8, pady=(0, 4))
            else:
                ctk.CTkLabel(
                    ord_box,
                    text="No Active Order",
                    font=ctk.CTkFont(size=10),
                    text_color=palette["text_secondary"]
                ).pack(anchor="w", padx=8, pady=4)

            # Action button
            ctk.CTkButton(
                card,
                text="⚙️ Table Actions",
                font=ctk.CTkFont(size=10, weight="bold"),
                height=28,
                fg_color=palette["bg_secondary"],
                hover_color=palette["border"],
                text_color=palette["text_primary"],
                command=lambda tbl_dict=dict(t): TableActionDialog(self, table_data=tbl_dict, on_saved=self._load_tables)
            ).pack(fill="x", padx=12, pady=(0, 10))
