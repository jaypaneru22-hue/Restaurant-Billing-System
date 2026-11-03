"""Premium split-screen login view for RestoPro restaurant management platform.

Implements the user's requested ROYAL PLUM + MIDNIGHT CHARCOAL palette:
DARK / ROYAL PLUM THEME (Default):
- Left branding panel: #171323
- Left subtle accent: #302044
- Brand name: #FFFFFF
- Tagline: #B9A7D9
- Right login workspace: #211B30
- Login card: #2B233B
- Input background: #171323
- Input border: #514461
- Primary text: #FFFFFF
- Secondary text: #B9AEC9
- Input placeholder: #A99BB9
- Sign In background: #7653DB (hover #8A6BE8)
- Sign In text: #FFFFFF
- Focus border: #9575F5
- Checkbox: #7653DB
- Links: #B99AFF
- Dividers / Subtle borders: #403451

LIGHT THEME (Coordinated warm lavender / soft plum):
- Workspace: #EDE7F5
- Login card: #E1D7ED
- Input background: #F1ECF6
- Text: #292039
- Secondary text: #655873
- Borders: #CFC1DF
- Primary button: #6650C8 (hover #7653DB)

All existing authentication, session handling, password hashing and role-based
routing logic is strictly preserved.
"""
import json
from pathlib import Path
from typing import Callable, Optional
import customtkinter as ctk

from services.auth_service import AuthService, auth_service
from ui.theme_manager import theme_manager
from config.settings import APP_NAME, DATA_DIR
from utils.window_utils import center_dialog
from utils.brand_assets import (
    get_brand_logo,
    get_brand_icon,
    apply_window_icon,
)


class ForgotPasswordDialog(ctk.CTkToplevel):
    """Informational dialog for enterprise credential recovery."""

    def __init__(self, master, **kwargs):
        super().__init__(master, **kwargs)
        self.title("RestoPro — Credential Recovery")
        self.resizable(False, False)
        center_dialog(self, master, target_width=440, target_height=260)
        self.grab_set()
        apply_window_icon(self)

        is_dark = (theme_manager.current_theme != "light")
        bg_col = "#211B30" if is_dark else "#EDE7F5"
        card_col = "#2B233B" if is_dark else "#E1D7ED"
        border_col = "#514461" if is_dark else "#CFC1DF"
        text_pri = "#FFFFFF" if is_dark else "#292039"
        text_sec = "#B9AEC9" if is_dark else "#655873"
        btn_col = "#7653DB" if is_dark else "#6650C8"
        btn_hover = "#8A6BE8" if is_dark else "#7653DB"

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

    def __init__(self, master, on_registered: Callable, auth_svc: AuthService = auth_service, **kwargs):
        super().__init__(master, **kwargs)
        self.auth_svc = auth_svc
        self.on_registered = on_registered
        self.title("RestoPro — Customer Account Registration")
        self.resizable(False, False)
        center_dialog(self, master, target_width=460, target_height=520)
        self.grab_set()
        apply_window_icon(self)

        is_dark = (theme_manager.current_theme != "light")
        bg_col = "#211B30" if is_dark else "#EDE7F5"
        card_col = "#2B233B" if is_dark else "#E1D7ED"
        input_col = "#171323" if is_dark else "#F1ECF6"
        border_col = "#514461" if is_dark else "#CFC1DF"
        text_pri = "#FFFFFF" if is_dark else "#292039"
        text_sec = "#B9AEC9" if is_dark else "#655873"
        btn_col = "#7653DB" if is_dark else "#6650C8"
        btn_hover = "#8A6BE8" if is_dark else "#7653DB"

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
            text="Create an account to browse menu, track orders, and leave dining reviews.",
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
#  Royal Plum RestoPro Login Frame
# ---------------------------------------------------------------------------

class LoginFrame(ctk.CTkFrame):
    """Royal Plum + Midnight Charcoal split-screen authentication interface for RestoPro.

    Palettes:
    ROYAL PLUM (Dark / Default):
    - Left branding panel: #171323 (solid dark plum, zero white/light-grey background)
    - Subtle accent / pill: #302044
    - Brand name: #FFFFFF
    - Tagline: #B9A7D9
    - Right login workspace: #211B30
    - Login card: #2B233B
    - Input background: #171323
    - Input border: #514461
    - Primary text: #FFFFFF
    - Secondary text: #B9AEC9
    - Input placeholder: #A99BB9
    - Sign In background: #7653DB (hover #8A6BE8)
    - Sign In text: #FFFFFF
    - Focus border: #9575F5
    - Checkbox: #7653DB
    - Links: #B99AFF
    - Dividers: #403451

    LIGHT THEME (Warm lavender / soft plum):
    - Workspace: #EDE7F5
    - Login card: #E1D7ED
    - Input background: #F1ECF6
    - Text: #292039
    - Secondary text: #655873
    - Borders: #CFC1DF
    - Primary button: #6650C8
    """

    def __init__(self, master, on_login_success: Callable, auth_svc: AuthService = auth_service, **kwargs):
        super().__init__(master, **kwargs)
        self.on_login_success = on_login_success
        self.auth_svc = auth_svc
        self._remember_file = DATA_DIR / ".remember_staff.json"
        self._password_visible = False
        self._is_submitting = False
        self._img_refs = {}

        # Default the login experience to Royal Plum (Dark) if not already dark
        if theme_manager.current_theme != "dark":
            theme_manager.apply_theme("dark")

        self._build_ui()
        self._load_remembered_staff()

    def _get_colors(self, is_dark: bool):
        """Returns the exact user-specified Royal Plum or coordinated Light palette."""
        if is_dark:
            return {
                "left_panel": "#171323",
                "left_accent": "#302044",
                "brand_name": "#FFFFFF",
                "tagline": "#B9A7D9",
                "workspace_bg": "#211B30",
                "card_bg": "#2B233B",
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
            }
        else:
            # Coordinated warm lavender / soft plum palette
            return {
                "left_panel": "#E1D7ED",
                "left_accent": "#EDE7F5",
                "brand_name": "#292039",
                "tagline": "#655873",
                "workspace_bg": "#EDE7F5",
                "card_bg": "#E1D7ED",
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
            }

    # ── Left Branding Panel ───────────────────────────────────────────
    def _build_left_panel(self, parent, colors, is_dark):
        """Builds the left branding panel with solid dark plum background."""
        left = ctk.CTkFrame(
            parent,
            corner_radius=0,
            fg_color=colors["left_panel"],
            border_width=0,
        )
        left.grid(row=0, column=0, sticky="nsew")

        # Centered container for logo, brand name and tagline
        center_box = ctk.CTkFrame(left, fg_color="transparent")
        center_box.place(relx=0.5, rely=0.5, anchor="center")

        # 1. RestoPro Logo (strict aspect ratio 1024:682, transparent PNG)
        logo_img = get_brand_logo(target_width=280)
        if logo_img:
            self._img_refs["brand_logo"] = logo_img
            logo_lbl = ctk.CTkLabel(center_box, image=logo_img, text="", fg_color="transparent")
            logo_lbl.pack(anchor="center", pady=(0, 16))

        # 2. RestoPro Brand Name
        ctk.CTkLabel(
            center_box,
            text="RestoPro",
            font=ctk.CTkFont(size=32, weight="bold"),
            text_color=colors["brand_name"],
        ).pack(anchor="center", pady=(0, 6))

        # 3. Small Tagline
        ctk.CTkLabel(
            center_box,
            text="RESTAURANT MANAGEMENT PLATFORM",
            font=ctk.CTkFont(size=11, weight="bold"),
            text_color=colors["tagline"],
        ).pack(anchor="center", pady=(0, 8))

        # Subtle divider
        sep = ctk.CTkFrame(
            center_box,
            height=2,
            width=120,
            fg_color=colors["divider"],
        )
        sep.pack(anchor="center", pady=(8, 12))

        # Understated descriptor
        ctk.CTkLabel(
            center_box,
            text="Enterprise Point of Sale & Kitchen Management",
            font=ctk.CTkFont(size=12),
            text_color=colors["tagline"],
        ).pack(anchor="center")

        return left

    # ── Right Login Workspace ─────────────────────────────────────────
    def _build_right_panel(self, parent, colors, is_dark):
        """Builds the dark plum workspace with #2B233B login card and #7653DB button."""
        right = ctk.CTkFrame(
            parent,
            corner_radius=0,
            fg_color=colors["workspace_bg"],
            border_width=0,
        )
        right.grid(row=0, column=1, sticky="nsew")

        # Top-right Theme Toggle
        toggle_bar = ctk.CTkFrame(right, fg_color="transparent")
        toggle_bar.pack(anchor="ne", padx=28, pady=(20, 0))

        toggle_text = "🌙 Royal Plum" if is_dark else "☀️ Soft Lavender"
        self.theme_btn = ctk.CTkButton(
            toggle_bar,
            text=toggle_text,
            width=120,
            height=32,
            font=ctk.CTkFont(size=11, weight="bold"),
            fg_color=colors["toggle_bg"],
            text_color=colors["links"],
            hover_color=colors["left_accent"],
            border_width=1,
            border_color=colors["toggle_border"],
            corner_radius=8,
            command=self._handle_theme_toggle,
        )
        self.theme_btn.pack(side="right")

        # Centered card container
        card_container = ctk.CTkFrame(right, fg_color="transparent")
        card_container.pack(expand=True, fill="both", padx=24, pady=10)

        # Login Card: #2B233B with subtle border #514461
        card = ctk.CTkFrame(
            card_container,
            fg_color=colors["card_bg"],
            corner_radius=16,
            border_width=1,
            border_color=colors["divider"],
            width=430,
        )
        card.place(relx=0.5, rely=0.49, anchor="center")

        # Header
        header = ctk.CTkFrame(card, fg_color="transparent")
        header.pack(fill="x", padx=36, pady=(32, 16))

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

        # Form Fields
        form = ctk.CTkFrame(card, fg_color="transparent")
        form.pack(fill="x", padx=36, pady=(0, 6))

        # Staff ID / Username Label
        ctk.CTkLabel(
            form,
            text="Staff ID or Username",
            font=ctk.CTkFont(size=12, weight="bold"),
            text_color=colors["text_primary"],
            anchor="w",
        ).pack(fill="x", pady=(0, 6))

        # Username Input: #171323 with #514461 border
        self.username_entry = ctk.CTkEntry(
            form,
            height=44,
            placeholder_text="e.g. admin or cashier1",
            font=ctk.CTkFont(size=13),
            fg_color=colors["input_bg"],
            border_color=colors["input_border"],
            border_width=1,
            text_color=colors["text_primary"],
            placeholder_text_color=colors["placeholder"],
            corner_radius=10,
        )
        self.username_entry.pack(fill="x", pady=(0, 14))

        # Password Label
        ctk.CTkLabel(
            form,
            text="Password",
            font=ctk.CTkFont(size=12, weight="bold"),
            text_color=colors["text_primary"],
            anchor="w",
        ).pack(fill="x", pady=(0, 6))

        pass_row = ctk.CTkFrame(form, fg_color="transparent")
        pass_row.pack(fill="x", pady=(0, 10))

        # Password Input: #171323 with #514461 border
        self.password_entry = ctk.CTkEntry(
            pass_row,
            height=44,
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

        # Password Show/Hide Toggle
        self.btn_toggle_pass = ctk.CTkButton(
            pass_row,
            text="\U0001F441\uFE0F",
            width=44,
            height=44,
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

        # Remember Staff ID & Forgot Password Row
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

        # Error notification label
        self.error_label = ctk.CTkLabel(
            form,
            text="",
            font=ctk.CTkFont(size=11, weight="bold"),
            text_color=colors["danger"],
            wraplength=360,
            justify="center",
        )
        self.error_label.pack(fill="x", pady=(0, 6))

        # Sign In Button: Royal Plum Accent #7653DB (hover #8A6BE8) with White Text
        self.btn_login = ctk.CTkButton(
            form,
            text="Sign In",
            font=ctk.CTkFont(size=15, weight="bold"),
            height=48,
            fg_color=colors["btn_primary"],
            hover_color=colors["btn_hover"],
            text_color=colors["btn_text"],
            corner_radius=10,
            command=self._handle_login,
        )
        self.btn_login.pack(fill="x", pady=(0, 8))

        # Customer Registration link
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

        # Compact Demo Access Section (understated, bottom)
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
        ).pack(anchor="w", padx=10, pady=(6, 3))

        roles_row = ctk.CTkFrame(demo_box, fg_color="transparent")
        roles_row.pack(fill="x", padx=6, pady=(0, 6))

        demo_users = [
            ("Admin", "admin", "Admin@123"),
            ("Manager", "manager1", "Manager@123"),
            ("Cashier", "cashier1", "Cashier@123"),
            ("Chef", "chef1", "Chef@123"),
            ("Customer", "customer1", "Customer@123"),
        ]

        for label, u, p in demo_users:
            ctk.CTkButton(
                roles_row,
                text=label,
                width=58,
                height=24,
                font=ctk.CTkFont(size=10, weight="bold"),
                fg_color=colors["card_bg"],
                hover_color=colors["btn_primary"],
                text_color=colors["text_primary"],
                border_width=1,
                border_color=colors["divider"],
                corner_radius=6,
                command=lambda un=u, pw=p: self._quick_login(un, pw),
            ).pack(side="left", expand=True, padx=2)

        # Footer
        footer = ctk.CTkFrame(card, fg_color="transparent")
        footer.pack(fill="x", padx=36, pady=(10, 22))

        ctk.CTkLabel(
            footer,
            text="Secure restaurant management access.",
            font=ctk.CTkFont(size=11),
            text_color=colors["placeholder"],
            justify="center",
        ).pack(anchor="center")

        # Keyboard Navigation bindings
        self.username_entry.bind("<Return>", lambda e: self.password_entry.focus_set())
        self.password_entry.bind("<Return>", lambda e: self._handle_login())

        return right

    # ── Main Layout Builder ───────────────────────────────────────────
    def _build_ui(self):
        is_dark = (theme_manager.current_theme != "light")
        colors = self._get_colors(is_dark)
        self.configure(fg_color=colors["workspace_bg"])

        # 2-column grid: left ~52%, right ~48%
        self.grid_columnconfigure(0, weight=11)
        self.grid_columnconfigure(1, weight=10)
        self.grid_rowconfigure(0, weight=1)

        self._build_left_panel(self, colors, is_dark)
        self._build_right_panel(self, colors, is_dark)

    # ── Preserved Authentication Logic ────────────────────────────────
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
        ForgotPasswordDialog(self.winfo_toplevel())

    def _handle_theme_toggle(self):
        """Toggles theme between Royal Plum and Soft Lavender and updates the login UI."""
        saved_user = self.username_entry.get().strip() if hasattr(self, "username_entry") else ""
        theme_manager.toggle_theme()
        for child in self.winfo_children():
            child.destroy()
        self._img_refs.clear()
        self._build_ui()
        if saved_user and hasattr(self, "username_entry"):
            self.username_entry.delete(0, "end")
            self.username_entry.insert(0, saved_user)

    def _open_customer_registration(self):
        CustomerRegisterDialog(self.winfo_toplevel(), on_registered=self.on_login_success)

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
            self.btn_login.configure(state="normal", text="Sign In")
            self.error_label.configure(text=msg)
            return

        self._save_remembered_staff(username)
        self.error_label.configure(text="")

        # Apply personalized theme if configured
        from repositories.settings_repository import SettingsRepository
        settings = SettingsRepository().get_by_user_id(user.id)
        if settings:
            theme_manager.apply_theme(settings.theme)

        # Notify application coordinator of authenticated user
        self.on_login_success(user)
