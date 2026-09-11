"""SDD (Service Diagnostic Data) Package Navigator Window.

Provides a modern interactive browser for browsing, filtering, and loading
TRF treatment delivery logs, machine subsystem event logs, and hardware manifests
directly from Elekta Unity SDD packages.
"""

import os
import tkinter as tk
from tkinter import ttk, messagebox
from typing import Callable, List, Optional

from core.sdd_package import SDDPackage, SDDTRFEntry, SDDLogEntry
from gui.styles import AppTheme


class SDDNavigatorDialog(tk.Toplevel):
    """Modeless navigation dialog for browsing and loading files from an SDD package."""

    def __init__(
        self,
        parent: tk.Misc,
        package: SDDPackage,
        on_load_trf: Callable[[SDDPackage, SDDTRFEntry], None],
        on_load_log: Optional[Callable[[SDDPackage, SDDLogEntry], None]] = None
    ):
        super().__init__(parent)
        self.package = package
        self.on_load_trf = on_load_trf
        self.on_load_log = on_load_log

        machine = self.package.machine_info.machine_id
        self.title(f"Elekta SDD Package Navigator — {machine}")
        self.geometry("980x660")
        self.minsize(760, 480)
        self.configure(bg=AppTheme.BG_MAIN)

        # Bring window to front
        self.lift()
        self.focus_force()

        # State tracking for sort directions
        self._sort_directions = {}

        self._build_header()
        self._build_tabs()
        self._build_footer()

    # -------------------------------------------------------------------------
    # UI Construction
    # -------------------------------------------------------------------------

    def _build_header(self) -> None:
        """Builds top package information banner."""
        header = tk.Frame(self, bg="#131d35", padx=16, pady=12, highlightbackground="#334155", highlightthickness=1)
        header.pack(fill="x", padx=10, pady=(10, 6))

        # Title row
        top_row = tk.Frame(header, bg="#131d35")
        top_row.pack(fill="x")

        lbl_pkg = tk.Label(
            top_row,
            text=f"📦 {self.package.name}",
            bg="#131d35",
            fg="#f8fafc",
            font=("Segoe UI", 12, "bold"),
            anchor="w"
        )
        lbl_pkg.pack(side="left")

        # Badges row
        badge_row = tk.Frame(header, bg="#131d35")
        badge_row.pack(fill="x", pady=(6, 0))

        # Machine ID badge
        m_id = self.package.machine_info.machine_id
        b_mach = tk.Label(
            badge_row,
            text=f"Linac: {m_id}",
            bg="#0369a1",
            fg="#ffffff",
            font=("Segoe UI", 9, "bold"),
            padx=8,
            pady=2
        )
        b_mach.pack(side="left", padx=(0, 6))

        # Export Date badge
        exp_ts = self.package.machine_info.export_timestamp or "Unknown Date"
        b_date = tk.Label(
            badge_row,
            text=f"Exported: {exp_ts}",
            bg="#b45309",
            fg="#ffffff",
            font=("Segoe UI", 9, "bold"),
            padx=8,
            pady=2
        )
        b_date.pack(side="left", padx=6)

        # TRF count badge
        num_trfs = len(self.package.trf_entries)
        b_trf = tk.Label(
            badge_row,
            text=f"🎯 {num_trfs} TRF Deliveries",
            bg="#047857",
            fg="#ffffff",
            font=("Segoe UI", 9, "bold"),
            padx=8,
            pady=2
        )
        b_trf.pack(side="left", padx=6)

        # Log count badge
        num_logs = len(self.package.log_entries)
        b_log = tk.Label(
            badge_row,
            text=f"📋 {num_logs} Subsystem Logs",
            bg="#334155",
            fg="#cbd5e1",
            font=("Segoe UI", 9, "bold"),
            padx=8,
            pady=2
        )
        b_log.pack(side="left", padx=6)

    def _build_tabs(self) -> None:
        """Constructs tabbed notebook containing Deliveries, Logs, and Manifest."""
        self.notebook = ttk.Notebook(self)
        self.notebook.pack(fill="both", expand=True, padx=10, pady=4)

        # Tab 1: TRF Deliveries
        tab_trf = ttk.Frame(self.notebook, padding=6)
        self.notebook.add(tab_trf, text=f"  🎯  Treatment Deliveries ({len(self.package.trf_entries)})  ")
        self._build_trf_tab(tab_trf)

        # Tab 2: Machine Logs
        tab_log = ttk.Frame(self.notebook, padding=6)
        self.notebook.add(tab_log, text=f"  📋  Subsystem Logs ({len(self.package.log_entries)})  ")
        self._build_log_tab(tab_log)

        # Tab 3: Machine Info & Manifest
        tab_info = ttk.Frame(self.notebook, padding=6)
        self.notebook.add(tab_info, text="  ℹ️  Machine Info & Manifest  ")
        self._build_manifest_tab(tab_info)

    # -------------------------------------------------------------------------
    # Tab 1: TRF Deliveries
    # -------------------------------------------------------------------------

    def _build_trf_tab(self, parent: ttk.Frame) -> None:
        """Builds TRF deliveries browser with filtering, search, and action buttons."""
        # Filter Bar
        filt_frame = tk.Frame(parent, bg=AppTheme.BG_CARD, padx=8, pady=6, highlightbackground="#334155", highlightthickness=1)
        filt_frame.pack(fill="x", pady=(0, 6))

        # Search box
        tk.Label(filt_frame, text="Search:", bg=AppTheme.BG_CARD, fg=AppTheme.TEXT_SECONDARY, font=AppTheme.FONT_BODY_BOLD).pack(side="left", padx=(0, 4))
        self.trf_search_var = tk.StringVar()
        self.trf_search_var.trace_add("write", lambda *args: self._apply_trf_filters())
        search_entry = ttk.Entry(filt_frame, textvariable=self.trf_search_var, width=22)
        search_entry.pack(side="left", padx=(0, 14))

        # Category Filter
        tk.Label(filt_frame, text="Category:", bg=AppTheme.BG_CARD, fg=AppTheme.TEXT_SECONDARY, font=AppTheme.FONT_BODY_BOLD).pack(side="left", padx=(0, 4))
        self.trf_cat_var = tk.StringVar(value="All")
        self.trf_cat_combo = ttk.Combobox(
            filt_frame,
            textvariable=self.trf_cat_var,
            values=["All", "Clinical Treatment", "Daily QA", "Warmup", "Shape / Test"],
            state="readonly",
            width=18
        )
        self.trf_cat_combo.pack(side="left", padx=(0, 14))
        self.trf_cat_combo.bind("<<ComboboxSelected>>", lambda e: self._apply_trf_filters())

        # Reset button
        btn_reset = ttk.Button(filt_frame, text="Reset", command=self._reset_trf_filters, width=7)
        btn_reset.pack(side="left")

        # Stats label
        self.lbl_trf_count = tk.Label(filt_frame, text="", bg=AppTheme.BG_CARD, fg="#38bdf8", font=AppTheme.FONT_SMALL)
        self.lbl_trf_count.pack(side="right", padx=6)

        # Treeview Table
        tree_frame = ttk.Frame(parent)
        tree_frame.pack(fill="both", expand=True)

        columns = ("date", "field", "category", "mu", "size", "filename")
        self.tree_trf = ttk.Treeview(
            tree_frame,
            columns=columns,
            show="headings",
            selectmode="browse"
        )

        self.tree_trf.heading("date", text="Delivery Date & Time", command=lambda: self._sort_trf_col("date"))
        self.tree_trf.heading("field", text="Plan / Field Name", command=lambda: self._sort_trf_col("field"))
        self.tree_trf.heading("category", text="Category", command=lambda: self._sort_trf_col("category"))
        self.tree_trf.heading("mu", text="Delivered MU", command=lambda: self._sort_trf_col("mu"))
        self.tree_trf.heading("size", text="Size (MB)", command=lambda: self._sort_trf_col("size"))
        self.tree_trf.heading("filename", text="TRF Filename", command=lambda: self._sort_trf_col("filename"))

        self.tree_trf.column("date", width=170, anchor="w")
        self.tree_trf.column("field", width=130, anchor="w")
        self.tree_trf.column("category", width=140, anchor="w")
        self.tree_trf.column("mu", width=110, anchor="e")
        self.tree_trf.column("size", width=90, anchor="e")
        self.tree_trf.column("filename", width=280, anchor="w")

        # Scrollbars
        scroll_y = ttk.Scrollbar(tree_frame, orient="vertical", command=self.tree_trf.yview)
        scroll_x = ttk.Scrollbar(tree_frame, orient="horizontal", command=self.tree_trf.xview)
        self.tree_trf.configure(yscrollcommand=scroll_y.set, xscrollcommand=scroll_x.set)

        self.tree_trf.grid(row=0, column=0, sticky="nsew")
        scroll_y.grid(row=0, column=1, sticky="ns")
        scroll_x.grid(row=1, column=0, sticky="ew")

        tree_frame.columnconfigure(0, weight=1)
        tree_frame.rowconfigure(0, weight=1)

        # Bindings
        self.tree_trf.bind("<Double-1>", lambda e: self._on_load_selected_trf())
        self.tree_trf.bind("<Return>", lambda e: self._on_load_selected_trf())

        # Tag styles for categories (high-contrast against white table background)
        self.tree_trf.tag_configure("clinical", foreground=AppTheme.TEXT_PRIMARY)
        self.tree_trf.tag_configure("qa", foreground="#0369a1")
        self.tree_trf.tag_configure("warmup", foreground="#b45309")
        self.tree_trf.tag_configure("shape", foreground="#6d28d9")

        # Initial populate
        self._apply_trf_filters()

    def _apply_trf_filters(self) -> None:
        """Filters and populates the TRF treeview."""
        self.tree_trf.delete(*self.tree_trf.get_children())
        query = self.trf_search_var.get().strip().upper()
        cat_filter = self.trf_cat_var.get()

        visible_count = 0
        for entry in self.package.trf_entries:
            # Filter by category
            if cat_filter != "All" and entry.category != cat_filter:
                continue

            # Filter by search term (filename, field, date)
            if query:
                combined = f"{entry.display_name} {entry.field_name} {entry.date} {entry.time} {entry.category}".upper()
                if query not in combined:
                    continue

            # Tag determination
            if entry.category == "Daily QA":
                tag = "qa"
            elif entry.category == "Warmup":
                tag = "warmup"
            elif entry.category == "Shape / Test":
                tag = "shape"
            else:
                tag = "clinical"

            sz_mb = entry.file_size / (1024 * 1024)
            ts_str = f"{entry.date} {entry.time}".strip()

            self.tree_trf.insert(
                "",
                "end",
                iid=entry.filename,
                values=(
                    ts_str,
                    entry.field_name,
                    entry.category,
                    f"{entry.mu:.1f} MU",
                    f"{sz_mb:.2f} MB",
                    entry.display_name
                ),
                tags=(tag,)
            )
            visible_count += 1

        total = len(self.package.trf_entries)
        self.lbl_trf_count.config(text=f"Showing {visible_count} of {total} deliveries")

    def _reset_trf_filters(self) -> None:
        """Clears search and category filter."""
        self.trf_search_var.set("")
        self.trf_cat_var.set("All")
        self._apply_trf_filters()

    def _sort_trf_col(self, col: str) -> None:
        """Sorts the TRF treeview by the clicked column."""
        items = self.tree_trf.get_children("")
        if not items:
            return

        asc = not self._sort_directions.get(col, True)
        self._sort_directions[col] = asc

        col_indices = {"date": 0, "field": 1, "category": 2, "mu": 3, "size": 4, "filename": 5}
        idx = col_indices.get(col, 0)

        def sort_key(item_id):
            val = self.tree_trf.item(item_id, "values")[idx]
            if col == "mu":
                try:
                    return float(val.replace(" MU", ""))
                except ValueError:
                    return 0.0
            elif col == "size":
                try:
                    return float(val.replace(" MB", ""))
                except ValueError:
                    return 0.0
            return str(val).lower()

        sorted_items = sorted(items, key=sort_key, reverse=not asc)
        for i, item_id in enumerate(sorted_items):
            self.tree_trf.move(item_id, "", i)

    def _on_load_selected_trf(self) -> None:
        """Loads selected TRF delivery into the main application viewer."""
        selected = self.tree_trf.selection()
        if not selected:
            messagebox.showinfo("Select Delivery", "Please select a TRF delivery to load.", parent=self)
            return

        filename = selected[0]
        # Find entry
        entry = next((e for e in self.package.trf_entries if e.filename == filename), None)
        if entry:
            self.on_load_trf(self.package, entry)

    # -------------------------------------------------------------------------
    # Tab 2: Subsystem Logs
    # -------------------------------------------------------------------------

    def _build_log_tab(self, parent: ttk.Frame) -> None:
        """Builds Subsystem & Event logs browser."""
        filt_frame = tk.Frame(parent, bg=AppTheme.BG_CARD, padx=8, pady=6, highlightbackground="#334155", highlightthickness=1)
        filt_frame.pack(fill="x", pady=(0, 6))

        tk.Label(filt_frame, text="Search Logs:", bg=AppTheme.BG_CARD, fg=AppTheme.TEXT_SECONDARY, font=AppTheme.FONT_BODY_BOLD).pack(side="left", padx=(0, 4))
        self.log_search_var = tk.StringVar()
        self.log_search_var.trace_add("write", lambda *args: self._apply_log_filters())
        search_entry = ttk.Entry(filt_frame, textvariable=self.log_search_var, width=26)
        search_entry.pack(side="left", padx=(0, 14))

        self.lbl_log_count = tk.Label(filt_frame, text="", bg=AppTheme.BG_CARD, fg="#38bdf8", font=AppTheme.FONT_SMALL)
        self.lbl_log_count.pack(side="right", padx=6)

        tree_frame = ttk.Frame(parent)
        tree_frame.pack(fill="both", expand=True)

        columns = ("date", "name", "category", "size")
        self.tree_log = ttk.Treeview(
            tree_frame,
            columns=columns,
            show="headings",
            selectmode="browse"
        )
        self.tree_log.heading("date", text="Date & Time", command=lambda: self._sort_log_col("date"))
        self.tree_log.heading("name", text="Log File Name", command=lambda: self._sort_log_col("name"))
        self.tree_log.heading("category", text="Category", command=lambda: self._sort_log_col("category"))
        self.tree_log.heading("size", text="Size", command=lambda: self._sort_log_col("size"))

        self.tree_log.column("date", width=160, anchor="w")
        self.tree_log.column("name", width=340, anchor="w")
        self.tree_log.column("category", width=180, anchor="w")
        self.tree_log.column("size", width=100, anchor="e")

        scroll_y = ttk.Scrollbar(tree_frame, orient="vertical", command=self.tree_log.yview)
        scroll_x = ttk.Scrollbar(tree_frame, orient="horizontal", command=self.tree_log.xview)
        self.tree_log.configure(yscrollcommand=scroll_y.set, xscrollcommand=scroll_x.set)

        self.tree_log.grid(row=0, column=0, sticky="nsew")
        scroll_y.grid(row=0, column=1, sticky="ns")
        scroll_x.grid(row=1, column=0, sticky="ew")

        tree_frame.columnconfigure(0, weight=1)
        tree_frame.rowconfigure(0, weight=1)

        self.tree_log.bind("<Double-1>", lambda e: self._on_load_selected_log())
        self.tree_log.bind("<Return>", lambda e: self._on_load_selected_log())

        self._apply_log_filters()

    def _apply_log_filters(self) -> None:
        """Filters logs list."""
        self.tree_log.delete(*self.tree_log.get_children())
        query = self.log_search_var.get().strip().upper()

        count = 0
        for entry in self.package.log_entries:
            if query and (query not in entry.display_name.upper() and
                          query not in entry.category.upper() and
                          query not in (entry.date_time or "").upper()):
                continue

            if entry.file_size > 1024 * 1024:
                sz_str = f"{entry.file_size / (1024 * 1024):.2f} MB"
            elif entry.file_size > 1024:
                sz_str = f"{entry.file_size / 1024:.1f} KB"
            else:
                sz_str = f"{entry.file_size} B"

            self.tree_log.insert(
                "",
                "end",
                iid=entry.filename,
                values=(entry.date_time or "--", entry.display_name, entry.category, sz_str)
            )
            count += 1

        self.lbl_log_count.config(text=f"Showing {count} of {len(self.package.log_entries)} logs")

    def _sort_log_col(self, col: str) -> None:
        """Sorts the log treeview by the clicked column."""
        items = self.tree_log.get_children("")
        if not items:
            return

        asc = not self._sort_directions.get(f"log_{col}", True)
        self._sort_directions[f"log_{col}"] = asc

        col_indices = {"date": 0, "name": 1, "category": 2, "size": 3}
        idx = col_indices.get(col, 0)

        def sort_key(item_id):
            vals = self.tree_log.item(item_id, "values")
            val = vals[idx]
            if col == "category":
                return (str(val).lower(), str(vals[0]), str(vals[1]).lower())
            elif col == "size":
                try:
                    parts = str(val).split()
                    if len(parts) == 2:
                        num, unit = float(parts[0]), parts[1].upper()
                        mult = 1024 * 1024 if "MB" in unit else (1024 if "KB" in unit else 1)
                        return num * mult
                    return float(parts[0])
                except (ValueError, IndexError):
                    return 0.0
            elif col == "date":
                return (str(val), str(vals[1]).lower())
            return str(val).lower()

        sorted_items = sorted(items, key=sort_key, reverse=not asc)
        for i, item_id in enumerate(sorted_items):
            self.tree_log.move(item_id, "", i)

    def _on_load_selected_log(self) -> None:
        """Loads selected log file into the main viewer's text log view."""
        selected = self.tree_log.selection()
        if not selected:
            messagebox.showinfo("Select Log", "Please select a log file to load.", parent=self)
            return

        filename = selected[0]
        entry = next((e for e in self.package.log_entries if e.filename == filename), None)
        if entry and self.on_load_log:
            self.on_load_log(self.package, entry)

    # -------------------------------------------------------------------------
    # Tab 3: Machine Info & Manifest
    # -------------------------------------------------------------------------

    def _build_manifest_tab(self, parent: ttk.Frame) -> None:
        """Builds machine info and raw manifest viewer."""
        top_info = tk.Frame(parent, bg=AppTheme.BG_CARD, padx=12, pady=10, highlightbackground="#334155", highlightthickness=1)
        top_info.pack(fill="x", pady=(0, 6))

        m = self.package.machine_info

        row1 = tk.Frame(top_info, bg=AppTheme.BG_CARD)
        row1.pack(fill="x", pady=2)
        tk.Label(row1, text="Linac Hostname:", bg=AppTheme.BG_CARD, fg=AppTheme.TEXT_SECONDARY, font=AppTheme.FONT_BODY_BOLD, width=16, anchor="w").pack(side="left")
        tk.Label(row1, text=m.machine_id, bg=AppTheme.BG_CARD, fg="#38bdf8", font=AppTheme.FONT_BODY_BOLD).pack(side="left")

        row2 = tk.Frame(top_info, bg=AppTheme.BG_CARD)
        row2.pack(fill="x", pady=2)
        tk.Label(row2, text="Export Timestamp:", bg=AppTheme.BG_CARD, fg=AppTheme.TEXT_SECONDARY, font=AppTheme.FONT_BODY_BOLD, width=16, anchor="w").pack(side="left")
        tk.Label(row2, text=m.export_timestamp or "Unknown", bg=AppTheme.BG_CARD, fg="#f8fafc", font=AppTheme.FONT_BODY).pack(side="left")

        if m.os_name or m.os_version:
            row3 = tk.Frame(top_info, bg=AppTheme.BG_CARD)
            row3.pack(fill="x", pady=2)
            tk.Label(row3, text="Operating System:", bg=AppTheme.BG_CARD, fg=AppTheme.TEXT_SECONDARY, font=AppTheme.FONT_BODY_BOLD, width=16, anchor="w").pack(side="left")
            tk.Label(row3, text=f"{m.os_name} {m.os_version}".strip(), bg=AppTheme.BG_CARD, fg="#f8fafc", font=AppTheme.FONT_BODY).pack(side="left")

        if m.ip_addresses:
            row4 = tk.Frame(top_info, bg=AppTheme.BG_CARD)
            row4.pack(fill="x", pady=2)
            tk.Label(row4, text="Network IPv4:", bg=AppTheme.BG_CARD, fg=AppTheme.TEXT_SECONDARY, font=AppTheme.FONT_BODY_BOLD, width=16, anchor="w").pack(side="left")
            tk.Label(row4, text=", ".join(m.ip_addresses), bg=AppTheme.BG_CARD, fg="#22c55e", font=AppTheme.FONT_BODY).pack(side="left")

        # Manifest text area
        txt_frame = ttk.Frame(parent)
        txt_frame.pack(fill="both", expand=True)

        txt_manifest = tk.Text(
            txt_frame,
            bg="#0b1120",
            fg="#cbd5e1",
            insertbackground="#ffffff",
            font=("Consolas", 9),
            wrap="none",
            highlightthickness=0
        )
        scroll_y = ttk.Scrollbar(txt_frame, orient="vertical", command=txt_manifest.yview)
        scroll_x = ttk.Scrollbar(txt_frame, orient="horizontal", command=txt_manifest.xview)
        txt_manifest.configure(yscrollcommand=scroll_y.set, xscrollcommand=scroll_x.set)

        txt_manifest.grid(row=0, column=0, sticky="nsew")
        scroll_y.grid(row=0, column=1, sticky="ns")
        scroll_x.grid(row=1, column=0, sticky="ew")
        txt_frame.columnconfigure(0, weight=1)
        txt_frame.rowconfigure(0, weight=1)

        manifest_content = m.raw_manifest or "No RTDManifest.txt file found in package."
        txt_manifest.insert("1.0", manifest_content)
        txt_manifest.config(state="disabled")

    # -------------------------------------------------------------------------
    # Footer Action Buttons
    # -------------------------------------------------------------------------

    def _build_footer(self) -> None:
        """Builds dialog footer bar with load and close actions."""
        footer = tk.Frame(self, bg=AppTheme.BG_MAIN, padx=12, pady=10)
        footer.pack(fill="x")

        lbl_hint = tk.Label(
            footer,
            text="💡 Tip: Double-click any delivery or log row to load it directly into the viewer.",
            bg=AppTheme.BG_MAIN,
            fg=AppTheme.TEXT_MUTED,
            font=AppTheme.FONT_SMALL
        )
        lbl_hint.pack(side="left")

        btn_close = tk.Button(
            footer,
            text="Close",
            bg="#334155",
            fg="#ffffff",
            activebackground="#475569",
            activeforeground="#ffffff",
            font=("Segoe UI", 9, "bold"),
            relief="flat",
            padx=14,
            pady=5,
            command=self.destroy
        )
        btn_close.pack(side="right", padx=(6, 0))

        btn_load = tk.Button(
            footer,
            text="▶ Load Selected Delivery",
            bg=AppTheme.PRIMARY,
            fg="#ffffff",
            activebackground=AppTheme.PRIMARY_HOVER,
            activeforeground="#ffffff",
            font=("Segoe UI", 9, "bold"),
            relief="flat",
            padx=16,
            pady=5,
            command=self._on_load_selected_trf
        )
        btn_load.pack(side="right")
