"""Staff Activity & Shift Log Floor Management View."""
from typing import Optional
from datetime import datetime
import customtkinter as ctk

from ui.theme_manager import theme_manager
from database.db import db
from repositories.user_repository import user_repository
from utils.logger import logger


class StaffActivityFrame(ctk.CTkFrame):
    """Floor manager interface for staff monitoring, active users, and real-time operational activity log."""

    def __init__(self, master, **kwargs):
        super().__init__(master, **kwargs)
        self.user_repo = user_repository

        theme_manager.subscribe(self.on_theme_changed)
        self._build_ui()
        self._load_data()

    def destroy(self):
        theme_manager.unsubscribe(self.on_theme_changed)
        super().destroy()

    def on_theme_changed(self, _theme: str):
        if self.winfo_exists():
            palette = theme_manager.get_palette()
            self.configure(fg_color=palette["bg_primary"])
            self._load_data()

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
            text="👥 Staff Activity & Shift Monitoring",
            font=ctk.CTkFont(size=20, weight="bold"),
            text_color=palette.get("heading", palette["text_primary"])
        ).pack(anchor="w")

        ctk.CTkLabel(
            title_box,
            text="Monitor shift personnel, account statuses, and cashier audit events across all terminals.",
            font=ctk.CTkFont(size=11),
            text_color=palette["text_secondary"]
        ).pack(anchor="w", pady=(2, 0))

        # Refresh Button
        ctk.CTkButton(
            header,
            text="🔄 Refresh Activity",
            font=ctk.CTkFont(size=11, weight="bold"),
            fg_color=palette["accent"],
            hover_color=palette["accent_hover"],
            height=32,
            width=130,
            command=self._load_data
        ).pack(side="right")

        # KPI Summary Cards
        self.kpi_container = ctk.CTkFrame(self, fg_color="transparent")
        self.kpi_container.pack(fill="x", padx=20, pady=(0, 10))

        # Main Scrollable Body
        self.main_scroll = ctk.CTkScrollableFrame(
            self,
            fg_color="transparent",
            scrollbar_button_color=palette.get("sidebar_hover", "#245A9B")
        )
        self.main_scroll.pack(fill="both", expand=True, padx=20, pady=(0, 15))

    def _load_data(self):
        palette = theme_manager.get_palette()

        # Query staff list
        try:
            users = self.user_repo.list_all()
        except Exception as e:
            logger.error(f"Error loading staff: {e}")
            users = []

        total_staff = len(users)
        active_staff = len([u for u in users if u.is_active])
        managers = len([u for u in users if u.role == "MANAGER"])
        cashiers = len([u for u in users if u.role == "CASHIER"])

        # Query audit log events count today
        today_prefix = datetime.now().strftime("%Y-%m-%d")
        try:
            today_logs_cnt = db.fetchone("SELECT COUNT(*) FROM audit_logs WHERE created_at LIKE ?;", (f"{today_prefix}%",))[0]
        except Exception:
            today_logs_cnt = 0

        # Render KPI Cards
        for w in self.kpi_container.winfo_children():
            w.destroy()

        kpi_specs = [
            ("Total Registered Staff", str(total_staff), "👥", "#3B82F6"),
            ("Active Accounts", str(active_staff), "🟢", "#10B981"),
            ("Floor Cashiers", str(cashiers), "💳", "#F59E0B"),
            ("Shift Actions Logged", str(today_logs_cnt), "📜", "#8B5CF6")
        ]

        for title, val, icon, _acc in kpi_specs:
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

        # Clear scroll content
        for w in self.main_scroll.winfo_children():
            w.destroy()

        # Section 1: Staff Directory & Status
        s1_head = ctk.CTkFrame(self.main_scroll, fg_color="transparent")
        s1_head.pack(fill="x", padx=6, pady=(0, 6))
        ctk.CTkLabel(s1_head, text="Staff Personnel Roster", font=ctk.CTkFont(size=14, weight="bold"), text_color=palette.get("heading", palette["text_primary"])).pack(side="left")

        # Staff Table Header
        tbl_head = ctk.CTkFrame(self.main_scroll, fg_color=palette["bg_secondary"], corner_radius=6, height=34)
        tbl_head.pack(fill="x", padx=6, pady=(0, 4))
        tbl_head.pack_propagate(False)

        cols = [
            ("Employee Name", 220, "w"),
            ("Username", 140, "w"),
            ("System Role", 130, "center"),
            ("Account Status", 130, "center"),
            ("Last Session", 180, "w")
        ]
        for cname, cwidth, calign in cols:
            ctk.CTkLabel(tbl_head, text=cname, font=ctk.CTkFont(size=11, weight="bold"), text_color=palette["text_secondary"], width=cwidth, anchor=calign).pack(side="left", padx=8)

        role_colors = {
            "ADMIN": ("#EEF2FF", "#4F46E5"),
            "MANAGER": ("#FFFBEB", "#D97706"),
            "CASHIER": ("#ECFDF5", "#059669")
        }

        for u in users:
            row = ctk.CTkFrame(self.main_scroll, fg_color=palette["bg_card"], corner_radius=6, border_width=1, border_color=palette["border"], height=42)
            row.pack(fill="x", padx=6, pady=2)
            row.pack_propagate(False)

            # Name with mini avatar
            name_box = ctk.CTkFrame(row, fg_color="transparent", width=220)
            name_box.pack(side="left", padx=8)
            name_box.pack_propagate(False)

            ctk.CTkLabel(name_box, text="👤", font=ctk.CTkFont(size=12)).pack(side="left", padx=(0, 6))
            ctk.CTkLabel(name_box, text=u.full_name, font=ctk.CTkFont(size=11, weight="bold"), text_color=palette["text_primary"]).pack(side="left")

            # Username
            ctk.CTkLabel(row, text=f"@{u.username}", font=ctk.CTkFont(family="Consolas", size=11), text_color=palette["text_secondary"], width=140, anchor="w").pack(side="left", padx=8)

            # Role Pill
            r_bg, r_fg = role_colors.get(u.role, ("#F1F5F9", "#475569"))
            r_box = ctk.CTkFrame(row, fg_color="transparent", width=130)
            r_box.pack(side="left", padx=8)
            r_box.pack_propagate(False)

            rp = ctk.CTkFrame(r_box, fg_color=r_bg, corner_radius=6)
            rp.pack(expand=True)
            ctk.CTkLabel(rp, text=u.role, font=ctk.CTkFont(size=9, weight="bold"), text_color=r_fg).pack(padx=8, pady=2)

            # Status Pill
            st_box = ctk.CTkFrame(row, fg_color="transparent", width=130)
            st_box.pack(side="left", padx=8)
            st_box.pack_propagate(False)

            if u.is_active:
                sp = ctk.CTkFrame(st_box, fg_color="#DCFCE7", corner_radius=6)
                sp.pack(expand=True)
                ctk.CTkLabel(sp, text="● Active", font=ctk.CTkFont(size=9, weight="bold"), text_color="#15803D").pack(padx=8, pady=2)
            else:
                sp = ctk.CTkFrame(st_box, fg_color="#FEE2E2", corner_radius=6)
                sp.pack(expand=True)
                ctk.CTkLabel(sp, text="Deactivated", font=ctk.CTkFont(size=9, weight="bold"), text_color="#B91C1C").pack(padx=8, pady=2)

            # Last Login
            last_login_txt = u.last_login if u.last_login else "Never logged in"
            ctk.CTkLabel(row, text=last_login_txt, font=ctk.CTkFont(size=10), text_color=palette["text_secondary"], width=180, anchor="w").pack(side="left", padx=8)

        # Section 2: Recent Shift Audit Feed
        s2_head = ctk.CTkFrame(self.main_scroll, fg_color="transparent")
        s2_head.pack(fill="x", padx=6, pady=(20, 6))
        ctk.CTkLabel(s2_head, text="Real-time Operational Audit Stream", font=ctk.CTkFont(size=14, weight="bold"), text_color=palette.get("heading", palette["text_primary"])).pack(side="left")

        try:
            recent_logs = db.fetchall("SELECT username, action, module, details, created_at FROM audit_logs ORDER BY id DESC LIMIT 15;")
        except Exception:
            recent_logs = []

        if not recent_logs:
            empty = ctk.CTkFrame(self.main_scroll, fg_color=palette["bg_card"], corner_radius=6, border_width=1, border_color=palette["border"])
            empty.pack(fill="x", padx=6, pady=6)
            ctk.CTkLabel(empty, text="No operational activity records logged today.", font=ctk.CTkFont(size=11), text_color=palette["text_secondary"]).pack(padx=15, pady=15)
        else:
            log_box = ctk.CTkFrame(self.main_scroll, fg_color=palette["bg_card"], corner_radius=8, border_width=1, border_color=palette["border"])
            log_box.pack(fill="x", padx=6, pady=4)

            for l in recent_logs:
                l_row = ctk.CTkFrame(log_box, fg_color="transparent")
                l_row.pack(fill="x", padx=12, pady=5)

                time_str = l["created_at"][-8:] if l["created_at"] else ""
                ctk.CTkLabel(l_row, text=f"⏱️ {time_str}", font=ctk.CTkFont(family="Consolas", size=10), text_color=palette["text_secondary"]).pack(side="left", padx=(0, 10))

                u_pill = ctk.CTkFrame(l_row, fg_color=palette["bg_secondary"], corner_radius=4)
                u_pill.pack(side="left", padx=(0, 8))
                ctk.CTkLabel(u_pill, text=f"@{l['username']}", font=ctk.CTkFont(size=10, weight="bold"), text_color=palette["accent"]).pack(padx=6, pady=1)

                m_pill = ctk.CTkFrame(l_row, fg_color="#F1F5F9", corner_radius=4)
                m_pill.pack(side="left", padx=(0, 8))
                ctk.CTkLabel(m_pill, text=l['module'], font=ctk.CTkFont(size=9, weight="bold"), text_color="#334155").pack(padx=5, pady=1)

                act_lbl = ctk.CTkLabel(l_row, text=f"{l['action']}: {l['details'] or ''}", font=ctk.CTkFont(size=11), text_color=palette["text_primary"])
                act_lbl.pack(side="left")
