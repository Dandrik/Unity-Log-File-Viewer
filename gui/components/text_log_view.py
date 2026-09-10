"""Machine Event & Subsystem Text Log Viewer."""

import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from typing import Dict, List, Optional

from core.models import LogEntry
from core.text_log_parser import TextLogParser
from gui.components.stat_card import StatCard
from gui.styles import AppTheme


SAMPLE_UNITY_LOG = """
2026-09-10 09:14:02.100 [LinacState] INFO - System entering Treatment Preparation state.
2026-09-10 09:14:05.340 [MRAcquisition] INFO - MRI sequence pre-scan calibration verified (Gradient shim OK).
2026-09-10 09:14:12.820 [MLCService] INFO - Initializing Agility 160-leaf MLC bank calibration.
2026-09-10 09:14:15.650 [MLCService] WARN - Leaf 24 optical encoder delta slightly elevated (+0.38 mm), compensating.
2026-09-10 09:14:22.010 [RFSubsystem] INFO - Magnetron mod pulse width: 3.2 us, Frequency AFC locked.
2026-09-10 09:14:30.500 [BeamControl] INFO - Radiation beam on: Target MU = 250.0, Dose Rate = 450 MU/min.
2026-09-10 09:14:48.210 [GantryDriver] WARN - Gantry angular velocity deviation detected: measured 5.8 deg/s vs expected 6.0 deg/s.
2026-09-10 09:15:02.110 [MLCService] ERROR - Dynamic leaf tracking error exceeded threshold on Leaf 24 (1.42 mm).
    Error Code: ERR_MLC_LEAF_LAG_0x0018
    Details: Bank Y1 Leaf 24 motor current 1.8A, tracking lag at Control Point 142.
    Stack Trace:
        at Elekta.Unity.MLC.AgilityController.VerifyTolerance()
        at Elekta.Unity.Delivery.TrackAxes()
2026-09-10 09:15:04.890 [SafetyInterlock] WARN - MLC leaf position warning flag active; continuing delivery within secondary guard band.
2026-09-10 09:15:35.400 [BeamControl] INFO - Beam complete: 250.0 MU delivered in 64.9 seconds.
2026-09-10 09:15:38.100 [LinacState] INFO - System returning to Ready state.
"""


class TextLogView(ttk.Frame):
    """Viewer for general Elekta Unity service, machine event, and subsystem text logs."""

    def __init__(self, parent, **kwargs):
        super().__init__(parent, **kwargs)
        self.parser = TextLogParser()
        self.active_entries: List[LogEntry] = []

        self._build_ui()

    def _build_ui(self) -> None:
        """Constructs toolbar, filter controls, table, and inspector."""
        # Top Action Bar
        self.action_bar = ttk.Frame(self)
        self.action_bar.pack(fill="x", padx=10, pady=(6, 4))

        self.btn_open = ttk.Button(
            self.action_bar,
            text="📂 Open Text Log",
            style="Primary.TButton",
            command=self.open_log_file
        )
        self.btn_open.pack(side="left", padx=(0, 6))

        self.btn_sample = ttk.Button(
            self.action_bar,
            text="🧪 Load Sample Log",
            style="Secondary.TButton",
            command=self.load_sample_log
        )
        self.btn_sample.pack(side="left", padx=4)

        self.btn_export = ttk.Button(
            self.action_bar,
            text="💾 Export Filtered",
            style="Secondary.TButton",
            command=self.export_filtered
        )
        self.btn_export.pack(side="left", padx=4)

        self.lbl_file_info = ttk.Label(
            self.action_bar,
            text="No log file loaded. Click 'Open Text Log' or 'Load Sample Log' to begin.",
            font=AppTheme.FONT_BODY,
            foreground=AppTheme.TEXT_SECONDARY
        )
        self.lbl_file_info.pack(side="left", padx=12)

        # KPI Badges Row
        self.kpi_frame = ttk.Frame(self)
        self.kpi_frame.pack(fill="x", padx=10, pady=4)

        self.card_total = StatCard(self.kpi_frame, title="Total Lines", value="0", subtext="Records")
        self.card_total.pack(side="left", fill="both", expand=True, padx=3)

        self.card_crit = StatCard(self.kpi_frame, title="Critical", value="0", subtext="Fatal / Severe", status="NEUTRAL")
        self.card_crit.pack(side="left", fill="both", expand=True, padx=3)

        self.card_err = StatCard(self.kpi_frame, title="Errors", value="0", subtext="Exceptions", status="NEUTRAL")
        self.card_err.pack(side="left", fill="both", expand=True, padx=3)

        self.card_warn = StatCard(self.kpi_frame, title="Warnings", value="0", subtext="Alerts", status="NEUTRAL")
        self.card_warn.pack(side="left", fill="both", expand=True, padx=3)

        self.card_info = StatCard(self.kpi_frame, title="Info / Debug", value="0", subtext="Normal messages")
        self.card_info.pack(side="left", fill="both", expand=True, padx=3)

        # Filter Bar
        self.filter_card = ttk.Frame(self, style="Card.TFrame", padding=(10, 6))
        self.filter_card.pack(fill="x", padx=10, pady=4)

        # Search box
        ttk.Label(self.filter_card, text="Search:", font=AppTheme.FONT_BODY_BOLD, style="CardTitle.TLabel").pack(side="left", padx=(0, 4))
        self.search_var = tk.StringVar()
        self.search_entry = ttk.Entry(self.filter_card, textvariable=self.search_var, width=28)
        self.search_entry.pack(side="left", padx=4)
        self.search_entry.bind("<KeyRelease>", lambda e: self.apply_filters())

        # Checkboxes: Regex & Case Sensitive
        self.regex_var = tk.BooleanVar(value=False)
        self.chk_regex = ttk.Checkbutton(self.filter_card, text="Regex", variable=self.regex_var, command=self.apply_filters)
        self.chk_regex.pack(side="left", padx=6)

        self.case_var = tk.BooleanVar(value=False)
        self.chk_case = ttk.Checkbutton(self.filter_card, text="Match Case", variable=self.case_var, command=self.apply_filters)
        self.chk_case.pack(side="left", padx=6)

        # Subsystem filter dropdown
        ttk.Label(self.filter_card, text="Subsystem:", font=AppTheme.FONT_BODY_BOLD, style="CardTitle.TLabel").pack(side="left", padx=(14, 4))
        self.comp_var = tk.StringVar(value="All")
        self.comp_combo = ttk.Combobox(self.filter_card, textvariable=self.comp_var, values=["All"], width=16, state="readonly")
        self.comp_combo.pack(side="left", padx=4)
        self.comp_combo.bind("<<ComboboxSelected>>", lambda e: self.apply_filters())

        # Severity checkboxes
        ttk.Label(self.filter_card, text="Levels:", font=AppTheme.FONT_BODY_BOLD, style="CardTitle.TLabel").pack(side="left", padx=(14, 4))
        self.level_vars: Dict[str, tk.BooleanVar] = {}
        for lvl in ["CRITICAL", "ERROR", "WARN", "INFO", "DEBUG"]:
            var = tk.BooleanVar(value=True)
            self.level_vars[lvl] = var
            chk = ttk.Checkbutton(self.filter_card, text=lvl, variable=var, command=self.apply_filters)
            chk.pack(side="left", padx=4)

        # Clear button
        self.btn_clear = ttk.Button(self.filter_card, text="✕ Reset", style="Secondary.TButton", command=self.reset_filters)
        self.btn_clear.pack(side="right", padx=4)

        # Split pane: Log Table on top, Inspector on bottom
        self.paned = ttk.PanedWindow(self, orient="vertical")
        self.paned.pack(fill="both", expand=True, padx=10, pady=(4, 8))

        # Top Pane: Treeview
        self.table_frame = ttk.Frame(self.paned)
        self.paned.add(self.table_frame, weight=3)

        cols = ("Line", "Timestamp", "Level", "Subsystem", "Message")
        self.tree = ttk.Treeview(self.table_frame, columns=cols, show="headings", selectmode="browse")
        self.tree.heading("Line", text="Line")
        self.tree.heading("Timestamp", text="Timestamp")
        self.tree.heading("Level", text="Level")
        self.tree.heading("Subsystem", text="Subsystem")
        self.tree.heading("Message", text="Message Preview")

        self.tree.column("Line", width=60, anchor="center")
        self.tree.column("Timestamp", width=170, anchor="w")
        self.tree.column("Level", width=80, anchor="center")
        self.tree.column("Subsystem", width=140, anchor="w")
        self.tree.column("Message", width=550, anchor="w")

        # Color row tags
        self.tree.tag_configure("CRITICAL", background="#fee2e2", foreground="#991b1b")
        self.tree.tag_configure("ERROR", background="#fee2e2", foreground="#dc2626")
        self.tree.tag_configure("WARN", background="#fef3c7", foreground="#b45309")
        self.tree.tag_configure("INFO", background="#ffffff", foreground="#0f172a")
        self.tree.tag_configure("DEBUG", background="#f8fafc", foreground="#64748b")

        tree_scroll_y = ttk.Scrollbar(self.table_frame, orient="vertical", command=self.tree.yview)
        tree_scroll_x = ttk.Scrollbar(self.table_frame, orient="horizontal", command=self.tree.xview)
        self.tree.configure(yscrollcommand=tree_scroll_y.set, xscrollcommand=tree_scroll_x.set)

        self.tree.pack(side="left", fill="both", expand=True)
        tree_scroll_y.pack(side="right", fill="y")
        tree_scroll_x.pack(side="bottom", fill="x")

        self.tree.bind("<<TreeviewSelect>>", self._on_tree_select)

        # Bottom Pane: Inspector
        self.inspector_frame = ttk.Frame(self.paned, style="Card.TFrame", padding=6)
        self.paned.add(self.inspector_frame, weight=1)

        insp_header = ttk.Frame(self.inspector_frame, style="Card.TFrame")
        insp_header.pack(fill="x", pady=(0, 4))
        ttk.Label(insp_header, text="ENTRY INSPECTOR & TRACEBACK", font=AppTheme.FONT_TITLE, style="CardTitle.TLabel").pack(side="left")

        self.btn_copy = ttk.Button(insp_header, text="📋 Copy", style="Secondary.TButton", command=self._copy_inspector)
        self.btn_copy.pack(side="right")

        self.txt_inspector = tk.Text(
            self.inspector_frame,
            wrap="word",
            font=AppTheme.FONT_MONO,
            bg="#f8fafc",
            fg="#0f172a",
            padx=8,
            pady=8,
            relief="solid",
            borderwidth=1
        )
        insp_scroll = ttk.Scrollbar(self.inspector_frame, orient="vertical", command=self.txt_inspector.yview)
        self.txt_inspector.configure(yscrollcommand=insp_scroll.set)
        self.txt_inspector.pack(side="left", fill="both", expand=True)
        insp_scroll.pack(side="right", fill="y")

    def open_log_file(self) -> None:
        """Opens file dialog for text log file."""
        filepath = filedialog.askopenfilename(
            title="Select Elekta Unity Text Log File",
            filetypes=[("Log & Text Files", "*.log;*.txt;*.csv;*.err"), ("All Files", "*.*")]
        )
        if not filepath:
            return

        try:
            self.parser.parse_file(filepath)
            self.lbl_file_info.config(text=f"Loaded: {filepath}")
            self._on_logs_loaded()
        except Exception as e:
            messagebox.showerror("Error Reading Log", f"Failed to parse log file:\n{e}")

    def load_sample_log(self) -> None:
        """Loads sample Elekta Unity event log."""
        self.parser.parse_text(SAMPLE_UNITY_LOG)
        self.lbl_file_info.config(text="Loaded: Sample Elekta Unity Machine Event Log")
        self._on_logs_loaded()

    def _on_logs_loaded(self) -> None:
        """Updates components and KPI stats after loading logs."""
        comps = self.parser.get_components()
        self.comp_combo["values"] = comps
        self.comp_var.set("All")

        stats = self.parser.get_summary_stats()
        self.card_total.update_data(str(stats["TOTAL"]), "Records")

        crit_status = "FAIL" if stats["CRITICAL"] > 0 else "NEUTRAL"
        self.card_crit.update_data(str(stats["CRITICAL"]), "Fatal / Severe", crit_status)

        err_status = "FAIL" if stats["ERROR"] > 0 else "NEUTRAL"
        self.card_err.update_data(str(stats["ERROR"]), "Exceptions", err_status)

        warn_status = "WARN" if stats["WARN"] > 0 else "NEUTRAL"
        self.card_warn.update_data(str(stats["WARN"]), "Alerts", warn_status)

        self.card_info.update_data(f"{stats['INFO']} / {stats['DEBUG']}", "Info / Debug")

        self.apply_filters()

    def apply_filters(self) -> None:
        """Applies active search, level, and component filters."""
        query = self.search_var.get().strip()
        is_regex = self.regex_var.get()
        case_sens = self.case_var.get()
        component = self.comp_var.get()

        selected_levels = [lvl for lvl, var in self.level_vars.items() if var.get()]

        self.active_entries = self.parser.filter_entries(
            search_query=query,
            is_regex=is_regex,
            case_sensitive=case_sens,
            levels=selected_levels,
            component=component
        )

        self.tree.delete(*self.tree.get_children())
        for e in self.active_entries:
            tag = e.level.upper() if e.level.upper() in ("CRITICAL", "ERROR", "WARN", "INFO", "DEBUG") else "INFO"
            self.tree.insert(
                "",
                "end",
                iid=str(e.line_number),
                values=(
                    e.line_number,
                    e.timestamp or "--",
                    e.level,
                    e.component,
                    e.message
                ),
                tags=(tag,)
            )

    def reset_filters(self) -> None:
        """Resets all filters to default."""
        self.search_var.set("")
        self.regex_var.set(False)
        self.case_var.set(False)
        self.comp_var.set("All")
        for var in self.level_vars.values():
            var.set(True)
        self.apply_filters()

    def _on_tree_select(self, event) -> None:
        """Shows selected entry's full details in inspector."""
        selected = self.tree.selection()
        if not selected:
            return

        line_id = int(selected[0])
        entry = next((e for e in self.active_entries if e.line_number == line_id), None)
        if not entry:
            return

        self.txt_inspector.delete("1.0", "end")
        content = [
            f"--- LOG ENTRY DETAIL ---",
            f"Line Number: {entry.line_number}",
            f"Timestamp  : {entry.timestamp or 'N/A'}",
            f"Level      : {entry.level}",
            f"Subsystem  : {entry.component}",
            f"Message    : {entry.message}",
            f"\n--- RAW RECORD ---",
            entry.raw_text
        ]
        if entry.details:
            content += [f"\n--- TRACEBACK / ADDITIONAL DETAILS ---", entry.details]

        self.txt_inspector.insert("1.0", "\n".join(content))

    def _copy_inspector(self) -> None:
        text = self.txt_inspector.get("1.0", "end-1c")
        if text:
            self.clipboard_clear()
            self.clipboard_append(text)
            messagebox.showinfo("Copied", "Log entry copied to clipboard.")

    def export_filtered(self) -> None:
        """Exports currently filtered entries to a text or CSV file."""
        if not self.active_entries:
            messagebox.showwarning("No Data", "No filtered entries to export.")
            return

        filepath = filedialog.asksaveasfilename(
            title="Export Filtered Logs",
            defaultextension=".txt",
            filetypes=[("Text Log", "*.log;*.txt"), ("CSV File", "*.csv"), ("All Files", "*.*")]
        )
        if not filepath:
            return

        try:
            with open(filepath, "w", encoding="utf-8") as f:
                for e in self.active_entries:
                    f.write(e.raw_text + "\n")
            messagebox.showinfo("Export Complete", f"Successfully exported {len(self.active_entries)} lines to:\n{filepath}")
        except Exception as e:
            messagebox.showerror("Export Failed", f"Could not write file:\n{e}")

