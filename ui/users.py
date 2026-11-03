"""User Management and Staff Account Administration views."""
from typing import Optional, Callable, List
import customtkinter as ctk

from models.user import User
from repositories.user_repository import UserRepository, user_repository
from services.auth_service import AuthService, auth_service
from ui.theme_manager import theme_manager
from utils.security import hash_password
from utils.validators import validate_username
from utils.window_utils import center_dialog


class StaffDialog(ctk.CTkToplevel):
    """Modal dialog for creating and editing staff accounts."""

    def __init__(self, master, on_saved: Callable, user: Optional[User] = None, user_repo: UserRepository = user_repository, **kwargs):
        super().__init__(master, **kwargs)
        self.on_saved = on_saved
        self.user = user
        self.user_repo = user_repo

        self.title("Edit Staff Member" if user else "Add New Staff Member")
        self.resizable(False, False)
        center_dialog(self, master, target_width=480, target_height=520)
        self.grab_set()

        self._build_ui()

    def _build_ui(self):
        palette = theme_manager.get_palette()
        self.configure(fg_color=palette["bg_primary"])

        title_text = f"✏️ Edit Staff: {self.user.username}" if self.user else "➕ Add New Staff Member"
        ctk.CTkLabel(
            self,
            text=title_text,
            font=ctk.CTkFont(size=18, weight="bold"),
            text_color=palette.get("heading", palette["text_primary"])
        ).pack(padx=25, pady=(20, 15), anchor="w")

        form = ctk.CTkFrame(self, fg_color=palette["bg_card"], corner_radius=10, border_width=1, border_color=palette["border"])
        form.pack(fill="both", expand=True, padx=25, pady=(0, 15))

        # Full Name
        ctk.CTkLabel(form, text="Full Name *", font=ctk.CTkFont(size=11, weight="bold"), text_color=palette.get("form_label", palette["text_primary"])).pack(anchor="w", padx=20, pady=(14, 2))
        self.entry_name = ctk.CTkEntry(form, height=34, font=ctk.CTkFont(size=12), placeholder_text="e.g. Rahul Sharma")
        self.entry_name.pack(fill="x", padx=20, pady=(0, 10))
        if self.user:
            self.entry_name.insert(0, self.user.full_name)

        # Username
        ctk.CTkLabel(form, text="Username (Login ID) *", font=ctk.CTkFont(size=11, weight="bold"), text_color=palette.get("form_label", palette["text_primary"])).pack(anchor="w", padx=20, pady=(0, 2))
        self.entry_username = ctk.CTkEntry(form, height=34, font=ctk.CTkFont(size=12), placeholder_text="e.g. rahul1")
        self.entry_username.pack(fill="x", padx=20, pady=(0, 10))
        if self.user:
            self.entry_username.insert(0, self.user.username)
            self.entry_username.configure(state="disabled")

        # Role
        ctk.CTkLabel(form, text="Assigned System Role *", font=ctk.CTkFont(size=11, weight="bold"), text_color=palette.get("form_label", palette["text_primary"])).pack(anchor="w", padx=20, pady=(0, 2))
        self.combo_role = ctk.CTkComboBox(form, values=["CASHIER", "WAITER", "CHEF", "MANAGER", "ADMIN"], height=34)
        self.combo_role.pack(fill="x", padx=20, pady=(0, 10))
        if self.user:
            self.combo_role.set(self.user.role)
        else:
            self.combo_role.set("CASHIER")

        # Password (required on create, optional note on edit)
        if not self.user:
            ctk.CTkLabel(form, text="Initial Password * (min 6 characters)", font=ctk.CTkFont(size=11, weight="bold"), text_color=palette.get("form_label", palette["text_primary"])).pack(anchor="w", padx=20, pady=(0, 2))
            self.entry_password = ctk.CTkEntry(form, height=34, font=ctk.CTkFont(size=12), show="•", placeholder_text="Enter secure password")
            self.entry_password.pack(fill="x", padx=20, pady=(0, 10))
        else:
            self.entry_password = None

        # Active Status Switch
        self.switch_active = ctk.CTkSwitch(form, text="Account Active & Permitted to Login", font=ctk.CTkFont(size=11, weight="bold"), text_color=palette.get("form_label", palette["text_primary"]))
        self.switch_active.pack(anchor="w", padx=20, pady=(4, 10))
        if self.user and not self.user.is_active:
            self.switch_active.deselect()
        else:
            self.switch_active.select()

        # Error label
        self.lbl_error = ctk.CTkLabel(form, text="", font=ctk.CTkFont(size=11), text_color=palette["danger"])
        self.lbl_error.pack(fill="x", padx=20, pady=(0, 5))

        # Action Buttons
        btn_box = ctk.CTkFrame(self, fg_color="transparent")
        btn_box.pack(fill="x", padx=25, pady=(0, 20))

        ctk.CTkButton(
            btn_box,
            text="Cancel",
            width=90,
            height=34,
            fg_color=palette["bg_card"],
            text_color=palette["text_primary"],
            hover_color=palette["bg_secondary"],
            command=self.destroy
        ).pack(side="right", padx=(10, 0))

        ctk.CTkButton(
            btn_box,
            text="Save Changes" if self.user else "Create Account",
            width=130,
            height=34,
            fg_color=palette["accent"],
            hover_color=palette["accent_hover"],
            command=self._handle_save
        ).pack(side="right")

    def _handle_save(self):
        full_name = self.entry_name.get().strip()
        role = self.combo_role.get().strip()
        is_active = bool(self.switch_active.get())

        if not full_name:
            self.lbl_error.configure(text="Full name cannot be empty.")
            return

        if self.user:
            # Edit existing staff
            ok = self.user_repo.update_staff(self.user.id, full_name, role, is_active)
            if ok:
                self.on_saved()
                self.destroy()
            else:
                self.lbl_error.configure(text="Failed to update staff member.")
        else:
            # Create new staff
            username = self.entry_username.get().strip()
            password = self.entry_password.get() if self.entry_password else ""

            valid_u, u_err = validate_username(username)
            if not valid_u:
                self.lbl_error.configure(text=u_err)
                return

            if self.user_repo.get_by_username(username):
                self.lbl_error.configure(text=f"Username '{username}' is already taken.")
                return

            if len(password) < 6:
                self.lbl_error.configure(text="Password must be at least 6 characters.")
                return

            pwd_hash = hash_password(password)
            created = self.user_repo.create(username, pwd_hash, full_name, role, is_active)
            if created:
                self.on_saved()
                self.destroy()
            else:
                self.lbl_error.configure(text="Failed to create user account.")


class PasswordResetDialog(ctk.CTkToplevel):
    """Modal dialog allowing Administrator to reset any staff member's password."""

    def __init__(self, master, user: User, on_reset_cb: Callable, user_repo: UserRepository = user_repository, **kwargs):
        super().__init__(master, **kwargs)
        self.user = user
        self.on_reset_cb = on_reset_cb
        self.user_repo = user_repo

        self.title("Reset Staff Password")
        self.resizable(False, False)
        center_dialog(self, master, target_width=440, target_height=360)
        self.grab_set()

        self._build_ui()

    def _build_ui(self):
        palette = theme_manager.get_palette()
        self.configure(fg_color=palette["bg_primary"])

        ctk.CTkLabel(
            self,
            text=f"🔑 Reset Password for {self.user.username}",
            font=ctk.CTkFont(size=17, weight="bold"),
            text_color=palette.get("heading", palette["text_primary"])
        ).pack(padx=25, pady=(20, 5), anchor="w")

        ctk.CTkLabel(
            self,
            text=f"Staff: {self.user.full_name}  •  Role: {self.user.role}",
            font=ctk.CTkFont(size=11),
            text_color=palette["text_secondary"]
        ).pack(padx=25, pady=(0, 14), anchor="w")

        form = ctk.CTkFrame(self, fg_color=palette["bg_card"], corner_radius=10, border_width=1, border_color=palette["border"])
        form.pack(fill="both", expand=True, padx=25, pady=(0, 15))

        ctk.CTkLabel(form, text="New Password * (min 6 characters)", font=ctk.CTkFont(size=11, weight="bold"), text_color=palette.get("form_label", palette["text_primary"])).pack(anchor="w", padx=20, pady=(16, 2))
        self.entry_pwd = ctk.CTkEntry(form, height=34, font=ctk.CTkFont(size=12), show="•")
        self.entry_pwd.pack(fill="x", padx=20, pady=(0, 10))

        ctk.CTkLabel(form, text="Confirm New Password *", font=ctk.CTkFont(size=11, weight="bold"), text_color=palette.get("form_label", palette["text_primary"])).pack(anchor="w", padx=20, pady=(0, 2))
        self.entry_confirm = ctk.CTkEntry(form, height=34, font=ctk.CTkFont(size=12), show="•")
        self.entry_confirm.pack(fill="x", padx=20, pady=(0, 10))

        self.lbl_error = ctk.CTkLabel(form, text="", font=ctk.CTkFont(size=11), text_color=palette["danger"])
        self.lbl_error.pack(fill="x", padx=20, pady=(0, 6))

        btn_box = ctk.CTkFrame(self, fg_color="transparent")
        btn_box.pack(fill="x", padx=25, pady=(0, 20))

        ctk.CTkButton(
            btn_box,
            text="Cancel",
            width=90,
            height=34,
            fg_color=palette["bg_card"],
            text_color=palette["text_primary"],
            hover_color=palette["bg_secondary"],
            command=self.destroy
        ).pack(side="right", padx=(10, 0))

        ctk.CTkButton(
            btn_box,
            text="Update Password",
            width=130,
            height=34,
            fg_color=palette["accent"],
            hover_color=palette["accent_hover"],
            command=self._handle_reset
        ).pack(side="right")

    def _handle_reset(self):
        pwd = self.entry_pwd.get()
        confirm = self.entry_confirm.get()

        if len(pwd) < 6:
            self.lbl_error.configure(text="Password must be at least 6 characters.")
            return

        if pwd != confirm:
            self.lbl_error.configure(text="Passwords do not match.")
            return

        new_hash = hash_password(pwd)
        ok = self.user_repo.reset_password(self.user.id, new_hash)
        if ok:
            self.on_reset_cb()
            self.destroy()
        else:
            self.lbl_error.configure(text="Failed to update password.")


class UserManagementFrame(ctk.CTkFrame):
    """Complete Enterprise Staff & User Account Administration view."""

    def __init__(self, master, user_repo: UserRepository = user_repository, auth_svc: AuthService = auth_service, **kwargs):
        super().__init__(master, **kwargs)
        self.user_repo = user_repo
        self.auth_svc = auth_svc

        theme_manager.subscribe(self.on_theme_changed)
        self._build_ui()
        self.refresh_users()

    def destroy(self):
        theme_manager.unsubscribe(self.on_theme_changed)
        super().destroy()

    def on_theme_changed(self, theme_name: str):
        if self.winfo_exists():
            palette = theme_manager.get_palette()
            self.configure(fg_color=palette["bg_primary"])
            self.refresh_users()

    def _build_ui(self):
        palette = theme_manager.get_palette()
        self.configure(fg_color=palette["bg_primary"])

        # Main scrollable canvas container to ensure fit on 1366x768
        self.main_scroll = ctk.CTkScrollableFrame(self, fg_color="transparent")
        self.main_scroll.pack(fill="both", expand=True)

        # Header Bar
        header = ctk.CTkFrame(self.main_scroll, fg_color="transparent")
        header.pack(fill="x", padx=24, pady=(18, 12))

        title_col = ctk.CTkFrame(header, fg_color="transparent")
        title_col.pack(side="left")

        ctk.CTkLabel(
            title_col,
            text="👥 Staff & User Account Administration",
            font=ctk.CTkFont(size=20, weight="bold"),
            text_color=palette.get("heading", palette["text_primary"])
        ).pack(anchor="w")

        ctk.CTkLabel(
            title_col,
            text="Manage counter cashiers, floor managers and executive administrators • Access control & credentials",
            font=ctk.CTkFont(size=11),
            text_color=palette["text_secondary"]
        ).pack(anchor="w")

        # Action button: Add Staff
        actions_box = ctk.CTkFrame(header, fg_color="transparent")
        actions_box.pack(side="right")

        ctk.CTkButton(
            actions_box,
            text="🔄 Refresh",
            width=85,
            height=32,
            font=ctk.CTkFont(size=11, weight="bold"),
            fg_color=palette["bg_card"],
            hover_color=palette["bg_secondary"],
            text_color=palette["text_primary"],
            command=self.refresh_users
        ).pack(side="left", padx=4)

        ctk.CTkButton(
            actions_box,
            text="➕ Add New Staff",
            width=135,
            height=32,
            font=ctk.CTkFont(size=11, weight="bold"),
            fg_color=palette["accent"],
            hover_color=palette["accent_hover"],
            command=self._open_add_dialog
        ).pack(side="left", padx=4)

        # 4 Summary KPI Cards
        kpi_row = ctk.CTkFrame(self.main_scroll, fg_color="transparent")
        kpi_row.pack(fill="x", padx=24, pady=(0, 14))
        kpi_row.grid_columnconfigure((0, 1, 2, 3), weight=1, uniform="kpi_user")

        self.lbl_kpi_total = self._build_kpi_card(kpi_row, 0, "👥 Total Accounts", "0", "All registered staff", "#3B82F6", palette)
        self.lbl_kpi_active = self._build_kpi_card(kpi_row, 1, "🟢 Active Staff", "0", "Permitted terminal login", "#10B981", palette)
        self.lbl_kpi_inactive = self._build_kpi_card(kpi_row, 2, "🚫 Deactivated", "0", "Suspended access", "#EF4444", palette)
        self.lbl_kpi_admins = self._build_kpi_card(kpi_row, 3, "🛡️ Administrators", "0", "Full system privileges", "#8B5CF6", palette)

        # Filter & Search Controls Bar
        filter_card = ctk.CTkFrame(self.main_scroll, fg_color=palette["bg_card"], corner_radius=10, border_width=1, border_color=palette["border"])
        filter_card.pack(fill="x", padx=24, pady=(0, 14))

        f_inner = ctk.CTkFrame(filter_card, fg_color="transparent")
        f_inner.pack(fill="x", padx=14, pady=10)

        ctk.CTkLabel(f_inner, text="🔍", font=ctk.CTkFont(size=14)).pack(side="left", padx=(0, 4))
        self.entry_search = ctk.CTkEntry(
            f_inner,
            placeholder_text="Search staff by username or full name...",
            height=32,
            width=260,
            font=ctk.CTkFont(size=11)
        )
        self.entry_search.pack(side="left", padx=(0, 14))
        self.entry_search.bind("<KeyRelease>", lambda e: self._apply_filters())

        ctk.CTkLabel(f_inner, text="Role:", font=ctk.CTkFont(size=11, weight="bold"), text_color=palette["text_secondary"]).pack(side="left", padx=(0, 4))
        self.combo_role_filter = ctk.CTkComboBox(
            f_inner,
            values=["All Roles", "ADMIN", "MANAGER", "CASHIER", "CHEF", "WAITER", "CUSTOMER"],
            width=125,
            height=32,
            command=lambda v: self._apply_filters()
        )
        self.combo_role_filter.set("All Roles")
        self.combo_role_filter.pack(side="left", padx=(0, 14))

        ctk.CTkLabel(f_inner, text="Status:", font=ctk.CTkFont(size=11, weight="bold"), text_color=palette["text_secondary"]).pack(side="left", padx=(0, 4))
        self.combo_status_filter = ctk.CTkComboBox(
            f_inner,
            values=["All Status", "Active", "Inactive"],
            width=115,
            height=32,
            command=lambda v: self._apply_filters()
        )
        self.combo_status_filter.set("All Status")
        self.combo_status_filter.pack(side="left")

        # Staff Table Container
        self.table_card = ctk.CTkFrame(self.main_scroll, fg_color=palette["bg_card"], corner_radius=10, border_width=1, border_color=palette["border"])
        self.table_card.pack(fill="both", expand=True, padx=24, pady=(0, 20))

        # Table Header
        tbl_head = ctk.CTkFrame(self.table_card, fg_color=palette["bg_secondary"], height=36, corner_radius=6)
        tbl_head.pack(fill="x", padx=10, pady=(10, 6))

        ctk.CTkLabel(tbl_head, text="STAFF MEMBER / USERNAME", font=ctk.CTkFont(size=10, weight="bold"), text_color=palette["text_secondary"], width=230, anchor="w").pack(side="left", padx=(14, 0))
        ctk.CTkLabel(tbl_head, text="ROLE", font=ctk.CTkFont(size=10, weight="bold"), text_color=palette["text_secondary"], width=90, anchor="w").pack(side="left")
        ctk.CTkLabel(tbl_head, text="ACCOUNT STATUS", font=ctk.CTkFont(size=10, weight="bold"), text_color=palette["text_secondary"], width=110, anchor="w").pack(side="left")
        ctk.CTkLabel(tbl_head, text="LAST SESSION", font=ctk.CTkFont(size=10, weight="bold"), text_color=palette["text_secondary"], width=170, anchor="w").pack(side="left")
        ctk.CTkLabel(tbl_head, text="CREATED AT", font=ctk.CTkFont(size=10, weight="bold"), text_color=palette["text_secondary"], width=100, anchor="w").pack(side="left")
        ctk.CTkLabel(tbl_head, text="ACTIONS", font=ctk.CTkFont(size=10, weight="bold"), text_color=palette["text_secondary"], width=200, anchor="e").pack(side="right", padx=(0, 14))

        # Rows Container
        self.rows_box = ctk.CTkFrame(self.table_card, fg_color="transparent")
        self.rows_box.pack(fill="both", expand=True, padx=10, pady=(0, 10))

    def _build_kpi_card(self, parent, col: int, title: str, default_val: str, subtitle: str, accent_color: str, palette: dict):
        card = ctk.CTkFrame(parent, fg_color=palette["bg_card"], corner_radius=10, border_width=1, border_color=palette["border"])
        card.grid(row=0, column=col, padx=5, sticky="nsew")

        strip = ctk.CTkFrame(card, height=4, fg_color=accent_color, corner_radius=0)
        strip.pack(fill="x")

        inner = ctk.CTkFrame(card, fg_color="transparent")
        inner.pack(fill="both", expand=True, padx=14, pady=10)

        ctk.CTkLabel(inner, text=title, font=ctk.CTkFont(size=10, weight="bold"), text_color=palette["text_secondary"]).pack(anchor="w")
        val_lbl = ctk.CTkLabel(inner, text=default_val, font=ctk.CTkFont(size=18, weight="bold"), text_color=palette.get("heading", palette["text_primary"]))
        val_lbl.pack(anchor="w", pady=(2, 2))
        ctk.CTkLabel(inner, text=subtitle, font=ctk.CTkFont(size=9), text_color=palette["text_secondary"]).pack(anchor="w")

        return val_lbl

    def refresh_users(self):
        """Loads all staff users from SQLite database."""
        self.all_users = self.user_repo.list_all()

        # Update KPIs
        total = len(self.all_users)
        active = sum(1 for u in self.all_users if u.is_active)
        inactive = total - active
        admins = sum(1 for u in self.all_users if u.role == "ADMIN")

        if hasattr(self, "lbl_kpi_total"):
            self.lbl_kpi_total.configure(text=str(total))
            self.lbl_kpi_active.configure(text=str(active))
            self.lbl_kpi_inactive.configure(text=str(inactive))
            self.lbl_kpi_admins.configure(text=str(admins))

        self._apply_filters()

    def _apply_filters(self):
        query = self.entry_search.get().strip().lower()
        role_f = self.combo_role_filter.get()
        status_f = self.combo_status_filter.get()

        filtered = []
        for u in getattr(self, "all_users", []):
            if query and (query not in u.username.lower() and query not in u.full_name.lower()):
                continue
            if role_f != "All Roles" and u.role != role_f:
                continue
            if status_f == "Active" and not u.is_active:
                continue
            if status_f == "Inactive" and u.is_active:
                continue
            filtered.append(u)

        self._render_rows(filtered)

    def _render_rows(self, users: List[User]):
        palette = theme_manager.get_palette()

        for w in self.rows_box.winfo_children():
            w.destroy()

        if not users:
            ctk.CTkLabel(
                self.rows_box,
                text="No staff members matching active filters.",
                font=ctk.CTkFont(size=12),
                text_color=palette["text_secondary"]
            ).pack(pady=30)
            return

        ROLE_COLORS = {
            "ADMIN": ("#8B5CF6", "#F5F3FF"),
            "MANAGER": ("#2563EB", "#EFF6FF"),
            "CASHIER": ("#0284C7", "#F0F9FF"),
            "CHEF": ("#2563EB", "#EFF6FF"),
            "WAITER": ("#D97706", "#FFFBEB"),
            "CUSTOMER": ("#0D9488", "#F0FDFA"),
        }

        for idx, u in enumerate(users):
            row = ctk.CTkFrame(
                self.rows_box,
                fg_color=palette["bg_card"] if idx % 2 == 0 else palette["bg_secondary"],
                corner_radius=6
            )
            row.pack(fill="x", pady=2)

            # User Info Column
            user_col = ctk.CTkFrame(row, fg_color="transparent", width=230)
            user_col.pack(side="left", padx=(14, 0), pady=8)

            ctk.CTkLabel(
                user_col,
                text=f"👤 {u.full_name}",
                font=ctk.CTkFont(size=11, weight="bold"),
                text_color=palette["text_primary"]
            ).pack(anchor="w")

            ctk.CTkLabel(
                user_col,
                text=f"Username: {u.username} (ID: #{u.id})",
                font=ctk.CTkFont(size=9),
                text_color=palette["text_secondary"]
            ).pack(anchor="w")

            # Role Badge
            border_c, bg_c = ROLE_COLORS.get(u.role, ("#64748B", "#F1F5F9"))
            badge = ctk.CTkFrame(row, fg_color=bg_c, width=85, height=22, corner_radius=10, border_width=1, border_color=border_c)
            badge.pack(side="left", padx=6)
            badge.pack_propagate(False)
            ctk.CTkLabel(badge, text=u.role, font=ctk.CTkFont(size=9, weight="bold"), text_color=border_c).place(relx=0.5, rely=0.5, anchor="center")

            # Status Pill (Account Status)
            st_color = palette["success"] if u.is_active else palette["danger"]
            st_text = "● ACTIVE" if u.is_active else "○ INACTIVE"
            ctk.CTkLabel(row, text=st_text, font=ctk.CTkFont(size=10, weight="bold"), text_color=st_color, width=110, anchor="w").pack(side="left", padx=6)

            # Last Session (Formatted timestamp from database)
            last_login_txt = u.format_last_login()
            txt_col = palette["text_secondary"] if u.last_login else palette.get("text_muted", "#64748B")
            ctk.CTkLabel(row, text=last_login_txt, font=ctk.CTkFont(size=10), text_color=txt_col, width=170, anchor="w").pack(side="left", padx=6)

            # Created timestamp
            created_str = (u.created_at or "")[:10]
            ctk.CTkLabel(row, text=created_str, font=ctk.CTkFont(size=10), text_color=palette["text_secondary"], width=100, anchor="w").pack(side="left", padx=6)

            # Actions
            act_box = ctk.CTkFrame(row, fg_color="transparent")
            act_box.pack(side="right", padx=14)

            # Edit Button
            ctk.CTkButton(
                act_box,
                text="✏️ Edit",
                width=65,
                height=26,
                font=ctk.CTkFont(size=10, weight="bold"),
                fg_color=palette["bg_card"],
                hover_color=palette["bg_secondary"],
                text_color=palette["text_primary"],
                command=lambda user=u: self._open_edit_dialog(user)
            ).pack(side="left", padx=2)

            # Reset Password Button
            ctk.CTkButton(
                act_box,
                text="🔑 Reset",
                width=68,
                height=26,
                font=ctk.CTkFont(size=10, weight="bold"),
                fg_color=palette["bg_card"],
                hover_color=palette["bg_secondary"],
                text_color=palette["accent"],
                command=lambda user=u: self._open_password_dialog(user)
            ).pack(side="left", padx=2)

            # Deactivate / Activate Toggle
            toggle_text = "🚫 Deactivate" if u.is_active else "🟢 Activate"
            toggle_color = palette["danger"] if u.is_active else palette["success"]
            ctk.CTkButton(
                act_box,
                text=toggle_text,
                width=88,
                height=26,
                font=ctk.CTkFont(size=10, weight="bold"),
                fg_color="transparent",
                hover_color=palette["bg_secondary"],
                text_color=toggle_color,
                command=lambda user=u: self._toggle_status(user)
            ).pack(side="left", padx=2)

    def _open_add_dialog(self):
        StaffDialog(self, on_saved=self.refresh_users, user=None)

    def _open_edit_dialog(self, user: User):
        StaffDialog(self, on_saved=self.refresh_users, user=user)

    def _open_password_dialog(self, user: User):
        PasswordResetDialog(self, user=user, on_reset_cb=self.refresh_users)

    def _toggle_status(self, user: User):
        new_status = not user.is_active
        # Guard: Cannot deactivate self if currently logged in as this admin
        curr = self.auth_svc.current_user
        if curr and curr.id == user.id and not new_status:
            # Alert: cannot deactivate own active session
            return
        self.user_repo.toggle_status(user.id, new_status)
        self.refresh_users()
