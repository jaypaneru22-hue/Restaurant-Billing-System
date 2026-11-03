"""Premium DARK split-screen login view for RestoPro restaurant management platform.

Implements the user's requested palette:
- Overall background: #0B0B12
- Left branding panel: #101019
- Right login workspace: #0B0B12
- Login card: #171720
- Input fields: #222231
- Input borders: #38364B
- Primary text: #F5F5F7
- Secondary text: #A1A1B5
- Purple primary accent: #6657F5
- Hover accent: #806FFF
- Subtle border: #292938

DESIGN:
1. Original RestoPro logo on the left branding panel (only one logo in the entire login screen).
2. Display only the RestoPro name and small tagline beneath it.
3. No marketing content, restaurant images, or feature cards.
4. Right login panel dark charcoal/purple, not white.
5. Slightly elevated charcoal input fields with subtle borders.
6. Sign In button purple with white text.
7. Light Theme available via toggle when explicitly chosen.

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

        palette = theme_manager.get_palette()
        self.configure(fg_color=palette["bg_primary"])

        card = ctk.CTkFrame(self, fg_color=palette["bg_card"], corner_radius=12, border_width=1, border_color=palette["border"])
        card.pack(fill="both", expand=True, padx=20, pady=20)

        ctk.CTkLabel(
            card,
            text="Staff Credential Recovery",
            font=ctk.CTkFont(size=16, weight="bold"),
            text_color=palette.get("heading", palette["text_primary"])
        ).pack(anchor="w", padx=18, pady=(16, 8))

        ctk.CTkLabel(
            card,
            text="To ensure database security and financial compliance,\nstaff passwords cannot be reset automatically at this terminal.\n\nPlease contact your Restaurant Administrator or Store Manager\nto issue a secure password reset via Staff Management.",
            font=ctk.CTkFont(size=11),
            text_color=palette["text_secondary"],
            justify="left"
        ).pack(anchor="w", padx=18, pady=(0, 16))

        ctk.CTkButton(
            card,
            text="Got It (Esc)",
            width=100,
            height=32,
            font=ctk.CTkFont(size=11, weight="bold"),
            fg_color=palette["accent"],
            hover_color=palette["accent_hover"],
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

        palette = theme_manager.get_palette()
        is_dark = (theme_manager.current_theme == "dark")
        self.configure(fg_color=palette["bg_primary"])

        card = ctk.CTkFrame(self, fg_color=palette["bg_card"], corner_radius=14, border_width=1, border_color=palette["border"])
        card.pack(fill="both", expand=True, padx=20, pady=20)

        ctk.CTkLabel(
            card,
            text="Customer Registration",
            font=ctk.CTkFont(size=18, weight="bold"),
            text_color=palette.get("heading", palette["text_primary"])
        ).pack(anchor="center", pady=(16, 4))

        ctk.CTkLabel(
            card,
            text="Create an account to browse menu, track orders, and leave dining reviews.",
            font=ctk.CTkFont(size=11),
            text_color=palette["text_secondary"],
            justify="center"
        ).pack(anchor="center", padx=16, pady=(0, 14))

        # Full Name
        ctk.CTkLabel(card, text="Full Name", font=ctk.CTkFont(size=11, weight="bold"), text_color=palette.get("form_label", palette["text_primary"])).pack(anchor="w", padx=20, pady=(0, 2))
        self.ent_name = ctk.CTkEntry(card, height=36, placeholder_text="e.g. John Doe", font=ctk.CTkFont(size=11))
        self.ent_name.pack(fill="x", padx=20, pady=(0, 10))

        # Username
        ctk.CTkLabel(card, text="Username", font=ctk.CTkFont(size=11, weight="bold"), text_color=palette.get("form_label", palette["text_primary"])).pack(anchor="w", padx=20, pady=(0, 2))
        self.ent_user = ctk.CTkEntry(card, height=36, placeholder_text="e.g. johndoe", font=ctk.CTkFont(size=11))
        self.ent_user.pack(fill="x", padx=20, pady=(0, 10))

        # Password
        ctk.CTkLabel(card, text="Password (min 6 characters)", font=ctk.CTkFont(size=11, weight="bold"), text_color=palette.get("form_label", palette["text_primary"])).pack(anchor="w", padx=20, pady=(0, 2))
        self.ent_pass = ctk.CTkEntry(card, height=36, placeholder_text="Enter password", show="\u2022", font=ctk.CTkFont(size=11))
        self.ent_pass.pack(fill="x", padx=20, pady=(0, 10))

        self.lbl_err = ctk.CTkLabel(card, text="", font=ctk.CTkFont(size=10, weight="bold"), text_color=palette["danger"])
        self.lbl_err.pack(fill="x", padx=20, pady=(0, 6))

        btn_row = ctk.CTkFrame(card, fg_color="transparent")
        btn_row.pack(fill="x", padx=20, pady=(0, 16))

        ctk.CTkButton(
            btn_row,
            text="Cancel",
            width=90,
            height=34,
            font=ctk.CTkFont(size=11, weight="bold"),
            fg_color=palette["bg_secondary"],
            hover_color=palette["border"],
            text_color=palette["text_primary"],
            command=self.destroy
        ).pack(side="left")

        ctk.CTkButton(
            btn_row,
            text="Register & Sign In",
            height=34,
            font=ctk.CTkFont(size=11, weight="bold"),
            fg_color=palette["accent"],
            hover_color=palette["accent_hover"],
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
#  Premium Dark RestoPro Login Frame
# ---------------------------------------------------------------------------

class LoginFrame(ctk.CTkFrame):
    """Premium split-screen authentication interface for RestoPro.

    Uses user-specified dark enterprise colour scheme:
    - Left branding panel: #101019 with single RestoPro logo, name & tagline.
    - Right login workspace: #0B0B12 with #171720 login card.
    - Elevated charcoal inputs: #222231 with subtle borders: #38364B.
    - Purple primary CTA: #6657F5 (hover #806FFF) with white text.
    - Zero marketing fluff, zero restaurant photos, zero duplicate logos.
    """

    def __init__(self, master, on_login_success: Callable, auth_svc: AuthService = auth_service, **kwargs):
        super().__init__(master, **kwargs)
        self.on_login_success = on_login_success
        self.auth_svc = auth_svc
        self._remember_file = DATA_DIR / ".remember_staff.json"
        self._password_visible = False
        self._is_submitting = False
        self._img_refs = {}

        self._build_ui()
        self._load_remembered_staff()

    def _get_colors(self, is_dark: bool):
        """Returns specific design tokens adhering to user-specified palette."""
        if is_dark:
            return {
                "overall_bg": "#0B0B12",
                "left_panel": "#101019",
                "right_panel": "#0B0B12",
                "card_bg": "#171720",
                "card_border": "#292938",
                "input_bg": "#222231",
                "input_border": "#38364B",
                "text_primary": "#F5F5F7",
                "text_secondary": "#A1A1B5",
                "text_muted": "#71718A",
                "accent": "#6657F5",
                "accent_hover": "#806FFF",
                "toggle_bg": "#1D1D29",
                "toggle_border": "#292938",
                "demo_btn_bg": "#222231",
                "demo_btn_hover": "#6657F5",
                "demo_btn_border": "#38364B",
                "danger": "#EF4444",
            }
        else:
            # Coordinated light theme palette
            return {
                "overall_bg": "#F5F6FA",
                "left_panel": "#EAECEF",
                "right_panel": "#F5F6FA",
                "card_bg": "#FFFFFF",
                "card_border": "#E2E8F0",
                "input_bg": "#F8FAFC",
                "input_border": "#CBD5E1",
                "text_primary": "#1E293B",
                "text_secondary": "#64748B",
                "text_muted": "#94A3B8",
                "accent": "#5546E8",
                "accent_hover": "#6657F5",
                "toggle_bg": "#E2E8F0",
                "toggle_border": "#CBD5E1",
                "demo_btn_bg": "#F1F5F9",
                "demo_btn_hover": "#5546E8",
                "demo_btn_border": "#CBD5E1",
                "danger": "#DC2626",
            }

    # ── Left Panel: Clean Enterprise Branding ─────────────────────────
    def _build_left_panel(self, parent, colors, is_dark):
        """Builds the left branding panel with RestoPro logo, name & tagline only."""
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

        # 1. Single Original RestoPro Logo (prominent, strict aspect ratio 1024:682)
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
            text_color=colors["text_primary"],
        ).pack(anchor="center", pady=(0, 6))

        # 3. Small Tagline
        ctk.CTkLabel(
            center_box,
            text="RESTAURANT MANAGEMENT PLATFORM",
            font=ctk.CTkFont(size=11, weight="bold"),
            text_color=colors["accent"] if is_dark else "#4338CA",
        ).pack(anchor="center", pady=(0, 8))

        # Subtle separator line
        sep = ctk.CTkFrame(
            center_box,
            height=2,
            width=120,
            fg_color=colors["accent"] if is_dark else "#CBD5E1",
        )
        sep.pack(anchor="center", pady=(8, 12))

        # Understated descriptor
        ctk.CTkLabel(
            center_box,
            text="Enterprise Point of Sale & Kitchen Management",
            font=ctk.CTkFont(size=12),
            text_color=colors["text_secondary"],
        ).pack(anchor="center")

        return left

    # ── Right Panel: Dark Charcoal Authentication Workspace ───────────
    def _build_right_panel(self, parent, colors, is_dark):
        """Builds the right login panel with #171720 card, charcoal inputs and purple CTA."""
        right = ctk.CTkFrame(
            parent,
            corner_radius=0,
            fg_color=colors["right_panel"],
            border_width=0,
        )
        right.grid(row=0, column=1, sticky="nsew")

        # Top-right Theme Toggle
        toggle_bar = ctk.CTkFrame(right, fg_color="transparent")
        toggle_bar.pack(anchor="ne", padx=28, pady=(20, 0))

        toggle_text = "🌙 Dark Theme" if is_dark else "☀️ Light Theme"
        self.theme_btn = ctk.CTkButton(
            toggle_bar,
            text=toggle_text,
            width=116,
            height=32,
            font=ctk.CTkFont(size=11, weight="bold"),
            fg_color=colors["toggle_bg"],
            text_color=colors["accent"],
            hover_color=colors["input_border"],
            border_width=1,
            border_color=colors["toggle_border"],
            corner_radius=8,
            command=self._handle_theme_toggle,
        )
        self.theme_btn.pack(side="right")

        # Centered card container
        card_container = ctk.CTkFrame(right, fg_color="transparent")
        card_container.pack(expand=True, fill="both", padx=24, pady=10)

        # Login Card: #171720 with subtle border #292938
        card = ctk.CTkFrame(
            card_container,
            fg_color=colors["card_bg"],
            corner_radius=16,
            border_width=1,
            border_color=colors["card_border"],
            width=430,
        )
        card.place(relx=0.5, rely=0.49, anchor="center")

        # Header (NO duplicate logo here, clean typography only)
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

        # Username Input: #222231 with #38364B border
        self.username_entry = ctk.CTkEntry(
            form,
            height=44,
            placeholder_text="e.g. admin or cashier1",
            font=ctk.CTkFont(size=13),
            fg_color=colors["input_bg"],
            border_color=colors["input_border"],
            border_width=1,
            text_color=colors["text_primary"],
            placeholder_text_color=colors["text_muted"],
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

        # Password Input: #222231 with #38364B border
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
            placeholder_text_color=colors["text_muted"],
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
            fg_color=colors["accent"],
            hover_color=colors["accent_hover"],
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
            text_color=colors["accent"],
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

        # Sign In Button: Purple #6657F5 (hover #806FFF) with White Text
        self.btn_login = ctk.CTkButton(
            form,
            text="Sign In",
            font=ctk.CTkFont(size=15, weight="bold"),
            height=48,
            fg_color=colors["accent"],
            hover_color=colors["accent_hover"],
            text_color="#FFFFFF",
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
            text_color=colors["accent"],
            command=self._open_customer_registration,
        )
        self.btn_register_cust.pack(fill="x", pady=(0, 8))

        # Compact Demo Access Section (understated, bottom)
        demo_box = ctk.CTkFrame(
            form,
            fg_color=colors["input_bg"],
            corner_radius=8,
            border_width=1,
            border_color=colors["card_border"],
        )
        demo_box.pack(fill="x", pady=(2, 0))

        ctk.CTkLabel(
            demo_box,
            text="DEMO ACCESS",
            font=ctk.CTkFont(size=9, weight="bold"),
            text_color=colors["text_muted"],
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
                hover_color=colors["accent"],
                text_color=colors["text_primary"],
                border_width=1,
                border_color=colors["card_border"],
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
            text_color=colors["text_muted"],
            justify="center",
        ).pack(anchor="center")

        # Keyboard Navigation bindings
        self.username_entry.bind("<Return>", lambda e: self.password_entry.focus_set())
        self.password_entry.bind("<Return>", lambda e: self._handle_login())

        return right

    # ── Main Layout Builder ───────────────────────────────────────────
    def _build_ui(self):
        is_dark = (theme_manager.current_theme == "dark")
        colors = self._get_colors(is_dark)
        self.configure(fg_color=colors["overall_bg"])

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
        """Toggles theme between Dark and Light mode and updates the login UI."""
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
