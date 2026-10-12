"""Menu Catalog Management view supporting CRUD, search, and category filtering."""
import customtkinter as ctk
from decimal import Decimal
from typing import Optional
from services.menu_service import MenuService, menu_service
from ui.theme_manager import theme_manager
from config.settings import DEFAULT_CATEGORIES, CURRENCY_SYMBOL


class MenuDialog(ctk.CTkToplevel):
    """Modal dialog for creating and editing menu items."""

    def __init__(self, master, on_save_cb, item=None, **kwargs):
        super().__init__(master, **kwargs)
        self.on_save_cb = on_save_cb
        self.item = item

        self.title("Edit Menu Item" if item else "Add New Menu Item")
        self.geometry("450x420")
        self.resizable(False, False)
        self.grab_set()

        self._build_ui()

    def _build_ui(self):
        palette = theme_manager.get_palette()
        self.configure(fg_color=palette["bg_primary"])

        title_text = "✏️ Edit Menu Item" if self.item else "➕ Add New Menu Item"
        ctk.CTkLabel(
            self,
            text=title_text,
            font=ctk.CTkFont(size=18, weight="bold"),
            text_color=palette["text_primary"]
        ).pack(padx=25, pady=(20, 15), anchor="w")

        form = ctk.CTkFrame(self, fg_color=palette["bg_card"], corner_radius=10, border_width=1, border_color=palette["border"])
        form.pack(fill="both", expand=True, padx=25, pady=(0, 15))

        # Item Name
        ctk.CTkLabel(form, text="Item Name *", font=ctk.CTkFont(size=12, weight="bold"), text_color=palette["text_primary"]).pack(anchor="w", padx=20, pady=(15, 2))
        self.entry_name = ctk.CTkEntry(form, height=34, font=ctk.CTkFont(size=13))
        self.entry_name.pack(fill="x", padx=20, pady=(0, 10))
        if self.item:
            self.entry_name.insert(0, self.item.name)

        # Category
        ctk.CTkLabel(form, text="Category *", font=ctk.CTkFont(size=12, weight="bold"), text_color=palette["text_primary"]).pack(anchor="w", padx=20, pady=(0, 2))
        self.combo_cat = ctk.CTkComboBox(form, values=DEFAULT_CATEGORIES, height=34)
        self.combo_cat.pack(fill="x", padx=20, pady=(0, 10))
        if self.item:
            self.combo_cat.set(self.item.category)
        else:
            self.combo_cat.set(DEFAULT_CATEGORIES[0])

        # Price
        ctk.CTkLabel(form, text=f"Price ({CURRENCY_SYMBOL}) *", font=ctk.CTkFont(size=12, weight="bold"), text_color=palette["text_primary"]).pack(anchor="w", padx=20, pady=(0, 2))
        self.entry_price = ctk.CTkEntry(form, height=34, font=ctk.CTkFont(size=13))
        self.entry_price.pack(fill="x", padx=20, pady=(0, 10))
        if self.item:
            self.entry_price.insert(0, str(self.item.price))

        # Availability Switch
        self.switch_avail = ctk.CTkSwitch(form, text="Available for Order", font=ctk.CTkFont(size=12))
        self.switch_avail.pack(anchor="w", padx=20, pady=(0, 10))
        if self.item and not self.item.is_available:
            self.switch_avail.deselect()
        else:
            self.switch_avail.select()

        # Error label
        self.lbl_error = ctk.CTkLabel(form, text="", font=ctk.CTkFont(size=11), text_color=palette["danger"])
        self.lbl_error.pack(fill="x", padx=20, pady=(0, 5))

        # Buttons
        btn_box = ctk.CTkFrame(self, fg_color="transparent")
        btn_box.pack(fill="x", padx=25, pady=(0, 20))

        cancel_btn = ctk.CTkButton(
            btn_box,
            text="Cancel",
            width=90,
            height=34,
            fg_color=palette["bg_card"],
            text_color=palette["text_primary"],
            hover_color=palette["bg_secondary"],
            command=self.destroy
        )
        cancel_btn.pack(side="right", padx=(10, 0))

        save_btn = ctk.CTkButton(
            btn_box,
            text="Save Item",
            width=110,
            height=34,
            fg_color=palette["accent"],
            hover_color=palette["accent_hover"],
            command=self._handle_save
        )
        save_btn.pack(side="right")

    def _handle_save(self):
        name = self.entry_name.get().strip()
        cat = self.combo_cat.get().strip()
        price_str = self.entry_price.get().strip()
        avail = bool(self.switch_avail.get())

        success, msg = self.on_save_cb(self.item.id if self.item else None, name, cat, price_str, avail)
        if success:
            self.destroy()
        else:
            self.lbl_error.configure(text=msg)


class MenuFrame(ctk.CTkFrame):
    """Menu Catalog Management view."""

    def __init__(self, master, menu_svc: MenuService = menu_service, **kwargs):
        super().__init__(master, **kwargs)
        self.menu_svc = menu_svc

        theme_manager.subscribe(self.on_theme_changed)
        self._build_ui()
        self.refresh_items()

    def on_theme_changed(self, theme_name: str):
        if self.winfo_exists():
            palette = theme_manager.get_palette()
            self.configure(fg_color=palette["bg_primary"])
            self.refresh_items()

    def _build_ui(self):
        palette = theme_manager.get_palette()
        self.configure(fg_color=palette["bg_primary"])

        # Header Bar
        header = ctk.CTkFrame(self, fg_color="transparent")
        header.pack(fill="x", padx=25, pady=(20, 15))

        title_box = ctk.CTkFrame(header, fg_color="transparent")
        title_box.pack(side="left")
        ctk.CTkLabel(
            title_box,
            text="📋 Menu Catalog Management",
            font=ctk.CTkFont(size=22, weight="bold"),
            text_color=palette["text_primary"]
        ).pack(anchor="w")
        ctk.CTkLabel(
            title_box,
            text="Define dishes, configure pricing, and control item availability",
            font=ctk.CTkFont(size=12),
            text_color=palette["text_secondary"]
        ).pack(anchor="w")

        add_btn = ctk.CTkButton(
            header,
            text="➕ Add New Item",
            width=130,
            height=34,
            fg_color=palette["accent"],
            hover_color=palette["accent_hover"],
            command=self._open_add_dialog
        )
        add_btn.pack(side="right")

        # Filters toolbar
        toolbar = ctk.CTkFrame(self, fg_color=palette["bg_card"], corner_radius=10, border_width=1, border_color=palette["border"])
        toolbar.pack(fill="x", padx=25, pady=(0, 15))

        ctk.CTkLabel(toolbar, text="Search:", font=ctk.CTkFont(size=12, weight="bold"), text_color=palette["text_secondary"]).pack(side="left", padx=(15, 6), pady=10)
        self.entry_search = ctk.CTkEntry(toolbar, width=220, placeholder_text="Search dish by name...", height=32)
        self.entry_search.pack(side="left", padx=(0, 15), pady=10)
        self.entry_search.bind("<KeyRelease>", lambda e: self.refresh_items())

        ctk.CTkLabel(toolbar, text="Category:", font=ctk.CTkFont(size=12, weight="bold"), text_color=palette["text_secondary"]).pack(side="left", padx=(0, 6), pady=10)
        self.combo_filter_cat = ctk.CTkComboBox(toolbar, values=["All"] + DEFAULT_CATEGORIES, height=32, command=lambda v: self.refresh_items())
        self.combo_filter_cat.set("All")
        self.combo_filter_cat.pack(side="left", padx=(0, 15), pady=10)

        # Status filter switch
        self.switch_available_only = ctk.CTkCheckBox(toolbar, text="Available Only", command=self.refresh_items)
        self.switch_available_only.pack(side="left", padx=(0, 15), pady=10)

        refresh_btn = ctk.CTkButton(
            toolbar,
            text="🔄 Refresh",
            width=80,
            height=30,
            fg_color="transparent",
            text_color=palette["text_primary"],
            hover_color=palette["bg_secondary"],
            command=self.refresh_items
        )
        refresh_btn.pack(side="right", padx=15, pady=10)

        # Scrollable items table
        self.table_scroll = ctk.CTkScrollableFrame(self, fg_color="transparent")
        self.table_scroll.pack(fill="both", expand=True, padx=25, pady=(0, 20))

    def refresh_items(self):
        query = self.entry_search.get().strip() if hasattr(self, "entry_search") else ""
        category = self.combo_filter_cat.get() if hasattr(self, "combo_filter_cat") else "All"
        available_only = bool(self.switch_available_only.get()) if hasattr(self, "switch_available_only") else False

        items = self.menu_svc.search_items(query=query, category=category, available_only=available_only)
        palette = theme_manager.get_palette()

        for child in self.table_scroll.winfo_children():
            child.destroy()

        if not items:
            ctk.CTkLabel(
                self.table_scroll,
                text="No menu items match your search/filter.",
                font=ctk.CTkFont(size=13),
                text_color=palette["text_secondary"]
            ).pack(pady=40)
            return

        for item in items:
            row = ctk.CTkFrame(self.table_scroll, fg_color=palette["bg_card"], corner_radius=10, border_width=1, border_color=palette["border"])
            row.pack(fill="x", pady=4)

            # Left Info
            left = ctk.CTkFrame(row, fg_color="transparent")
            left.pack(side="left", padx=15, pady=10)

            ctk.CTkLabel(
                left,
                text=item.name,
                font=ctk.CTkFont(size=14, weight="bold"),
                text_color=palette["text_primary"]
            ).pack(anchor="w")

            ctk.CTkLabel(
                left,
                text=f"Category: {item.category}  |  Status: {'Available' if item.is_available else 'Unavailable'}",
                font=ctk.CTkFont(size=11),
                text_color=palette["success"] if item.is_available else palette["danger"]
            ).pack(anchor="w")

            # Right Controls
            right = ctk.CTkFrame(row, fg_color="transparent")
            right.pack(side="right", padx=15, pady=10)

            # Price
            ctk.CTkLabel(
                right,
                text=f"{CURRENCY_SYMBOL}{item.price}",
                font=ctk.CTkFont(size=15, weight="bold"),
                text_color=palette["text_primary"]
            ).pack(side="left", padx=(0, 20))

            # Edit Button
            edit_btn = ctk.CTkButton(
                right,
                text="✏️ Edit",
                width=65,
                height=28,
                font=ctk.CTkFont(size=11),
                fg_color=palette["bg_secondary"],
                hover_color=palette["border"],
                text_color=palette["text_primary"],
                command=lambda it=item: self._open_edit_dialog(it)
            )
            edit_btn.pack(side="left", padx=4)

            # Delete Button
            del_btn = ctk.CTkButton(
                right,
                text="🗑️ Delete",
                width=65,
                height=28,
                font=ctk.CTkFont(size=11),
                fg_color=palette["danger"],
                hover_color="#b91c1c",
                command=lambda it=item: self._delete_item(it)
            )
            del_btn.pack(side="left", padx=4)

    def _open_add_dialog(self):
        MenuDialog(self, on_save_cb=self._save_menu_item)

    def _open_edit_dialog(self, item):
        MenuDialog(self, on_save_cb=self._save_menu_item, item=item)

    def _save_menu_item(self, item_id: Optional[int], name: str, category: str, price_str: str, is_available: bool):
        if item_id:
            ok, msg = self.menu_svc.update_item(item_id, name, category, price_str, is_available)
        else:
            ok, msg, _ = self.menu_svc.add_item(name, category, price_str, is_available)
        if ok:
            self.refresh_items()
            return True, "Success"
        return False, msg

    def _delete_item(self, item):
        ok, msg = self.menu_svc.delete_item(item.id)
        if ok:
            self.refresh_items()
