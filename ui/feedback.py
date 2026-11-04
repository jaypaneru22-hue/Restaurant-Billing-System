"""Customer Feedback & Dining Guest Satisfaction Module (Q08)."""
from typing import Optional
from datetime import datetime
import customtkinter as ctk

from ui.theme_manager import theme_manager
from database.db import db
from utils.window_utils import center_dialog
from utils.logger import logger


class FeedbackRecordDialog(ctk.CTkToplevel):
    """Modal dialog for floor staff or manager to capture guest feedback directly."""

    def __init__(self, master, on_saved, **kwargs):
        super().__init__(master, **kwargs)
        self.on_saved = on_saved
        self.title("Record Guest Feedback (Q08)")
        self.resizable(False, False)
        center_dialog(self, master, target_width=440, target_height=420, min_width=420, min_height=400)
        self.grab_set()

        palette = theme_manager.get_palette()
        self.configure(fg_color=palette["bg_primary"])

        ctk.CTkLabel(
            self,
            text="⭐ Record Guest Dining Feedback",
            font=ctk.CTkFont(size=16, weight="bold"),
            text_color=palette.get("heading", palette["text_primary"])
        ).pack(padx=20, pady=(15, 4), anchor="w")

        ctk.CTkLabel(
            self,
            text="Capture diner rating and quality impressions for continuous restaurant improvement.",
            font=ctk.CTkFont(size=10),
            text_color=palette["text_secondary"]
        ).pack(padx=20, pady=(0, 12), anchor="w")

        card = ctk.CTkFrame(self, fg_color=palette["bg_card"], corner_radius=8, border_width=1, border_color=palette["border"])
        card.pack(fill="both", expand=True, padx=20, pady=(0, 15))

        # Customer Name
        ctk.CTkLabel(card, text="Guest / Customer Name", font=ctk.CTkFont(size=11, weight="bold"), text_color=palette["text_primary"]).pack(padx=14, pady=(10, 2), anchor="w")
        self.name_entry = ctk.CTkEntry(card, height=32, placeholder_text="e.g. Mr. Rajesh Sharma", border_color=palette["border"])
        self.name_entry.pack(fill="x", padx=14, pady=(0, 8))

        # Table Number
        ctk.CTkLabel(card, text="Table Number / Order Type", font=ctk.CTkFont(size=11, weight="bold"), text_color=palette["text_primary"]).pack(padx=14, pady=(0, 2), anchor="w")
        self.table_entry = ctk.CTkEntry(card, height=32, placeholder_text="e.g. Table 4 or Takeaway", border_color=palette["border"])
        self.table_entry.pack(fill="x", padx=14, pady=(0, 8))

        # Rating Selector
        ctk.CTkLabel(card, text="Experience Rating (1 to 5 Stars)", font=ctk.CTkFont(size=11, weight="bold"), text_color=palette["text_primary"]).pack(padx=14, pady=(0, 2), anchor="w")
        self.rating_var = ctk.StringVar(value="5 - Exceptional (⭐⭐⭐⭐⭐)")
        rating_menu = ctk.CTkOptionMenu(
            card,
            variable=self.rating_var,
            values=[
                "5 - Exceptional (⭐⭐⭐⭐⭐)",
                "4 - Very Good (⭐⭐⭐⭐)",
                "3 - Average (⭐⭐⭐)",
                "2 - Needs Improvement (⭐⭐)",
                "1 - Unsatisfactory (⭐)"
            ],
            height=32,
            fg_color=palette["bg_secondary"],
            text_color=palette["text_primary"],
            button_color=palette["accent"]
        )
        rating_menu.pack(fill="x", padx=14, pady=(0, 8))

        # Comment Text
        ctk.CTkLabel(card, text="Guest Comments / Food Feedback", font=ctk.CTkFont(size=11, weight="bold"), text_color=palette["text_primary"]).pack(padx=14, pady=(0, 2), anchor="w")
        self.comment_box = ctk.CTkTextbox(card, height=70, border_width=1, border_color=palette["border"])
        self.comment_box.pack(fill="x", padx=14, pady=(0, 8))

        # Action Buttons
        btn_row = ctk.CTkFrame(self, fg_color="transparent")
        btn_row.pack(fill="x", padx=20, pady=(0, 15))

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
            text="💾 Save Feedback",
            width=130,
            height=32,
            font=ctk.CTkFont(size=11, weight="bold"),
            fg_color=palette["accent"],
            hover_color=palette["accent_hover"],
            command=self._handle_save
        ).pack(side="right")

    def _handle_save(self):
        cname = self.name_entry.get().strip() or "Valued Guest"
        tbl = self.table_entry.get().strip() or "Dining Hall"
        rating_val = int(self.rating_var.get()[0])
        comments = self.comment_box.get("1.0", "end").strip()

        try:
            db.execute(
                """INSERT INTO customer_feedback (customer_name, table_number, rating, comment)
                   VALUES (?, ?, ?, ?);""",
                (cname, tbl, rating_val, comments)
            )
            db.execute(
                """INSERT INTO audit_logs (username, action, module, details)
                   VALUES ('Floor', 'RECORD_FEEDBACK', 'CUSTOMER_SATISFACTION', ?);""",
                (f"Recorded {rating_val}-star feedback from {cname} at {tbl}",)
            )
            self.on_saved()
            self.destroy()
        except Exception as e:
            logger.error(f"Error saving feedback: {e}")


class CustomerFeedbackFrame(ctk.CTkFrame):
    """Floor manager interface for tracking guest reviews, rating analytics, and customer satisfaction (Q08)."""

    def __init__(self, master, **kwargs):
        super().__init__(master, **kwargs)
        self.filter_stars = 0

        theme_manager.subscribe(self.on_theme_changed)
        self._build_ui()
        self._load_feedbacks()

    def destroy(self):
        theme_manager.unsubscribe(self.on_theme_changed)
        super().destroy()

    def on_theme_changed(self, _theme: str):
        if self.winfo_exists():
            palette = theme_manager.get_palette()
            self.configure(fg_color=palette["bg_primary"])
            self._load_feedbacks()

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
            text="⭐ Guest Feedback & Dining Satisfaction",
            font=ctk.CTkFont(size=20, weight="bold"),
            text_color=palette.get("heading", palette["text_primary"])
        ).pack(anchor="w")

        ctk.CTkLabel(
            title_box,
            text="Quality Goal Q08: Direct guest feedback, service quality indices, and dining sentiment tracking.",
            font=ctk.CTkFont(size=11),
            text_color=palette["text_secondary"]
        ).pack(anchor="w", pady=(2, 0))

        # Add Feedback Button
        ctk.CTkButton(
            header,
            text="➕ Record Guest Review",
            font=ctk.CTkFont(size=11, weight="bold"),
            fg_color=palette["accent"],
            hover_color=palette["accent_hover"],
            height=32,
            width=160,
            command=self._open_record_dialog
        ).pack(side="right")

        # KPI Summary Cards
        self.kpi_container = ctk.CTkFrame(self, fg_color="transparent")
        self.kpi_container.pack(fill="x", padx=20, pady=(0, 10))

        # Star Rating Filters Bar
        self.filter_bar = ctk.CTkFrame(self, fg_color="transparent")
        self.filter_bar.pack(fill="x", padx=20, pady=(0, 10))

        # Scrollable Reviews List
        self.scroll_container = ctk.CTkScrollableFrame(
            self,
            fg_color="transparent",
            scrollbar_button_color=palette.get("sidebar_hover", "#245A9B")
        )
        self.scroll_container.pack(fill="both", expand=True, padx=20, pady=(0, 15))

    def _open_record_dialog(self):
        FeedbackRecordDialog(self, on_saved=self._load_feedbacks)

    def _load_feedbacks(self):
        try:
            feedbacks = db.fetchall("SELECT id, customer_name, table_number, rating, comment, created_at FROM customer_feedback ORDER BY id DESC;")
        except Exception as e:
            logger.error(f"Error loading feedbacks: {e}")
            feedbacks = []

        self.all_feedbacks = feedbacks
        total_rev = len(feedbacks)
        avg_score_str = f"⭐ {sum(f['rating'] for f in feedbacks) / total_rev:.2f} / 5.0" if total_rev > 0 else "No reviews yet"
        five_star_cnt = len([f for f in feedbacks if f["rating"] == 5])
        csat_str = f"{(len([f for f in feedbacks if f['rating'] >= 4]) / total_rev * 100):.1f}% Positive" if total_rev > 0 else "0% (No data)"

        palette = theme_manager.get_palette()
        for w in self.kpi_container.winfo_children():
            w.destroy()

        kpi_specs = [
            ("Average Guest Rating", avg_score_str, "🌟", "#F59E0B"),
            ("Total Reviews Logged", str(total_rev), "📝", "#3B82F6"),
            ("5-Star Ratings", f"{five_star_cnt} reviews", "💎", "#10B981"),
            ("CSAT Satisfaction (Q08)", csat_str, "🎯", "#8B5CF6")
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

        # Render Filter Buttons
        for w in self.filter_bar.winfo_children():
            w.destroy()

        filter_options = [
            (0, f"All Reviews ({total_rev})"),
            (5, f"⭐⭐⭐⭐⭐ ({five_star_cnt})"),
            (4, f"⭐⭐⭐⭐ ({len([f for f in feedbacks if f['rating'] == 4])})"),
            (3, f"⭐⭐⭐ ({len([f for f in feedbacks if f['rating'] == 3])})"),
        ]

        for s_val, s_lbl in filter_options:
            is_active = (self.filter_stars == s_val)
            ctk.CTkButton(
                self.filter_bar,
                text=s_lbl,
                font=ctk.CTkFont(size=11, weight="bold"),
                height=30,
                fg_color=palette["accent"] if is_active else palette["bg_card"],
                text_color="#FFFFFF" if is_active else palette["text_secondary"],
                border_width=1,
                border_color=palette["border"],
                command=lambda sv=s_val: self._set_star_filter(sv)
            ).pack(side="left", padx=4)

        self._render_reviews_list()

    def _set_star_filter(self, s_val: int):
        self.filter_stars = s_val
        self._load_feedbacks()

    def _render_reviews_list(self):
        palette = theme_manager.get_palette()
        for w in self.scroll_container.winfo_children():
            w.destroy()

        filtered = [f for f in self.all_feedbacks if (self.filter_stars == 0 or f["rating"] == self.filter_stars)]

        if not filtered:
            empty = ctk.CTkFrame(self.scroll_container, fg_color=palette["bg_card"], corner_radius=8, border_width=1, border_color=palette["border"])
            empty.pack(fill="x", padx=6, pady=20)
            ctk.CTkLabel(empty, text="No feedback records found matching this star rating filter.", font=ctk.CTkFont(size=12), text_color=palette["text_secondary"]).pack(padx=20, pady=20)
            return

        for fb in filtered:
            card = ctk.CTkFrame(self.scroll_container, fg_color=palette["bg_card"], corner_radius=8, border_width=1, border_color=palette["border"])
            card.pack(fill="x", padx=6, pady=4)

            top_row = ctk.CTkFrame(card, fg_color="transparent")
            top_row.pack(fill="x", padx=14, pady=(10, 4))

            # Guest Name & Table
            ctk.CTkLabel(
                top_row,
                text=f"👤 {fb['customer_name']}",
                font=ctk.CTkFont(size=12, weight="bold"),
                text_color=palette.get("heading", palette["text_primary"])
            ).pack(side="left")

            t_pill = ctk.CTkFrame(top_row, fg_color=palette["bg_secondary"], corner_radius=4)
            t_pill.pack(side="left", padx=10)
            ctk.CTkLabel(t_pill, text=fb["table_number"] or "Dine-in", font=ctk.CTkFont(size=10, weight="bold"), text_color=palette["accent"]).pack(padx=6, pady=2)

            # Rating Stars
            stars_text = "⭐" * fb["rating"]
            ctk.CTkLabel(top_row, text=stars_text, font=ctk.CTkFont(size=13)).pack(side="right")

            # Comment Text
            ctk.CTkLabel(
                card,
                text=f"\"{fb['comment']}\"",
                font=ctk.CTkFont(size=11, slant="italic"),
                text_color=palette["text_primary"],
                wraplength=800,
                justify="left"
            ).pack(anchor="w", padx=14, pady=(0, 6))

            # Date stamp
            date_str = fb["created_at"] or ""
            ctk.CTkLabel(
                card,
                text=f"Recorded: {date_str}",
                font=ctk.CTkFont(size=9),
                text_color=palette["text_secondary"]
            ).pack(anchor="w", padx=14, pady=(0, 8))
