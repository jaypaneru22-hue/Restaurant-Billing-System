"""Multi-theme split-screen authentication interface for RestoPro restaurant management platform.

Supports 3 user-selectable themes via an interactive theme toggle:
1. ROYAL PLUM (Dark / Default):
   - Left branding panel: #171323
   - Accent: #302044 / #7653DB
   - Right login workspace: #211B30
   - Login card: #2B233B
   - Button: #7653DB (hover #8A6BE8)

2. OBSIDIAN ORANGE (Foodix-Inspired Reference Aesthetic):
   - Outer glow / ambient frame: #0B0806
   - Left form workspace: #120E0C
   - Headline: "Manage your Restaurant, Smarter" (#FF5B1E italic accent)
   - Inputs: #1C1715 with #362C27 subtle borders
   - Primary button: #FF5B1E (hover #FF753F)
   - Right visual panel: 3D fluid ribbon sculpture in obsidian black and glowing amber
   - Customer signup: "Don't have an account ? Sign Up" (#FF5B1E)

3. SOFT LAVENDER (Coordinated Light Theme):
   - Workspace: #EDE7F5
   - Login card: #E1D7ED
   - Input background: #F1ECF6
   - Text: #292039
   - Primary button: #6650C8 (hover #7653DB)

All existing authentication, session handling, password hashing and role-based
routing logic is strictly preserved across all 6 roles (Admin, Manager, Cashier, Chef, Waiter, Customer).
"""
import json
from pathlib import Path
from typing import Callable, Optional
import customtkinter as ctk
from PIL import Image

from services.auth_service import AuthService, auth_service
from ui.theme_manager import theme_manager
from config.settings import APP_NAME, DATA_DIR, ASSETS_DIR
from utils.window_utils import center_dialog
from utils.brand_assets import (
    get_brand_logo,
    get_brand_icon,
    apply_window_icon,
)


class ForgotPasswordDialog(ctk.CTkToplevel):
    """Informational dialog for enterprise credential recovery."""

    def __init__(self, master, active_theme: str = "dark", **kwargs):
        super().__init__(master, **kwargs)
        self.title("RestoPro — Credential Recovery")
        self.resizable(False, False)
        center_dialog(self, master, target_width=440, target_height=260)
        self.grab_set()
        apply_window_icon(self)

        if active_theme == "obsidian_orange":
            bg_col = "#0B0806"
            card_col = "#161210"
            border_col = "#362C27"
            text_pri = "#FFFFFF"
            text_sec = "#A3948E"
            btn_col = "#FF5B1E"
            btn_hover = "#FF753F"
        elif active_theme == "light":
            bg_col = "#EDE7F5"
            card_col = "#E1D7ED"
            border_col = "#CFC1DF"
            text_pri = "#292039"
            text_sec = "#655873"
            btn_col = "#6650C8"
            btn_hover = "#7653DB"
        else:
            bg_col = "#211B30"
            card_col = "#2B233B"
            border_col = "#514461"
            text_pri = "#FFFFFF"
            text_sec = "#B9AEC9"
            btn_col = "#7653DB"
            btn_hover = "#8A6BE8"

        self.configure(fg_color=bg_col)

        card = ctk.CTkFrame(self, fg_color=card_col, corner_radius=12, border_width=1, border_color=border_col)
        card.pack(fill="both", expand=True, padx=20, pady=20)

        ctk.CTkLabel(
            card,
            text="Staff Credential Recovery",
            font=ctk.CTkFont(size=16, weight="bold"),
            text_color=text_pri
        ).pack(anchor="w", padx=18, pady=(16, 8))

        ctk.CTkLabel(
            card,
            text="To ensure database security and financial compliance,\nstaff passwords cannot be reset automatically at this terminal.\n\nPlease contact your Restaurant Administrator or Store Manager\nto issue a secure password reset via Staff Management.",
            font=ctk.CTkFont(size=11),
            text_color=text_sec,
            justify="left"
        ).pack(anchor="w", padx=18, pady=(0, 16))

        ctk.CTkButton(
            card,
            text="Got It (Esc)",
            width=100,
            height=32,
            font=ctk.CTkFont(size=11, weight="bold"),
            fg_color=btn_col,
            hover_color=btn_hover,
            command=self.destroy
        ).pack(anchor="e", padx=18, pady=(0, 16))

        self.bind("<Escape>", lambda e: self.destroy())


class CustomerRegisterDialog(ctk.CTkToplevel):
    """Registration dialog for customers to create a personal dining account."""

    def __init__(self, master, on_registered: Callable, auth_svc: AuthService = auth_service, active_theme: str = "dark", **kwargs):
        super().__init__(master, **kwargs)
        self.auth_svc = auth_svc
        self.on_registered = on_registered
        self.title("RestoPro — Customer Account Registration")
        self.resizable(False, False)
        center_dialog(self, master, target_width=460, target_height=520)
        self.grab_set()
        apply_window_icon(self)

        if active_theme == "obsidian_orange":
            bg_col = "#0B0806"
            card_col = "#161210"
            input_col = "#1C1715"
            border_col = "#362C27"
            text_pri = "#FFFFFF"
            text_sec = "#A3948E"
            btn_col = "#FF5B1E"
            btn_hover = "#FF753F"
        elif active_theme == "light":
            bg_col = "#EDE7F5"
            card_col = "#E1D7ED"
            input_col = "#F1ECF6"
            border_col = "#CFC1DF"
            text_pri = "#292039"
            text_sec = "#655873"
            btn_col = "#6650C8"
            btn_hover = "#7653DB"
        else:
            bg_col = "#211B30"
            card_col = "#2B233B"
            input_col = "#171323"
            border_col = "#514461"
            text_pri = "#FFFFFF"
            text_sec = "#B9AEC9"
            btn_col = "#7653DB"
            btn_hover = "#8A6BE8"

        self.configure(fg_color=bg_col)

        card = ctk.CTkFrame(self, fg_color=card_col, corner_radius=14, border_width=1, border_color=border_col)
        card.pack(fill="both", expand=True, padx=20, pady=20)

        ctk.CTkLabel(
            card,
            text="Customer Registration",
            font=ctk.CTkFont(size=18, weight="bold"),
            text_color=text_pri
        ).pack(anchor="center", pady=(16, 4))

        ctk.CTkLabel(
            card,
            text="Create an account to browse menu, track orders, and request service.",
            font=ctk.CTkFont(size=11),
            text_color=text_sec,
            justify="center"
        ).pack(anchor="center", padx=16, pady=(0, 14))

        # Full Name
        ctk.CTkLabel(card, text="Full Name", font=ctk.CTkFont(size=11, weight="bold"), text_color=text_pri).pack(anchor="w", padx=20, pady=(0, 2))
        self.ent_name = ctk.CTkEntry(card, height=36, placeholder_text="e.g. John Doe", font=ctk.CTkFont(size=11), fg_color=input_col, border_color=border_col, text_color=text_pri)
        self.ent_name.pack(fill="x", padx=20, pady=(0, 10))

        # Username
        ctk.CTkLabel(card, text="Username", font=ctk.CTkFont(size=11, weight="bold"), text_color=text_pri).pack(anchor="w", padx=20, pady=(0, 2))
        self.ent_user = ctk.CTkEntry(card, height=36, placeholder_text="e.g. johndoe", font=ctk.CTkFont(size=11), fg_color=input_col, border_color=border_col, text_color=text_pri)
        self.ent_user.pack(fill="x", padx=20, pady=(0, 10))

        # Password
        ctk.CTkLabel(card, text="Password (min 6 characters)", font=ctk.CTkFont(size=11, weight="bold"), text_color=text_pri).pack(anchor="w", padx=20, pady=(0, 2))
        self.ent_pass = ctk.CTkEntry(card, height=36, placeholder_text="Enter password", show="\u2022", font=ctk.CTkFont(size=11), fg_color=input_col, border_color=border_col, text_color=text_pri)
        self.ent_pass.pack(fill="x", padx=20, pady=(0, 10))

        self.lbl_err = ctk.CTkLabel(card, text="", font=ctk.CTkFont(size=10, weight="bold"), text_color="#EF4444")
        self.lbl_err.pack(fill="x", padx=20, pady=(0, 6))

        btn_row = ctk.CTkFrame(card, fg_color="transparent")
        btn_row.pack(fill="x", padx=20, pady=(0, 16))

        ctk.CTkButton(
            btn_row,
            text="Cancel",
            width=90,
            height=34,
            font=ctk.CTkFont(size=11, weight="bold"),
            fg_color=input_col,
            border_width=1,
            border_color=border_col,
            hover_color=border_col,
            text_color=text_pri,
            command=self.destroy
        ).pack(side="left")

        ctk.CTkButton(
            btn_row,
            text="Register & Sign In",
            height=34,
            font=ctk.CTkFont(size=11, weight="bold"),
            fg_color=btn_col,
            hover_color=btn_hover,
            text_color="#FFFFFF",
            command=self._handle_register
        ).pack(side="right")

    def _handle_register(self):
        name = self.ent_name.get().strip()
        user = self.ent_user.get().strip()
        pwd = self.ent_pass.get().strip()

        ok, msg, created_user = self.auth_svc.register_customer(user, pwd, name)
        if ok and created_user:
            self.destroy()
            self.on_registered(created_user)
        else:
            self.lbl_err.configure(text=msg)


# ---------------------------------------------------------------------------
#  Multi-Theme RestoPro Login Frame
# ---------------------------------------------------------------------------

class LoginFrame(ctk.CTkFrame):
    """Tri-theme authentication interface supporting:
    1. Royal Plum (Dark)
    2. Obsidian Orange (Foodix-Inspired Reference Aesthetic)
    3. Soft Lavender (Light)
    """

    def __init__(self, master, on_login_success: Callable, auth_svc: AuthService = auth_service, **kwargs):
        super().__init__(master, **kwargs)
        self.on_login_success = on_login_success
        self.auth_svc = auth_svc
        self._remember_file = DATA_DIR / ".remember_staff.json"
        self._password_visible = False
        self._is_submitting = False
        self._img_refs = {}

        # Determine initial theme: default to "dark" (Royal Plum) or persist previous choice
        curr = theme_manager.current_theme
        if curr in ["dark", "obsidian_orange", "light"]:
            self.active_login_theme = curr
        else:
            self.active_login_theme = "dark"

        self._build_ui()
        self._load_remembered_staff()

    def _get_colors(self, theme_key: Optional[str] = None) -> dict:
        """Returns the complete palette dictionary for the specified theme."""
        tk = theme_key or self.active_login_theme
        if tk == "obsidian_orange":
            return {
                "outer_bg": "#0B0806",
                "card_bg": "#120E0C",
                "workspace_bg": "#0B0806",
                "left_panel": "#120E0C",
                "right_panel": "#0B0806",
                "left_accent": "#201814",
                "brand_name": "#FFFFFF",
                "brand_accent": "#FF5B1E",
                "tagline": "#A3948E",
                "input_bg": "#1C1715",
                "input_border": "#362C27",
                "text_primary": "#FFFFFF",
                "text_secondary": "#A3948E",
                "placeholder": "#7A6B65",
                "btn_primary": "#FF5B1E",
                "btn_hover": "#FF753F",
                "btn_text": "#FFFFFF",
                "focus_border": "#FF5B1E",
                "checkbox": "#FF5B1E",
                "links": "#FF5B1E",
                "divider": "#2A211D",
                "toggle_bg": "#1C1715",
                "toggle_border": "#362C27",
                "demo_btn_bg": "#1C1715",
                "danger": "#EF4444",
                "accent": "#FF5B1E",
            }
        elif tk == "light":
            return {
                "outer_bg": "#EDE7F5",
                "card_bg": "#E1D7ED",
                "workspace_bg": "#EDE7F5",
                "left_panel": "#E1D7ED",
                "right_panel": "#EDE7F5",
                "left_accent": "#EDE7F5",
                "brand_name": "#292039",
                "brand_accent": "#6650C8",
                "tagline": "#655873",
                "input_bg": "#F1ECF6",
                "input_border": "#CFC1DF",
                "text_primary": "#292039",
                "text_secondary": "#655873",
                "placeholder": "#8D7F9B",
                "btn_primary": "#6650C8",
                "btn_hover": "#7653DB",
                "btn_text": "#FFFFFF",
                "focus_border": "#7653DB",
                "checkbox": "#6650C8",
                "links": "#6650C8",
                "divider": "#CFC1DF",
                "toggle_bg": "#F1ECF6",
                "toggle_border": "#CFC1DF",
                "demo_btn_bg": "#F1ECF6",
                "danger": "#DC2626",
                "accent": "#6650C8",
            }
        else:  # "dark" / Royal Plum
            return {
                "outer_bg": "#211B30",
                "card_bg": "#2B233B",
                "workspace_bg": "#211B30",
                "left_panel": "#171323",
                "right_panel": "#211B30",
                "left_accent": "#302044",
                "brand_name": "#FFFFFF",
                "brand_accent": "#9575F5",
                "tagline": "#B9A7D9",
                "input_bg": "#171323",
                "input_border": "#514461",
                "text_primary": "#FFFFFF",
                "text_secondary": "#B9AEC9",
                "placeholder": "#A99BB9",
                "btn_primary": "#7653DB",
                "btn_hover": "#8A6BE8",
                "btn_text": "#FFFFFF",
                "focus_border": "#9575F5",
                "checkbox": "#7653DB",
                "links": "#B99AFF",
                "divider": "#403451",
                "toggle_bg": "#171323",
                "toggle_border": "#514461",
                "demo_btn_bg": "#171323",
                "danger": "#EF4444",
                "accent": "#7653DB",
            }

    # ── Interactive 3-Theme Selector Bar ──────────────────────────────
    def _build_theme_selector(self, parent, colors):
        """Constructs a sleek tri-theme selector pill row."""
        sel_frame = ctk.CTkFrame(parent, fg_color="transparent")

        themes = [
            ("dark", "🌙 Royal Plum"),
            ("obsidian_orange", "🔥 Obsidian Orange"),
            ("light", "☀️ Soft Lavender"),
        ]

        for key, label in themes:
            is_active = (self.active_login_theme == key)
            bg_c = colors["btn_primary"] if is_active else colors["toggle_bg"]
            text_c = "#FFFFFF" if is_active else colors["text_secondary"]
            border_c = colors["btn_primary"] if is_active else colors["toggle_border"]

            btn = ctk.CTkButton(
                sel_frame,
                text=label,
                height=28,
                width=115 if key == "obsidian_orange" else 95,
                font=ctk.CTkFont(size=10, weight="bold" if is_active else "normal"),
                fg_color=bg_c,
                hover_color=colors["btn_hover"] if is_active else colors["left_accent"],
                text_color=text_c,
                border_width=1,
                border_color=border_c,
                corner_radius=8,
                command=lambda k=key: self._switch_theme(k),
            )
            btn.pack(side="left", padx=3)

        return sel_frame

    # ── Theme Switching Handler ───────────────────────────────────────
    def _switch_theme(self, target_theme: str):
        """Smoothly switches the active login theme in place while preserving inputs."""
        if target_theme == self.active_login_theme:
            return

        saved_user = self.username_entry.get().strip() if hasattr(self, "username_entry") else ""
        self.active_login_theme = target_theme

        # Synchronize ThemeManager
        theme_manager.apply_theme(target_theme)

        # Clear existing visual tree
        for child in self.winfo_children():
            child.destroy()
        self._img_refs.clear()

        # Rebuild UI
        self._build_ui()

        # Restore input
        if saved_user and hasattr(self, "username_entry"):
            self.username_entry.delete(0, "end")
            self.username_entry.insert(0, saved_user)

    # ── Master UI Router ──────────────────────────────────────────────
    def _build_ui(self):
        # Reset grid weights
        self.grid_columnconfigure(0, weight=0)
        self.grid_columnconfigure(1, weight=0)
        self.grid_rowconfigure(0, weight=0)

        colors = self._get_colors(self.active_login_theme)
        self.configure(fg_color=colors["outer_bg"])

        if self.active_login_theme == "obsidian_orange":
            self._build_obsidian_orange_layout(colors)
        else:
            self._build_classic_split_layout(colors)

    # ═════════════════════════════════════════════════════════════════════
    #  A. OBSIDIAN ORANGE LAYOUT (Foodix Reference Style)
    #  Form on Left, 3D Abstract Artwork on Right
    # ═════════════════════════════════════════════════════════════════════
    def _build_obsidian_orange_layout(self, colors):
        """Builds the Foodix-inspired Obsidian Orange login interface."""
        # Main layout container
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=1)

        outer_card = ctk.CTkFrame(
            self,
            fg_color=colors["card_bg"],
            corner_radius=20,
            border_width=2,
            border_color="#3D2012",
        )
        outer_card.grid(row=0, column=0, sticky="nsew", padx=24, pady=20)

        # 2 columns inside card: Left ~46% form, Right ~54% artwork
        outer_card.grid_columnconfigure(0, weight=10)
        outer_card.grid_columnconfigure(1, weight=12)
        outer_card.grid_rowconfigure(0, weight=1)

        # ── Left Form Workspace ───────────────────────────────────────
        left_box = ctk.CTkFrame(outer_card, fg_color="transparent")
        left_box.grid(row=0, column=0, sticky="nsew", padx=36, pady=24)

        # Top row: Brand mark on left, theme selector on right
        top_bar = ctk.CTkFrame(left_box, fg_color="transparent")
        top_bar.pack(fill="x", pady=(0, 14))

        # Brand mark (horizontal lockup: icon + RestoPro)
        brand_lockup = ctk.CTkFrame(top_bar, fg_color="transparent")
        brand_lockup.pack(side="left")

        orange_icon_path = ASSETS_DIR / "restopro_icon_orange.png"
        if orange_icon_path.exists():
            try:
                pil_icon = Image.open(orange_icon_path)
                ctk_icon = ctk.CTkImage(light_image=pil_icon, dark_image=pil_icon, size=(30, 30))
                self._img_refs["orange_icon"] = ctk_icon
                ctk.CTkLabel(brand_lockup, image=ctk_icon, text="").pack(side="left", padx=(0, 8))
            except Exception:
                pass

        logo_text_row = ctk.CTkFrame(brand_lockup, fg_color="transparent")
        logo_text_row.pack(side="left")
        ctk.CTkLabel(logo_text_row, text="RESTO", font=ctk.CTkFont(family="Segoe UI", size=20, weight="bold"), text_color="#FFFFFF").pack(side="left")
        ctk.CTkLabel(logo_text_row, text="PRO", font=ctk.CTkFont(family="Segoe UI", size=20, weight="bold"), text_color=colors["btn_primary"]).pack(side="left")

        # Theme selector in top bar
        selector = self._build_theme_selector(top_bar, colors)
        selector.pack(side="right")

        # Headline (Exact Reference: "Manage your Restaurant, Smarter")
        head_box = ctk.CTkFrame(left_box, fg_color="transparent")
        head_box.pack(fill="x", pady=(8, 4))

        ctk.CTkLabel(
            head_box,
            text="Manage your",
            font=ctk.CTkFont(family="Segoe UI", size=30, weight="bold"),
            text_color="#FFFFFF",
        ).pack(anchor="w")

        row2 = ctk.CTkFrame(head_box, fg_color="transparent")
        row2.pack(anchor="w")
        ctk.CTkLabel(row2, text="Restaurant, ", font=ctk.CTkFont(family="Segoe UI", size=30, weight="bold"), text_color="#FFFFFF").pack(side="left")
        ctk.CTkLabel(row2, text="Smarter ", font=ctk.CTkFont(family="Segoe UI", size=30, weight="bold", slant="italic"), text_color=colors["btn_primary"]).pack(side="left")

        # Subtitle
        ctk.CTkLabel(
            left_box,
            text="A simple and powerful tool designed to help restaurants run smoother, faster, and smarter, all in one place.",
            font=ctk.CTkFont(size=12),
            text_color=colors["text_secondary"],
            wraplength=440,
            justify="left",
        ).pack(anchor="w", pady=(6, 18))

        # Input Form Container
        form = ctk.CTkFrame(left_box, fg_color="transparent")
        form.pack(fill="x", pady=(0, 4))

        # Username / Staff ID
        self.username_entry = ctk.CTkEntry(
            form,
            height=44,
            placeholder_text="jane@gmail.com or staff username",
            font=ctk.CTkFont(size=12),
            fg_color=colors["input_bg"],
            border_color=colors["input_border"],
            border_width=1,
            text_color=colors["text_primary"],
            placeholder_text_color=colors["placeholder"],
            corner_radius=12,
        )
        self.username_entry.pack(fill="x", pady=(0, 10))

        # Password with show/hide toggle
        pass_row = ctk.CTkFrame(form, fg_color="transparent")
        pass_row.pack(fill="x", pady=(0, 8))

        self.password_entry = ctk.CTkEntry(
            pass_row,
            height=44,
            placeholder_text="\u2022\u2022\u2022\u2022\u2022\u2022",
            show="\u2022",
            font=ctk.CTkFont(size=12),
            fg_color=colors["input_bg"],
            border_color=colors["input_border"],
            border_width=1,
            text_color=colors["text_primary"],
            placeholder_text_color=colors["placeholder"],
            corner_radius=12,
        )
        self.password_entry.pack(side="left", fill="x", expand=True, padx=(0, 8))

        self.btn_toggle_pass = ctk.CTkButton(
            pass_row,
            text="\U0001F441\uFE0F",
            width=44,
            height=44,
            font=ctk.CTkFont(size=13),
            fg_color=colors["input_bg"],
            border_color=colors["input_border"],
            border_width=1,
            hover_color=colors["input_border"],
            text_color=colors["text_primary"],
            corner_radius=12,
            command=self._toggle_password_visibility,
        )
        self.btn_toggle_pass.pack(side="right")

        # Remember Me + Forgot Password
        action_row = ctk.CTkFrame(form, fg_color="transparent")
        action_row.pack(fill="x", pady=(0, 10))

        self.remember_var = ctk.BooleanVar(value=False)
        self.chk_remember = ctk.CTkCheckBox(
            action_row,
            text="Remember me",
            variable=self.remember_var,
            font=ctk.CTkFont(size=11),
            text_color=colors["text_secondary"],
            fg_color=colors["checkbox"],
            hover_color=colors["btn_hover"],
            border_color=colors["input_border"],
            checkbox_width=18,
            checkbox_height=18,
            corner_radius=4,
        )
        self.chk_remember.pack(side="left")

        btn_forgot = ctk.CTkButton(
            action_row,
            text="Forgot Password ?",
            font=ctk.CTkFont(size=11),
            fg_color="transparent",
            hover_color=colors["input_bg"],
            text_color=colors["text_secondary"],
            width=110,
            command=self._open_forgot_password,
        )
        btn_forgot.pack(side="right")

        # Error notification
        self.error_label = ctk.CTkLabel(
            form,
            text="",
            font=ctk.CTkFont(size=11, weight="bold"),
            text_color=colors["danger"],
            wraplength=380,
            justify="center",
        )
        self.error_label.pack(fill="x", pady=(0, 4))

        # Sign In Button: Rounded Orange Pill Button
        self.btn_login = ctk.CTkButton(
            form,
            text="Sign in",
            font=ctk.CTkFont(size=14, weight="bold"),
            height=46,
            fg_color=colors["btn_primary"],
            hover_color=colors["btn_hover"],
            text_color=colors["btn_text"],
            corner_radius=12,
            command=self._handle_login,
        )
        self.btn_login.pack(fill="x", pady=(0, 8))

        # Customer Signup Link (Exact Reference: "Don't have an account ? Sign Up")
        signup_row = ctk.CTkFrame(form, fg_color="transparent")
        signup_row.pack(anchor="w", pady=(2, 10))

        ctk.CTkLabel(
            signup_row,
            text="Don't have an account ? ",
            font=ctk.CTkFont(size=11),
            text_color=colors["text_secondary"],
        ).pack(side="left")

        ctk.CTkButton(
            signup_row,
            text="Sign Up",
            font=ctk.CTkFont(size=11, weight="bold"),
            fg_color="transparent",
            hover_color=colors["input_bg"],
            text_color=colors["btn_primary"],
            width=60,
            command=self._open_customer_registration,
        ).pack(side="left")

        # Demo Access Quick Access Bar (6 roles)
        demo_box = ctk.CTkFrame(
            form,
            fg_color=colors["input_bg"],
            corner_radius=10,
            border_width=1,
            border_color=colors["divider"],
        )
        demo_box.pack(fill="x", pady=(2, 6))

        ctk.CTkLabel(
            demo_box,
            text="DEMO ACCESS",
            font=ctk.CTkFont(size=9, weight="bold"),
            text_color=colors["placeholder"],
        ).pack(anchor="w", padx=10, pady=(4, 2))

        roles_row = ctk.CTkFrame(demo_box, fg_color="transparent")
        roles_row.pack(fill="x", padx=4, pady=(0, 4))

        demo_users = [
            ("Admin", "admin", "Admin@123"),
            ("Manager", "manager1", "Manager@123"),
            ("Cashier", "cashier1", "Cashier@123"),
            ("Chef", "chef1", "Chef@123"),
            ("Waiter", "waiter1", "Waiter@123"),
            ("Customer", "customer1", "Customer@123"),
        ]

        for label, u, p in demo_users:
            ctk.CTkButton(
                roles_row,
                text=label,
                width=52,
                height=22,
                font=ctk.CTkFont(size=9, weight="bold"),
                fg_color=colors["card_bg"],
                hover_color=colors["btn_primary"],
                text_color=colors["text_primary"],
                border_width=1,
                border_color=colors["divider"],
                corner_radius=6,
                command=lambda un=u, pw=p: self._quick_login(un, pw),
            ).pack(side="left", expand=True, padx=2)

        # Footer Copyright
        ctk.CTkLabel(
            left_box,
            text="Copyright \u00A9 2026 RestoPro. All rights reserved.",
            font=ctk.CTkFont(size=10),
            text_color=colors["placeholder"],
        ).pack(anchor="w", pady=(8, 0))

        # ── Right Artwork Panel ───────────────────────────────────────
        right_art_frame = ctk.CTkFrame(
            outer_card,
            corner_radius=18,
            fg_color="#0A0807",
            border_width=0,
        )
        right_art_frame.grid(row=0, column=1, sticky="nsew", padx=12, pady=12)

        art_file = ASSETS_DIR / "obsidian_orange_art.png"
        if art_file.exists():
            try:
                pil_art = Image.open(art_file)
                # Resized for high sharpness to fill the right card panel
                ctk_art = ctk.CTkImage(
                    light_image=pil_art,
                    dark_image=pil_art,
                    size=(580, 620)
                )
                self._img_refs["obsidian_art"] = ctk_art
                lbl_art = ctk.CTkLabel(right_art_frame, image=ctk_art, text="")
                lbl_art.place(relx=0.5, rely=0.5, anchor="center")
            except Exception:
                pass

        # Keyboard bindings
        self.username_entry.bind("<Return>", lambda e: self.password_entry.focus_set())
        self.password_entry.bind("<Return>", lambda e: self._handle_login())

    # ═════════════════════════════════════════════════════════════════════
    #  B. CLASSIC SPLIT LAYOUT (Royal Plum Dark & Soft Lavender Light)
    #  Branding on Left, Form Card on Right
    # ═════════════════════════════════════════════════════════════════════
    def _build_classic_split_layout(self, colors):
        """Builds the classic split layout for Royal Plum and Soft Lavender themes."""
        self.grid_columnconfigure(0, weight=11)
        self.grid_columnconfigure(1, weight=10)
        self.grid_rowconfigure(0, weight=1)

        # ── Left Branding Panel ───────────────────────────────────────
        left = ctk.CTkFrame(
            self,
            corner_radius=0,
            fg_color=colors["left_panel"],
            border_width=0,
        )
        left.grid(row=0, column=0, sticky="nsew")

        center_box = ctk.CTkFrame(left, fg_color="transparent")
        center_box.place(relx=0.5, rely=0.5, anchor="center")

        logo_img = get_brand_logo(target_width=280)
        if logo_img:
            self._img_refs["brand_logo"] = logo_img
            logo_lbl = ctk.CTkLabel(center_box, image=logo_img, text="", fg_color="transparent")
            logo_lbl.pack(anchor="center", pady=(0, 16))

        ctk.CTkLabel(
            center_box,
            text="RestoPro",
            font=ctk.CTkFont(size=32, weight="bold"),
            text_color=colors["brand_name"],
        ).pack(anchor="center", pady=(0, 6))

        ctk.CTkLabel(
            center_box,
            text="RESTAURANT MANAGEMENT PLATFORM",
            font=ctk.CTkFont(size=11, weight="bold"),
            text_color=colors["tagline"],
        ).pack(anchor="center", pady=(0, 8))

        sep = ctk.CTkFrame(
            center_box,
            height=2,
            width=120,
            fg_color=colors["divider"],
        )
        sep.pack(anchor="center", pady=(8, 12))

        ctk.CTkLabel(
            center_box,
            text="Enterprise Point of Sale & Kitchen Management",
            font=ctk.CTkFont(size=12),
            text_color=colors["tagline"],
        ).pack(anchor="center")

        # ── Right Login Workspace ─────────────────────────────────────
        right = ctk.CTkFrame(
            self,
            corner_radius=0,
            fg_color=colors["workspace_bg"],
            border_width=0,
        )
        right.grid(row=0, column=1, sticky="nsew")

        # Top Bar: Theme Selector
        top_bar = ctk.CTkFrame(right, fg_color="transparent")
        top_bar.pack(anchor="ne", padx=28, pady=(18, 0))

        sel = self._build_theme_selector(top_bar, colors)
        sel.pack(side="right")

        # Centered Card Container
        card_container = ctk.CTkFrame(right, fg_color="transparent")
        card_container.pack(expand=True, fill="both", padx=24, pady=10)

        card = ctk.CTkFrame(
            card_container,
            fg_color=colors["card_bg"],
            corner_radius=16,
            border_width=1,
            border_color=colors["divider"],
            width=430,
        )
        card.place(relx=0.5, rely=0.49, anchor="center")

        header = ctk.CTkFrame(card, fg_color="transparent")
        header.pack(fill="x", padx=36, pady=(28, 14))

        ctk.CTkLabel(
            header,
            text="Welcome back",
            font=ctk.CTkFont(size=26, weight="bold"),
            text_color=colors["text_primary"],
        ).pack(anchor="w")

        ctk.CTkLabel(
            header,
            text="Sign in to continue to RestoPro.",
            font=ctk.CTkFont(size=13),
            text_color=colors["text_secondary"],
        ).pack(anchor="w", pady=(4, 0))

        form = ctk.CTkFrame(card, fg_color="transparent")
        form.pack(fill="x", padx=36, pady=(0, 6))

        ctk.CTkLabel(
            form,
            text="Staff ID or Username",
            font=ctk.CTkFont(size=12, weight="bold"),
            text_color=colors["text_primary"],
            anchor="w",
        ).pack(fill="x", pady=(0, 6))

        self.username_entry = ctk.CTkEntry(
            form,
            height=42,
            placeholder_text="e.g. admin or cashier1",
            font=ctk.CTkFont(size=13),
            fg_color=colors["input_bg"],
            border_color=colors["input_border"],
            border_width=1,
            text_color=colors["text_primary"],
            placeholder_text_color=colors["placeholder"],
            corner_radius=10,
        )
        self.username_entry.pack(fill="x", pady=(0, 12))

        ctk.CTkLabel(
            form,
            text="Password",
            font=ctk.CTkFont(size=12, weight="bold"),
            text_color=colors["text_primary"],
            anchor="w",
        ).pack(fill="x", pady=(0, 6))

        pass_row = ctk.CTkFrame(form, fg_color="transparent")
        pass_row.pack(fill="x", pady=(0, 10))

        self.password_entry = ctk.CTkEntry(
            pass_row,
            height=42,
            placeholder_text="Enter your password",
            show="\u2022",
            font=ctk.CTkFont(size=13),
            fg_color=colors["input_bg"],
            border_color=colors["input_border"],
            border_width=1,
            text_color=colors["text_primary"],
            placeholder_text_color=colors["placeholder"],
            corner_radius=10,
        )
        self.password_entry.pack(side="left", fill="x", expand=True, padx=(0, 8))

        self.btn_toggle_pass = ctk.CTkButton(
            pass_row,
            text="\U0001F441\uFE0F",
            width=42,
            height=42,
            font=ctk.CTkFont(size=14),
            fg_color=colors["input_bg"],
            border_color=colors["input_border"],
            border_width=1,
            hover_color=colors["input_border"],
            text_color=colors["text_primary"],
            corner_radius=10,
            command=self._toggle_password_visibility,
        )
        self.btn_toggle_pass.pack(side="right")

        action_row = ctk.CTkFrame(form, fg_color="transparent")
        action_row.pack(fill="x", pady=(2, 10))

        self.remember_var = ctk.BooleanVar(value=False)
        self.chk_remember = ctk.CTkCheckBox(
            action_row,
            text="Remember Staff ID",
            variable=self.remember_var,
            font=ctk.CTkFont(size=11),
            text_color=colors["text_secondary"],
            fg_color=colors["checkbox"],
            hover_color=colors["btn_hover"],
            border_color=colors["input_border"],
            checkbox_width=18,
            checkbox_height=18,
        )
        self.chk_remember.pack(side="left")

        btn_forgot = ctk.CTkButton(
            action_row,
            text="Forgot Password?",
            font=ctk.CTkFont(size=11),
            fg_color="transparent",
            hover_color=colors["input_bg"],
            text_color=colors["links"],
            width=110,
            command=self._open_forgot_password,
        )
        btn_forgot.pack(side="right")

        self.error_label = ctk.CTkLabel(
            form,
            text="",
            font=ctk.CTkFont(size=11, weight="bold"),
            text_color=colors["danger"],
            wraplength=360,
            justify="center",
        )
        self.error_label.pack(fill="x", pady=(0, 6))

        self.btn_login = ctk.CTkButton(
            form,
            text="Sign In",
            font=ctk.CTkFont(size=15, weight="bold"),
            height=46,
            fg_color=colors["btn_primary"],
            hover_color=colors["btn_hover"],
            text_color=colors["btn_text"],
            corner_radius=10,
            command=self._handle_login,
        )
        self.btn_login.pack(fill="x", pady=(0, 8))

        self.btn_register_cust = ctk.CTkButton(
            form,
            text="New Customer? Register Account",
            font=ctk.CTkFont(size=11, weight="bold"),
            height=28,
            fg_color="transparent",
            hover_color=colors["input_bg"],
            text_color=colors["links"],
            command=self._open_customer_registration,
        )
        self.btn_register_cust.pack(fill="x", pady=(0, 8))

        # Compact Demo Access Section (6 roles)
        demo_box = ctk.CTkFrame(
            form,
            fg_color=colors["input_bg"],
            corner_radius=8,
            border_width=1,
            border_color=colors["divider"],
        )
        demo_box.pack(fill="x", pady=(2, 0))

        ctk.CTkLabel(
            demo_box,
            text="DEMO ACCESS",
            font=ctk.CTkFont(size=9, weight="bold"),
            text_color=colors["placeholder"],
        ).pack(anchor="w", padx=10, pady=(5, 2))

        roles_row = ctk.CTkFrame(demo_box, fg_color="transparent")
        roles_row.pack(fill="x", padx=4, pady=(0, 5))

        demo_users = [
            ("Admin", "admin", "Admin@123"),
            ("Manager", "manager1", "Manager@123"),
            ("Cashier", "cashier1", "Cashier@123"),
            ("Chef", "chef1", "Chef@123"),
            ("Waiter", "waiter1", "Waiter@123"),
            ("Customer", "customer1", "Customer@123"),
        ]

        for label, u, p in demo_users:
            ctk.CTkButton(
                roles_row,
                text=label,
                width=52,
                height=22,
                font=ctk.CTkFont(size=9, weight="bold"),
                fg_color=colors["card_bg"],
                hover_color=colors["btn_primary"],
                text_color=colors["text_primary"],
                border_width=1,
                border_color=colors["divider"],
                corner_radius=6,
                command=lambda un=u, pw=p: self._quick_login(un, pw),
            ).pack(side="left", expand=True, padx=2)

        footer = ctk.CTkFrame(card, fg_color="transparent")
        footer.pack(fill="x", padx=36, pady=(10, 18))

        ctk.CTkLabel(
            footer,
            text="Secure restaurant management access.",
            font=ctk.CTkFont(size=11),
            text_color=colors["placeholder"],
            justify="center",
        ).pack(anchor="center")

        self.username_entry.bind("<Return>", lambda e: self.password_entry.focus_set())
        self.password_entry.bind("<Return>", lambda e: self._handle_login())

    # ── Shared Operations ─────────────────────────────────────────────
    def _toggle_password_visibility(self):
        """Toggles between hidden dots and visible plaintext password."""
        self._password_visible = not self._password_visible
        if self._password_visible:
            self.password_entry.configure(show="")
            self.btn_toggle_pass.configure(text="\U0001F512")
        else:
            self.password_entry.configure(show="\u2022")
            self.btn_toggle_pass.configure(text="\U0001F441\uFE0F")

    def _open_forgot_password(self):
        ForgotPasswordDialog(self.winfo_toplevel(), active_theme=self.active_login_theme)

    def _open_customer_registration(self):
        CustomerRegisterDialog(
            self.winfo_toplevel(),
            on_registered=self.on_login_success,
            auth_svc=self.auth_svc,
            active_theme=self.active_login_theme,
        )

    def _quick_login(self, username: str, password: str):
        """Fills credentials and executes full production password hashing and authentication."""
        self.username_entry.delete(0, "end")
        self.username_entry.insert(0, username)
        self.password_entry.delete(0, "end")
        self.password_entry.insert(0, password)
        self._handle_login()

    def _load_remembered_staff(self):
        """Pre-populates the username if the user previously opted to remember it."""
        try:
            if self._remember_file.exists():
                with open(self._remember_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    staff_id = data.get("staff_id", "")
                    if staff_id:
                        self.username_entry.delete(0, "end")
                        self.username_entry.insert(0, staff_id)
                        self.remember_var.set(True)
                        self.password_entry.focus_set()
                        return
        except Exception:
            pass
        self.username_entry.focus_set()

    def _save_remembered_staff(self, staff_id: str):
        """Persists or clears staff ID based on the Remember Me toggle."""
        try:
            if self.remember_var.get() and staff_id:
                with open(self._remember_file, "w", encoding="utf-8") as f:
                    json.dump({"staff_id": staff_id}, f)
            else:
                if self._remember_file.exists():
                    self._remember_file.unlink()
        except Exception:
            pass

    def _handle_login(self):
        """Validates credentials, establishes session, and triggers role-based routing."""
        if self._is_submitting:
            return

        username = self.username_entry.get().strip()
        password = self.password_entry.get().strip()

        if not username:
            self.error_label.configure(text="Please enter your Staff ID or username.")
            self.username_entry.focus_set()
            return

        if not password:
            self.error_label.configure(text="Please enter your password.")
            self.password_entry.focus_set()
            return

        self._is_submitting = True
        self.btn_login.configure(state="disabled", text="Authenticating...")
        self.update_idletasks()

        ok, msg, user = self.auth_svc.login(username, password)
        if not ok or not user:
            self._is_submitting = False
            self.btn_login.configure(state="normal", text="Sign in" if self.active_login_theme == "obsidian_orange" else "Sign In")
            self.error_label.configure(text=msg)
            return

        self._save_remembered_staff(username)
        self.error_label.configure(text="")
        self._is_submitting = False
        self.btn_login.configure(state="normal", text="Sign in" if self.active_login_theme == "obsidian_orange" else "Sign In")

        # Apply personalized theme if configured
        from repositories.settings_repository import SettingsRepository
        settings = SettingsRepository().get_by_user_id(user.id)
        if settings:
            theme_manager.apply_theme(settings.theme)

        # Notify application coordinator of authenticated user
        self.on_login_success(user)
