"""Login view for commercial staff authentication with role-based routing."""
import json
from pathlib import Path
from typing import Callable, Optional
import customtkinter as ctk

from services.auth_service import AuthService, auth_service
from ui.theme_manager import theme_manager
from config.settings import APP_NAME, DATA_DIR
from utils.window_utils import center_dialog
from utils.brand_assets import get_brand_logo, get_brand_icon, apply_window_icon


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
            text="🔒 Staff Credential Recovery",
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
        center_dialog(self, master, target_width=460, target_height=540)
        self.grab_set()
        apply_window_icon(self)

        palette = theme_manager.get_palette()
        is_dark = (theme_manager.current_theme == "dark")
        self.configure(fg_color=palette["bg_primary"])

        card = ctk.CTkFrame(self, fg_color=palette["bg_card"], corner_radius=14, border_width=1, border_color=palette["border"])
        card.pack(fill="both", expand=True, padx=20, pady=20)

        # Prominent RestoPro Logo Showcase
        logo_img = get_brand_logo(target_width=170)
        if logo_img:
            logo_frame = ctk.CTkFrame(
                card,
                fg_color="#08080E" if is_dark else "#0A0A12",
                corner_radius=12,
                border_width=1,
                border_color="#2A2A3A" if is_dark else "#312E81"
            )
            logo_frame.pack(anchor="center", pady=(14, 8))

            logo_lbl = ctk.CTkLabel(logo_frame, image=logo_img, text="")
            logo_lbl.pack(padx=8, pady=6)

        ctk.CTkLabel(
            card,
            text="🍽️ Customer Registration",
            font=ctk.CTkFont(size=16, weight="bold"),
            text_color=palette.get("heading", palette["text_primary"])
        ).pack(anchor="center", pady=(0, 2))

        ctk.CTkLabel(
            card,
            text="Create an account to browse menu, track orders, and leave dining reviews.",
            font=ctk.CTkFont(size=11),
            text_color=palette["text_secondary"],
            justify="center"
        ).pack(anchor="center", padx=16, pady=(0, 12))

        # Full Name
        ctk.CTkLabel(card, text="Full Name", font=ctk.CTkFont(size=11, weight="bold"), text_color=palette.get("form_label", palette["text_primary"])).pack(anchor="w", padx=20, pady=(0, 2))
        self.ent_name = ctk.CTkEntry(card, height=34, placeholder_text="e.g. John Doe", font=ctk.CTkFont(size=11))
        self.ent_name.pack(fill="x", padx=20, pady=(0, 10))

        # Username
        ctk.CTkLabel(card, text="Username", font=ctk.CTkFont(size=11, weight="bold"), text_color=palette.get("form_label", palette["text_primary"])).pack(anchor="w", padx=20, pady=(0, 2))
        self.ent_user = ctk.CTkEntry(card, height=34, placeholder_text="e.g. johndoe", font=ctk.CTkFont(size=11))
        self.ent_user.pack(fill="x", padx=20, pady=(0, 10))

        # Password
        ctk.CTkLabel(card, text="Password (min 6 characters)", font=ctk.CTkFont(size=11, weight="bold"), text_color=palette.get("form_label", palette["text_primary"])).pack(anchor="w", padx=20, pady=(0, 2))
        self.ent_pass = ctk.CTkEntry(card, height=34, placeholder_text="Enter password", show="•", font=ctk.CTkFont(size=11))
        self.ent_pass.pack(fill="x", padx=20, pady=(0, 10))

        self.lbl_err = ctk.CTkLabel(card, text="", font=ctk.CTkFont(size=10, weight="bold"), text_color=palette["danger"])
        self.lbl_err.pack(fill="x", padx=20, pady=(0, 6))

        btn_row = ctk.CTkFrame(card, fg_color="transparent")
        btn_row.pack(fill="x", padx=20, pady=(0, 12))

        ctk.CTkButton(
            btn_row,
            text="Cancel",
            width=90,
            height=32,
            font=ctk.CTkFont(size=11, weight="bold"),
            fg_color=palette["bg_secondary"],
            hover_color=palette["border"],
            text_color=palette["text_primary"],
            command=self.destroy
        ).pack(side="left")

        ctk.CTkButton(
            btn_row,
            text="Register & Sign In 🚀",
            height=32,
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


class LoginFrame(ctk.CTkFrame):
    """Modern SaaS commercial authentication interface inspired by industry POS solutions."""

    def __init__(self, master, on_login_success: Callable, auth_svc: AuthService = auth_service, **kwargs):
        super().__init__(master, **kwargs)
        self.on_login_success = on_login_success
        self.auth_svc = auth_svc
        self._remember_file = DATA_DIR / ".remember_staff.json"
        self._password_visible = False
        self._is_submitting = False

        self._build_ui()
        self._load_remembered_staff()

    def _build_ui(self):
        palette = theme_manager.get_palette()
        is_dark = (theme_manager.current_theme == "dark")
        self.configure(fg_color=palette["bg_secondary"])

        # Top Bar with Instant Theme Toggle (Light / Dark)
        top_bar = ctk.CTkFrame(self, fg_color="transparent")
        top_bar.place(relx=1.0, rely=0.0, anchor="ne", x=-24, y=20)

        self.theme_btn = ctk.CTkButton(
            top_bar,
            text="🌙 Dark Mode" if theme_manager.current_theme == "light" else "☀️ Light Mode",
            width=96,
            height=30,
            font=ctk.CTkFont(size=11, weight="bold"),
            fg_color=palette.get("accent_light", palette["bg_secondary"]),
            text_color=palette["accent"],
            hover_color=palette["border"],
            command=self._handle_theme_toggle
        )
        self.theme_btn.pack(side="right")

        # Center elevation card
        card = ctk.CTkFrame(
            self,
            fg_color=palette["bg_card"],
            corner_radius=16,
            border_width=1,
            border_color=palette["border"],
            width=460
        )
        card.place(relx=0.5, rely=0.5, anchor="center")

        # 1. Header & Brand Identity Area
        header_box = ctk.CTkFrame(card, fg_color="transparent")
        header_box.pack(fill="x", padx=36, pady=(24, 12))

        # RestoPro Prominent Logo Showcase (Preserving Exact Aspect Ratio & Sharpness)
        logo_img = get_brand_logo(target_width=210)
        if logo_img:
            self.logo_frame = ctk.CTkFrame(
                header_box,
                fg_color="#08080E" if is_dark else "#0A0A12",
                corner_radius=14,
                border_width=1,
                border_color="#2A2A3A" if is_dark else "#312E81"
            )
            self.logo_frame.pack(anchor="center", pady=(0, 10))

            logo_lbl = ctk.CTkLabel(self.logo_frame, image=logo_img, text="")
            logo_lbl.pack(padx=10, pady=8)

        ctk.CTkLabel(
            header_box,
            text="Staff Sign In",
            font=ctk.CTkFont(size=20, weight="bold"),
            text_color=palette.get("heading", palette["text_primary"])
        ).pack(anchor="center")

        ctk.CTkLabel(
            header_box,
            text="Authorized staff terminal • Enter your assigned credentials",
            font=ctk.CTkFont(size=11),
            text_color=palette["text_secondary"],
            justify="center"
        ).pack(anchor="center", pady=(2, 0))

        # 2. Form Inputs
        form_box = ctk.CTkFrame(card, fg_color="transparent")
        form_box.pack(fill="x", padx=36, pady=(0, 12))

        # Username / Staff ID
        ctk.CTkLabel(
            form_box,
            text="Staff ID or Username",
            font=ctk.CTkFont(size=11, weight="bold"),
            text_color=palette.get("form_label", palette["text_primary"]),
            anchor="w"
        ).pack(fill="x", pady=(0, 4))

        self.username_entry = ctk.CTkEntry(
            form_box,
            height=38,
            placeholder_text="e.g. admin or cashier1",
            font=ctk.CTkFont(size=12)
        )
        self.username_entry.pack(fill="x", pady=(0, 12))

        # Password
        ctk.CTkLabel(
            form_box,
            text="Password",
            font=ctk.CTkFont(size=11, weight="bold"),
            text_color=palette.get("form_label", palette["text_primary"]),
            anchor="w"
        ).pack(fill="x", pady=(0, 4))

        pass_row = ctk.CTkFrame(form_box, fg_color="transparent")
        pass_row.pack(fill="x", pady=(0, 10))

        self.password_entry = ctk.CTkEntry(
            pass_row,
            height=38,
            placeholder_text="Enter secure password",
            show="•",
            font=ctk.CTkFont(size=12)
        )
        self.password_entry.pack(side="left", fill="x", expand=True, padx=(0, 6))

        self.btn_toggle_pass = ctk.CTkButton(
            pass_row,
            text="👁️",
            width=38,
            height=38,
            font=ctk.CTkFont(size=13),
            fg_color=palette["bg_secondary"],
            hover_color=palette["border"],
            text_color=palette["text_primary"],
            command=self._toggle_password_visibility
        )
        self.btn_toggle_pass.pack(side="right")

        # Remember me & Forgot Password Row
        action_row = ctk.CTkFrame(form_box, fg_color="transparent")
        action_row.pack(fill="x", pady=(2, 10))

        self.remember_var = ctk.BooleanVar(value=False)
        self.chk_remember = ctk.CTkCheckBox(
            action_row,
            text="Remember Staff ID",
            variable=self.remember_var,
            font=ctk.CTkFont(size=11),
            text_color=palette["text_secondary"],
            checkbox_width=18,
            checkbox_height=18
        )
        self.chk_remember.pack(side="left")

        btn_forgot = ctk.CTkButton(
            action_row,
            text="Forgot Password?",
            font=ctk.CTkFont(size=11),
            fg_color="transparent",
            hover_color=palette["bg_secondary"],
            text_color=palette["accent"],
            width=100,
            command=self._open_forgot_password
        )
        btn_forgot.pack(side="right")

        # Error notification strip
        self.error_label = ctk.CTkLabel(
            form_box,
            text="",
            font=ctk.CTkFont(size=11, weight="bold"),
            text_color=palette["danger"],
            wraplength=380,
            justify="center"
        )
        self.error_label.pack(fill="x", pady=(0, 8))

        # Sign In Submit Button
        self.btn_login = ctk.CTkButton(
            form_box,
            text="Sign In to Terminal 🚀",
            font=ctk.CTkFont(size=13, weight="bold"),
            height=40,
            fg_color=palette["accent"],
            hover_color=palette["accent_hover"],
            text_color="#FFFFFF",
            command=self._handle_login
        )
        self.btn_login.pack(fill="x", pady=(0, 6))

        # Customer Registration Action
        self.btn_register_cust = ctk.CTkButton(
            form_box,
            text="🍽️ New Customer? Register Account",
            font=ctk.CTkFont(size=11, weight="bold"),
            height=30,
            fg_color="transparent",
            hover_color=palette["bg_secondary"],
            text_color=palette["accent"],
            command=self._open_customer_registration
        )
        self.btn_register_cust.pack(fill="x", pady=(0, 10))

        # Quick Demo Role Fill Row
        demo_box = ctk.CTkFrame(form_box, fg_color=palette["bg_secondary"], corner_radius=8)
        demo_box.pack(fill="x", pady=(0, 8))

        ctk.CTkLabel(
            demo_box,
            text="⚡ QUICK DEMO LOGIN (1-CLICK):",
            font=ctk.CTkFont(size=9, weight="bold"),
            text_color=palette["text_secondary"]
        ).pack(anchor="w", padx=10, pady=(6, 4))

        roles_row = ctk.CTkFrame(demo_box, fg_color="transparent")
        roles_row.pack(fill="x", padx=6, pady=(0, 8))

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
                width=65,
                height=26,
                font=ctk.CTkFont(size=10, weight="bold"),
                fg_color=palette["bg_card"],
                hover_color=palette["accent"],
                text_color=palette["text_primary"],
                command=lambda un=u, pw=p: self._quick_login(un, pw)
            ).pack(side="left", expand=True, padx=2)

        # 3. Footer Security Indicator
        footer_box = ctk.CTkFrame(card, fg_color="transparent")
        footer_box.pack(fill="x", padx=36, pady=(0, 24))

        ctk.CTkLabel(
            footer_box,
            text="🔒 256-bit PBKDF2 Password Hashing • Role-Enforced RBAC",
            font=ctk.CTkFont(size=10),
            text_color=palette["text_secondary"],
            justify="center"
        ).pack(anchor="center")

        # Keyboard Navigation bindings
        self.username_entry.bind("<Return>", lambda e: self.password_entry.focus_set())
        self.password_entry.bind("<Return>", lambda e: self._handle_login())

    def _toggle_password_visibility(self):
        """Toggles between hidden dots and visible plaintext password."""
        self._password_visible = not self._password_visible
        if self._password_visible:
            self.password_entry.configure(show="")
            self.btn_toggle_pass.configure(text="🔒")
        else:
            self.password_entry.configure(show="•")
            self.btn_toggle_pass.configure(text="👁️")

    def _open_forgot_password(self):
        ForgotPasswordDialog(self.winfo_toplevel())

    def _handle_theme_toggle(self):
        """Toggles theme between Dark and Light mode and updates the login UI."""
        saved_user = self.username_entry.get().strip() if hasattr(self, "username_entry") else ""
        theme_manager.toggle_theme()
        for child in self.winfo_children():
            child.destroy()
        self._build_ui()
        if saved_user and hasattr(self, "username_entry"):
            self.username_entry.delete(0, "end")
            self.username_entry.insert(0, saved_user)

    def _open_customer_registration(self):
        CustomerRegisterDialog(self.winfo_toplevel(), on_registered=self.on_login_success)

    def _quick_login(self, username: str, password: str):
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
        self.btn_login.configure(state="disabled", text="Authenticating Terminal...")
        self.update_idletasks()

        ok, msg, user = self.auth_svc.login(username, password)
        if not ok or not user:
            self._is_submitting = False
            self.btn_login.configure(state="normal", text="Sign In to Terminal 🚀")
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
