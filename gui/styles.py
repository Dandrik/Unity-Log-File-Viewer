"""Styles and color theme definitions for Elekta Unity Log File Viewer."""

import tkinter as tk
from tkinter import ttk


class AppTheme:
    """Color palette and visual constants."""
    # Backgrounds
    BG_MAIN = "#f8fafc"         # Slate-50
    BG_CARD = "#ffffff"         # White
    BG_HEADER = "#0f172a"       # Slate-900
    BG_SIDEBAR = "#f1f5f9"      # Slate-100
    BG_HOVER = "#e2e8f0"        # Slate-200

    # Text colors
    TEXT_PRIMARY = "#0f172a"    # Slate-900
    TEXT_SECONDARY = "#64748b"  # Slate-500
    TEXT_LIGHT = "#ffffff"
    TEXT_MUTED = "#94a3b8"

    # Status / Accent colors
    PRIMARY = "#0284c7"         # Sky-600
    PRIMARY_HOVER = "#0369a1"   # Sky-700
    SUCCESS = "#16a34a"         # Green-600
    SUCCESS_BG = "#dcfce7"      # Green-100
    WARNING = "#d97706"         # Amber-600
    WARNING_BG = "#fef3c7"      # Amber-100
    DANGER = "#dc2626"          # Red-600
    DANGER_BG = "#fee2e2"       # Red-100
    INFO = "#3b82f6"            # Blue-500

    # MLC Colors
    MLC_Y1 = "#2563eb"          # Deep Blue (Bank Y1)
    MLC_Y2 = "#0891b2"          # Cyan / Teal (Bank Y2)
    MLC_APERTURE = "#fef08a"    # Soft Warm Gold (Open beam aperture)
    MLC_JAW = "#334155"         # Slate-700
    MLC_CROSSHAIR = "#94a3b8"   # Slate-400
    MLC_ERROR_WARN = "#f59e0b"  # Amber
    MLC_ERROR_FAIL = "#ef4444"  # Red

    # Fonts
    FONT_FAMILY = "Segoe UI"
    FONT_HEADER = ("Segoe UI", 13, "bold")
    FONT_TITLE = ("Segoe UI", 11, "bold")
    FONT_BODY = ("Segoe UI", 9)
    FONT_BODY_BOLD = ("Segoe UI", 9, "bold")
    FONT_SMALL = ("Segoe UI", 8)
    FONT_MONO = ("Consolas", 9)
    FONT_MONO_BOLD = ("Consolas", 9, "bold")


def configure_app_styles(root: tk.Tk) -> ttk.Style:
    """Configures global ttk styles."""
    style = ttk.Style(root)

    # Use 'clam' or 'vista' engine as base
    available_themes = style.theme_names()
    if "clam" in available_themes:
        style.theme_use("clam")

    # General Frames and Labels
    style.configure(".", background=AppTheme.BG_MAIN, font=AppTheme.FONT_BODY)
    style.configure("TFrame", background=AppTheme.BG_MAIN)
    style.configure("Card.TFrame", background=AppTheme.BG_CARD, relief="ridge", borderwidth=1)
    style.configure("Header.TFrame", background=AppTheme.BG_HEADER)

    # Labels
    style.configure("TLabel", background=AppTheme.BG_MAIN, foreground=AppTheme.TEXT_PRIMARY)
    style.configure("HeaderTitle.TLabel", background=AppTheme.BG_HEADER, foreground=AppTheme.TEXT_LIGHT, font=("Segoe UI", 13, "bold"))
    style.configure("HeaderSubtitle.TLabel", background=AppTheme.BG_HEADER, foreground=AppTheme.TEXT_MUTED, font=("Segoe UI", 9))
    style.configure("CardTitle.TLabel", background=AppTheme.BG_CARD, foreground=AppTheme.TEXT_SECONDARY, font=AppTheme.FONT_TITLE)
    style.configure("CardValue.TLabel", background=AppTheme.BG_CARD, foreground=AppTheme.TEXT_PRIMARY, font=("Segoe UI", 15, "bold"))
    style.configure("CardSub.TLabel", background=AppTheme.BG_CARD, foreground=AppTheme.TEXT_SECONDARY, font=AppTheme.FONT_SMALL)

    # Buttons
    style.configure(
        "Primary.TButton",
        background=AppTheme.PRIMARY,
        foreground=AppTheme.TEXT_LIGHT,
        font=AppTheme.FONT_BODY_BOLD,
        borderwidth=0,
        padding=(10, 5)
    )
    style.map(
        "Primary.TButton",
        background=[("active", AppTheme.PRIMARY_HOVER), ("disabled", AppTheme.BG_HOVER)],
        foreground=[("disabled", AppTheme.TEXT_MUTED)]
    )

    style.configure(
        "Secondary.TButton",
        background=AppTheme.BG_CARD,
        foreground=AppTheme.TEXT_PRIMARY,
        font=AppTheme.FONT_BODY,
        borderwidth=1,
        relief="solid",
        padding=(8, 4)
    )
    style.map(
        "Secondary.TButton",
        background=[("active", AppTheme.BG_HOVER)]
    )

    # Notebook
    style.configure("TNotebook", background=AppTheme.BG_MAIN, borderwidth=0)
    style.configure("TNotebook.Tab", background=AppTheme.BG_SIDEBAR, foreground=AppTheme.TEXT_PRIMARY, font=AppTheme.FONT_BODY_BOLD, padding=(14, 7))
    style.map(
        "TNotebook.Tab",
        background=[("selected", AppTheme.BG_CARD), ("active", AppTheme.BG_HOVER)],
        foreground=[("selected", AppTheme.PRIMARY)]
    )

    # Treeview (Tables)
    style.configure(
        "Treeview",
        background=AppTheme.BG_CARD,
        foreground=AppTheme.TEXT_PRIMARY,
        fieldbackground=AppTheme.BG_CARD,
        font=AppTheme.FONT_BODY,
        rowheight=24
    )
    style.configure(
        "Treeview.Heading",
        background=AppTheme.BG_SIDEBAR,
        foreground=AppTheme.TEXT_PRIMARY,
        font=AppTheme.FONT_BODY_BOLD,
        padding=(6, 4)
    )
    style.map("Treeview", background=[("selected", "#bae6fd")], foreground=[("selected", AppTheme.TEXT_PRIMARY)])

    return style

