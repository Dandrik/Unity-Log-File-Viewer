"""Main application window for Elekta Unity Log & TRF File Viewer."""

import tkinter as tk
from tkinter import ttk, messagebox
import sys

from gui.styles import AppTheme, configure_app_styles
from gui.components.trf_view import TRFView
from gui.components.text_log_view import TextLogView


class UnityLogViewerApp(tk.Tk):
    """Elekta Unity MR-Linac Log & TRF Delivery QA Viewer Application."""

    def __init__(self):
        super().__init__()
        self.title("Elekta Unity MR-Linac - Log & TRF Delivery Viewer")
        self.geometry("1280x850")
        self.minsize(1024, 700)

        # Configure styles
        self.style = configure_app_styles(self)
        self.configure(bg=AppTheme.BG_MAIN)

        self._build_menu()
        self._build_header()
        self._build_body()
        self._build_statusbar()

    def _build_menu(self) -> None:
        """Constructs application menu bar."""
        menubar = tk.Menu(self)

        # File menu
        file_menu = tk.Menu(menubar, tearoff=0)
        file_menu.add_command(label="Open .TRF Delivery File...", command=self._menu_open_trf)
        file_menu.add_command(label="Open Machine Text Log...", command=self._menu_open_text_log)
        file_menu.add_separator()
        file_menu.add_command(label="Load Sample TRF Delivery", command=self._menu_sample_trf)
        file_menu.add_command(label="Load Sample Text Log", command=self._menu_sample_text_log)
        file_menu.add_separator()
        file_menu.add_command(label="Exit", command=self.quit)
        menubar.add_cascade(label="File", menu=file_menu)

        # View menu
        view_menu = tk.Menu(menubar, tearoff=0)
        view_menu.add_command(label="TRF Delivery & MLC Viewer", command=lambda: self.notebook.select(0))
        view_menu.add_command(label="Machine Event & Text Logs", command=lambda: self.notebook.select(1))
        menubar.add_cascade(label="View", menu=view_menu)

        # Help menu
        help_menu = tk.Menu(menubar, tearoff=0)
        help_menu.add_command(label="About", command=self._show_about)
        menubar.add_cascade(label="Help", menu=help_menu)

        self.config(menu=menubar)

    def _build_header(self) -> None:
        """Constructs modern top banner."""
        self.header_frame = ttk.Frame(self, style="Header.TFrame", padding=(16, 10))
        self.header_frame.pack(fill="x")

        # Left title & subtitle
        title_box = ttk.Frame(self.header_frame, style="Header.TFrame")
        title_box.pack(side="left")

        lbl_title = ttk.Label(
            title_box,
            text="ELEKTA UNITY MR-LINAC",
            style="HeaderTitle.TLabel"
        )
        lbl_title.pack(anchor="w")

        lbl_sub = ttk.Label(
            title_box,
            text="Log & TRF Delivery QA Analyzer (Agility 160-Leaf MLC • Gantry • Interlocks)",
            style="HeaderSubtitle.TLabel"
        )
        lbl_sub.pack(anchor="w")

        # Right quick sample launch buttons
        quick_box = ttk.Frame(self.header_frame, style="Header.TFrame")
        quick_box.pack(side="right")

        btn_demo_trf = tk.Button(
            quick_box,
            text="▶ Try Sample TRF",
            bg=AppTheme.PRIMARY,
            fg="#ffffff",
            activebackground=AppTheme.PRIMARY_HOVER,
            activeforeground="#ffffff",
            font=("Segoe UI", 9, "bold"),
            relief="flat",
            padx=10,
            pady=4,
            command=self._menu_sample_trf
        )
        btn_demo_trf.pack(side="left", padx=4)

        btn_demo_log = tk.Button(
            quick_box,
            text="▶ Try Sample Log",
            bg="#334155",
            fg="#ffffff",
            activebackground="#475569",
            activeforeground="#ffffff",
            font=("Segoe UI", 9, "bold"),
            relief="flat",
            padx=10,
            pady=4,
            command=self._menu_sample_text_log
        )
        btn_demo_log.pack(side="left", padx=4)

    def _build_body(self) -> None:
        """Constructs main tabbed view."""
        self.notebook = ttk.Notebook(self)
        self.notebook.pack(fill="both", expand=True, padx=6, pady=6)

        # Tab 1: TRF Delivery Analyzer
        self.trf_view = TRFView(self.notebook)
        self.notebook.add(self.trf_view, text="  🎯  TRF Delivery & MLC Analyzer  ")

        # Tab 2: Machine Text Log Viewer
        self.text_log_view = TextLogView(self.notebook)
        self.notebook.add(self.text_log_view, text="  📋  Machine Event & Text Logs  ")

    def _build_statusbar(self) -> None:
        """Constructs bottom status bar."""
        self.statusbar = ttk.Frame(self, relief="sunken", padding=(8, 3))
        self.statusbar.pack(fill="x", side="bottom")

        self.status_left = ttk.Label(self.statusbar, text="Ready", font=AppTheme.FONT_SMALL)
        self.status_left.pack(side="left")

        py_ver = f"Python {sys.version.split()[0]}"
        self.status_right = ttk.Label(
            self.statusbar,
            text=f"Agility MLC 80-pairs | 25 Hz TRF Support | {py_ver}",
            font=AppTheme.FONT_SMALL,
            foreground=AppTheme.TEXT_SECONDARY
        )
        self.status_right.pack(side="right")

    # Menu Callbacks
    def _menu_open_trf(self) -> None:
        self.notebook.select(0)
        self.trf_view.open_trf_file()

    def _menu_open_text_log(self) -> None:
        self.notebook.select(1)
        self.text_log_view.open_log_file()

    def _menu_sample_trf(self) -> None:
        self.notebook.select(0)
        self.trf_view.load_sample_data()
        self.status_left.config(text="Loaded: Synthetic Elekta Unity VMAT delivery")

    def _menu_sample_text_log(self) -> None:
        self.notebook.select(1)
        self.text_log_view.load_sample_log()
        self.status_left.config(text="Loaded: Sample Elekta Unity Machine Event Log")

    def _show_about(self) -> None:
        messagebox.showinfo(
            "About Elekta Unity Log Viewer",
            "Elekta Unity MR-Linac Log & TRF File Viewer\n\n"
            "Features:\n"
            "• Agility 160-leaf MLC Beam's Eye View (BEV) animation\n"
            "• Gantry position trajectory and error analysis\n"
            "• 2D leaf error heatmaps and RMS error profiles\n"
            "• Elekta service and subsystem event log viewer\n"
            "• Real-time regex search, level filtering, and CSV export\n\n"
            "Elekta Radiotherapy & MR-Linac Support Tool"
        )

