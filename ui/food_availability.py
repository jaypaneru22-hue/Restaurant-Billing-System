"""Food Availability & 86 List Floor Management View."""
from typing import Optional
import customtkinter as ctk

from ui.theme_manager import theme_manager
from database.db import db
from repositories.menu_repository import MenuRepository
from utils.logger import logger


class FoodAvailabilityFrame(ctk.CTkFrame):
    """Floor manager interface for 86 list tracking, kitchen stockouts, and 1-click menu availability toggle."""

    def __init__(self, master, **kwargs):
        super().__init__(master, **kwargs)
        self.menu_repo = MenuRepository(db)
        self.search_term = ""
        self.selected_category = "ALL"
        self.only_86 = False

        theme_manager.subscribe(self.on_theme_changed)
        self._build_ui()
        self._load_items()

    def destroy(self):
        theme_manager.unsubscribe(self.on_theme_changed)
        super().destroy()

    def on_theme_changed(self, _theme: str):
        if self.winfo_exists():
            palette = theme_manager.get_palette()
            self.configure(fg_color=palette["bg_primary"])
            self._load_items()

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
            text="🚫 Food Availability & Kitchen 86 List",
            font=ctk.CTkFont(size=20, weight="bold"),
            text_color=palette.get("heading", palette["text_primary"])
        ).pack(anchor="w")

        ctk.CTkLabel(
            title_box,
            text="Prevent ordering errors: immediately 86 out-of-stock items or restore dishes once replenished.",
            font=ctk.CTkFont(size=11),
            text_color=palette["text_secondary"]
        ).pack(anchor="w", pady=(2, 0))

        # KPI Summary Cards
        self.kpi_container = ctk.CTkFrame(self, fg_color="transparent")
        self.kpi_container.pack(fill="x", padx=20, pady=(0, 10))

        # Filter & Search Controls Bar
        ctrl_bar = ctk.CTkFrame(self, fg_color=palette["bg_card"], corner_radius=10, border_width=1, border_color=palette["border"])
        ctrl_bar.pack(fill="x", padx=20, pady=(0, 10))

        inner_ctrl = ctk.CTkFrame(ctrl_bar, fg_color="transparent")
        inner_ctrl.pack(fill="x", padx=12, pady=10)

        # Search Entry
        self.search_var = ctk.StringVar()
        self.search_var.trace_add("write", lambda *_: self._on_search_change())
        search_entry = ctk.CTkEntry(
            inner_ctrl,
            textvariable=self.search_var,
            placeholder_text="🔍 Search dish name or category...",
            width=260,
            height=32,
            border_color=palette["border"]
        )
        search_entry.pack(side="left", padx=(0, 10))

        # Category Dropdown
        self.cat_var = ctk.StringVar(value="ALL Categories")
        cat_options = ["ALL Categories", "Starter", "Main Course", "Beverage", "Dessert"]
        cat_menu = ctk.CTkOptionMenu(
            inner_ctrl,
            variable=self.cat_var,
            values=cat_options,
            width=150,
            height=32,
            fg_color=palette["bg_secondary"],
            text_color=palette["text_primary"],
            button_color=palette["accent"],
            command=self._on_category_select
        )
        cat_menu.pack(side="left", padx=(0, 10))

        # Only 86 Toggle
        self.only_86_switch = ctk.CTkSwitch(
            inner_ctrl,
            text="Show 86'd / Unavailable Only",
            font=ctk.CTkFont(size=11, weight="bold"),
            command=self._on_toggle_86_filter
        )
        self.only_86_switch.pack(side="right")

        # Table Container
        self.table_scroll = ctk.CTkScrollableFrame(
            self,
            fg_color="transparent",
            scrollbar_button_color=palette.get("sidebar_hover", "#245A9B")
        )
        self.table_scroll.pack(fill="both", expand=True, padx=20, pady=(0, 15))

    def _on_search_change(self):
        self.search_term = self.search_var.get().strip().lower()
        self._render_table()

    def _on_category_select(self, val: str):
        if val == "ALL Categories":
            self.selected_category = "ALL"
        else:
            self.selected_category = val
        self._render_table()

    def _on_toggle_86_filter(self):
        self.only_86 = bool(self.only_86_switch.get())
        self._render_table()

    def _load_items(self):
        try:
            items = self.menu_repo.list_all(available_only=False)
        except Exception as e:
            logger.error(f"Error fetching menu items for 86 list: {e}")
            items = []

        self.all_items = items
        total_cnt = len(items)
        available_cnt = len([it for it in items if it.is_available])
        out_cnt = total_cnt - available_cnt
        avail_rate = (available_cnt / total_cnt * 100) if total_cnt > 0 else 0.0

        palette = theme_manager.get_palette()
        for w in self.kpi_container.winfo_children():
            w.destroy()

        kpis = [
            ("Total Catalog Items", str(total_cnt), "🍽️", "#3B82F6"),
            ("Active & Serving", str(available_cnt), "✅", "#10B981"),
            ("86'd / Out of Stock", str(out_cnt), "🚫", "#EF4444"),
            ("Catalog Availability", f"{avail_rate:.1f}%", "📊", "#8B5CF6")
        ]

        for title, val, icon, _acc in kpis:
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

        self._render_table()

    def _render_table(self):
        palette = theme_manager.get_palette()
        for w in self.table_scroll.winfo_children():
            w.destroy()

        # Filter items
        filtered = []
        for it in self.all_items:
            if self.search_term:
                if (self.search_term not in it.name.lower()) and (self.search_term not in it.category.lower()):
                    continue
            if self.selected_category != "ALL" and it.category != self.selected_category:
                continue
            if self.only_86 and it.is_available:
                continue
            filtered.append(it)

        # Table Header
        tbl_head = ctk.CTkFrame(self.table_scroll, fg_color=palette["bg_secondary"], corner_radius=6, height=36)
        tbl_head.pack(fill="x", padx=6, pady=(0, 4))
        tbl_head.pack_propagate(False)

        cols = [
            ("ID", 50, "w"),
            ("Dish Name", 280, "w"),
            ("Category", 140, "w"),
            ("Unit Price", 100, "e"),
            ("Kitchen Status", 150, "center"),
            ("1-Click Floor Action", 140, "center")
        ]
        for cname, cwidth, calign in cols:
            ctk.CTkLabel(
                tbl_head,
                text=cname,
                font=ctk.CTkFont(size=11, weight="bold"),
                text_color=palette["text_secondary"],
                width=cwidth,
                anchor=calign
            ).pack(side="left", padx=8)

        if not filtered:
            empty = ctk.CTkFrame(self.table_scroll, fg_color=palette["bg_card"], corner_radius=8, border_width=1, border_color=palette["border"])
            empty.pack(fill="x", padx=6, pady=20)
            ctk.CTkLabel(empty, text="No menu items matched your search criteria.", font=ctk.CTkFont(size=12), text_color=palette["text_secondary"]).pack(padx=20, pady=20)
            return

        for it in filtered:
            row = ctk.CTkFrame(self.table_scroll, fg_color=palette["bg_card"], corner_radius=6, border_width=1, border_color=palette["border"], height=44)
            row.pack(fill="x", padx=6, pady=2)
            row.pack_propagate(False)

            # ID
            ctk.CTkLabel(row, text=f"#{it.id}", font=ctk.CTkFont(size=11), text_color=palette["text_secondary"], width=50, anchor="w").pack(side="left", padx=8)

            # Name
            ctk.CTkLabel(row, text=it.name, font=ctk.CTkFont(size=12, weight="bold"), text_color=palette["text_primary"], width=280, anchor="w").pack(side="left", padx=8)

            # Category Pill
            cat_pill = ctk.CTkFrame(row, fg_color=palette["bg_secondary"], corner_radius=4, width=140, height=24)
            cat_pill.pack(side="left", padx=8)
            cat_pill.pack_propagate(False)
            ctk.CTkLabel(cat_pill, text=it.category, font=ctk.CTkFont(size=10, weight="bold"), text_color=palette["accent"]).pack(expand=True)

            # Unit Price
            ctk.CTkLabel(row, text=f"₹{float(it.price):,.2f}", font=ctk.CTkFont(size=11, weight="bold"), text_color=palette["text_primary"], width=100, anchor="e").pack(side="left", padx=8)

            # Status Pill
            st_box = ctk.CTkFrame(row, fg_color="transparent", width=150)
            st_box.pack(side="left", padx=8)
            st_box.pack_propagate(False)

            if it.is_available:
                pill = ctk.CTkFrame(st_box, fg_color="#DCFCE7", corner_radius=6)
                pill.pack(expand=True)
                ctk.CTkLabel(pill, text="● IN STOCK / AVAILABLE", font=ctk.CTkFont(size=9, weight="bold"), text_color="#15803D").pack(padx=8, pady=2)
            else:
                pill = ctk.CTkFrame(st_box, fg_color="#FEE2E2", corner_radius=6)
                pill.pack(expand=True)
                ctk.CTkLabel(pill, text="🚫 86'd / OUT OF STOCK", font=ctk.CTkFont(size=9, weight="bold"), text_color="#B91C1C").pack(padx=8, pady=2)

            # 1-Click Action Button
            act_box = ctk.CTkFrame(row, fg_color="transparent", width=140)
            act_box.pack(side="left", padx=8)
            act_box.pack_propagate(False)

            if it.is_available:
                ctk.CTkButton(
                    act_box,
                    text="🚫 86 This Item",
                    font=ctk.CTkFont(size=10, weight="bold"),
                    height=26,
                    width=120,
                    fg_color="#EF4444",
                    hover_color="#DC2626",
                    command=lambda i=it.id: self._toggle_item_stock(i, False)
                ).pack(expand=True)
            else:
                ctk.CTkButton(
                    act_box,
                    text="✅ Restore Stock",
                    font=ctk.CTkFont(size=10, weight="bold"),
                    height=26,
                    width=120,
                    fg_color="#10B981",
                    hover_color="#059669",
                    command=lambda i=it.id: self._toggle_item_stock(i, True)
                ).pack(expand=True)

    def _toggle_item_stock(self, item_id: int, target_available: bool):
        val = 1 if target_available else 0
        try:
            db.execute("UPDATE menu_items SET is_available = ? WHERE id = ?;", (val, item_id))
            action_desc = "RESTORED_STOCK" if target_available else "MARKED_86_OUT_OF_STOCK"
            db.execute(
                """INSERT INTO audit_logs (username, action, module, details)
                   VALUES ('Manager', ?, 'MENU_AVAILABILITY', ?);""",
                (action_desc, f"Menu item #{item_id} availability changed to {target_available}")
            )
            self._load_items()
        except Exception as e:
            logger.error(f"Error toggling menu item #{item_id} stock: {e}")
