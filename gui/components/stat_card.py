"""Reusable KPI stat card widget."""

import tkinter as tk
from tkinter import ttk
from gui.styles import AppTheme


class StatCard(ttk.Frame):
    """A card widget displaying a KPI metric with title, value, and status."""

    def __init__(
        self,
        parent,
        title: str,
        value: str = "--",
        subtext: str = "",
        status: str = "NEUTRAL",  # 'PASS', 'WARN', 'FAIL', 'NEUTRAL'
        **kwargs
    ):
        super().__init__(parent, style="Card.TFrame", padding=(12, 8), **kwargs)

        self.title_label = ttk.Label(self, text=title.upper(), style="CardTitle.TLabel")
        self.title_label.pack(anchor="w")

        self.value_label = ttk.Label(self, text=value, style="CardValue.TLabel")
        self.value_label.pack(anchor="w", pady=(2, 2))

        self.bottom_frame = ttk.Frame(self, style="Card.TFrame")
        self.bottom_frame.pack(fill="x", expand=True)

        self.sub_label = ttk.Label(self.bottom_frame, text=subtext, style="CardSub.TLabel")
        self.sub_label.pack(side="left")

        self.badge_label = tk.Label(
            self.bottom_frame,
            text="",
            font=("Segoe UI", 8, "bold"),
            padx=6,
            pady=1,
            relief="flat"
        )
        self.update_status(status)

    def update_data(self, value: str, subtext: str = "", status: str = "NEUTRAL") -> None:
        """Updates the card's displayed values and status."""
        self.value_label.config(text=value)
        if subtext:
            self.sub_label.config(text=subtext)
        self.update_status(status)

    def update_status(self, status: str) -> None:
        """Updates the badge color and text."""
        status = status.upper()
        if status == "PASS":
            self.badge_label.config(text="PASS", bg=AppTheme.SUCCESS_BG, fg=AppTheme.SUCCESS)
            self.badge_label.pack(side="right")
        elif status == "WARN":
            self.badge_label.config(text="WARN", bg=AppTheme.WARNING_BG, fg=AppTheme.WARNING)
            self.badge_label.pack(side="right")
        elif status == "FAIL":
            self.badge_label.config(text="FAIL", bg=AppTheme.DANGER_BG, fg=AppTheme.DANGER)
            self.badge_label.pack(side="right")
        else:
            self.badge_label.pack_forget()

