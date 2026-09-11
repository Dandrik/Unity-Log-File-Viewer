"""Main application window for Elekta Unity Log & TRF File Viewer."""

import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import sys
from typing import Optional

from gui.styles import AppTheme, configure_app_styles
from gui.components.trf_view import TRFView
from gui.components.text_log_view import TextLogView
from core.sdd_package import SDDPackage, SDDTRFEntry, SDDLogEntry
from gui.components.sdd_navigator import SDDNavigatorDialog


class UnityLogViewerApp(tk.Tk):
    """Elekta Unity MR-Linac Log & TRF Delivery QA Viewer Application."""

    def __init__(self):
        super().__init__()
        self.title("Elekta Unity MR-Linac - Log & TRF Delivery Viewer")
        self.geometry("1280x850")
        self.minsize(1024, 700)

        # Active SDD package tracking
        self.active_sdd: Optional[SDDPackage] = None
        self.sdd_dialog: Optional[SDDNavigatorDialog] = None

        # Configure styles
        self.style = configure_app_styles(self)
        self.configure(bg=AppTheme.BG_MAIN)

        self._build_menu()
        self._build_header()
        self._build_body()
        self._build_statusbar()

        # Keyboard shortcuts
        self.bind("<Control-Shift-O>", lambda e: self._menu_open_sdd())
        self.bind("<Control-Shift-o>", lambda e: self._menu_open_sdd())
        self.bind("<Control-b>", lambda e: self._menu_browse_sdd())
        self.bind("<Control-B>", lambda e: self._menu_browse_sdd())

    def _build_menu(self) -> None:
        """Constructs application menu bar."""
        menubar = tk.Menu(self)

        # File menu
        file_menu = tk.Menu(menubar, tearoff=0)
        file_menu.add_command(label="Open SDD Package (.zip / folder)...", command=self._menu_open_sdd, accelerator="Ctrl+Shift+O")
        file_menu.add_command(label="Browse Active SDD Deliveries...", command=self._menu_browse_sdd, accelerator="Ctrl+B")
        file_menu.add_separator()
        file_menu.add_command(label="Open .TRF Delivery File...", command=self._menu_open_trf, accelerator="Ctrl+O")
        file_menu.add_command(label="Open Machine Text Log...", command=self._menu_open_text_log, accelerator="Ctrl+L")
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

        btn_open_sdd = tk.Button(
            quick_box,
            text="📦 Open SDD Package (.zip)",
            bg="#0284c7",
            fg="#ffffff",
            activebackground="#0369a1",
            activeforeground="#ffffff",
            font=("Segoe UI", 9, "bold"),
            relief="flat",
            padx=12,
            pady=4,
            command=self._menu_open_sdd
        )
        btn_open_sdd.pack(side="left", padx=4)

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
    def _menu_open_sdd(self) -> None:
        """Opens file dialog for Elekta SDD (.zip) or folder."""
        filepath = filedialog.askopenfilename(
            title="Select Elekta Service Diagnostic Data (SDD) Package",
            filetypes=[
                ("SDD Packages & Zip Files", "*.zip"),
                ("All Files", "*.*")
            ]
        )
        if not filepath:
            return

        try:
            if self.active_sdd:
                self.active_sdd.close()

            self.active_sdd = SDDPackage.open(filepath)
            self.status_left.config(
                text=f"Loaded SDD [{self.active_sdd.machine_info.machine_id}]: {len(self.active_sdd.trf_entries)} TRF deliveries, {len(self.active_sdd.log_entries)} logs"
            )

            # Open Navigator Dialog
            if self.sdd_dialog and self.sdd_dialog.winfo_exists():
                self.sdd_dialog.destroy()

            self.sdd_dialog = SDDNavigatorDialog(
                self,
                self.active_sdd,
                on_load_trf=self.load_sdd_trf,
                on_load_log=self.load_sdd_log
            )
        except Exception as e:
            messagebox.showerror(
                "Error Loading SDD Package",
                f"Failed to load SDD package:\n{e}\n\nPlease verify that the file is a valid Elekta SDD archive."
            )

    def _menu_browse_sdd(self) -> None:
        """Opens or brings to front the active SDD package navigator."""
        if not self.active_sdd:
            self._menu_open_sdd()
            return

        if self.sdd_dialog and self.sdd_dialog.winfo_exists():
            self.sdd_dialog.lift()
            self.sdd_dialog.focus_force()
        else:
            self.sdd_dialog = SDDNavigatorDialog(
                self,
                self.active_sdd,
                on_load_trf=self.load_sdd_trf,
                on_load_log=self.load_sdd_log
            )

    def load_sdd_trf(self, package: SDDPackage, entry: SDDTRFEntry) -> None:
        """Decodes and loads a TRF delivery from an SDD package into the delivery analyzer."""
        try:
            dataset = package.read_trf_dataset(entry)
            self.notebook.select(0)
            source_name = f"SDD [{package.machine_info.machine_id}]: {entry.display_name} ({entry.mu:.1f} MU)"
            self.trf_view.load_dataset(dataset, source_name=source_name)
            self.status_left.config(text=f"Loaded from SDD: {entry.display_name} ({entry.mu:.1f} MU)")
        except Exception as e:
            messagebox.showerror(
                "Error Loading Delivery",
                f"Failed to decode TRF delivery '{entry.display_name}':\n{e}",
                parent=self.sdd_dialog if self.sdd_dialog and self.sdd_dialog.winfo_exists() else self
            )

    def load_sdd_log(self, package: SDDPackage, entry: SDDLogEntry) -> None:
        """Extracts and loads a machine or subsystem log from an SDD package into the log viewer."""
        try:
            log_text = package.get_log_text(entry.filename)
            self.notebook.select(1)
            source_name = f"SDD [{package.machine_info.machine_id}]: {entry.display_name}"
            self.text_log_view.load_raw_text(log_text, source_name=source_name)
            self.status_left.config(text=f"Loaded Log from SDD: {entry.display_name}")
        except Exception as e:
            messagebox.showerror(
                "Error Loading Log",
                f"Failed to read log '{entry.display_name}':\n{e}",
                parent=self.sdd_dialog if self.sdd_dialog and self.sdd_dialog.winfo_exists() else self
            )

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

