"""Main TRF Delivery and Machine Trajectory View."""

import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from typing import Optional
import numpy as np

from core.models import TRFDataset
from core.trf_reader import TRFReader
from core.trf_analyzer import TRFAnalyzer
from gui.components.stat_card import StatCard
from gui.components.mlc_canvas import MLCCanvas
from gui.components.gantry_view import GantryView
from gui.components.error_view import ErrorView
from gui.styles import AppTheme


class TRFView(ttk.Frame):
    """Main container for Elekta Linac TRF file analysis."""

    def __init__(self, parent, **kwargs):
        super().__init__(parent, **kwargs)
        self.dataset: Optional[TRFDataset] = None
        self.analyzer: Optional[TRFAnalyzer] = None

        self._build_ui()

    def _build_ui(self) -> None:
        """Constructs TRF view layout."""
        # Action Bar
        self.action_bar = ttk.Frame(self)
        self.action_bar.pack(fill="x", padx=10, pady=(6, 4))

        self.btn_open = ttk.Button(
            self.action_bar,
            text="📂 Open .TRF File",
            style="Primary.TButton",
            command=self.open_trf_file
        )
        self.btn_open.pack(side="left", padx=(0, 6))

        self.btn_sample = ttk.Button(
            self.action_bar,
            text="🧪 Load Sample Delivery",
            style="Secondary.TButton",
            command=self.load_sample_data
        )
        self.btn_sample.pack(side="left", padx=4)

        self.lbl_file_info = ttk.Label(
            self.action_bar,
            text="No TRF file loaded. Click 'Open .TRF File' or 'Load Sample Delivery' to begin.",
            font=AppTheme.FONT_BODY,
            foreground=AppTheme.TEXT_SECONDARY
        )
        self.lbl_file_info.pack(side="left", padx=12)

        self.beam_only_var = tk.BooleanVar(value=True)
        self.chk_beam_only = ttk.Checkbutton(
            self.action_bar,
            text="Delivery Only (MU > 0)",
            variable=self.beam_only_var,
            command=self._on_beam_only_toggle
        )
        self.chk_beam_only.pack(side="right", padx=6)

        # KPI Stats Row
        self.kpi_frame = ttk.Frame(self)
        self.kpi_frame.pack(fill="x", padx=10, pady=6)

        self.card_machine = StatCard(self.kpi_frame, title="Machine", value="--", subtext="Elekta Unity")
        self.card_machine.pack(side="left", fill="both", expand=True, padx=3)

        self.card_field = StatCard(self.kpi_frame, title="Treatment Field", value="--", subtext="Plan / Field ID")
        self.card_field.pack(side="left", fill="both", expand=True, padx=3)

        self.card_mu = StatCard(self.kpi_frame, title="Delivered MU", value="--", subtext="Target MU")
        self.card_mu.pack(side="left", fill="both", expand=True, padx=3)

        self.card_gantry = StatCard(self.kpi_frame, title="Max Gantry Error", value="--", subtext="Tolerance: ±1.0°")
        self.card_gantry.pack(side="left", fill="both", expand=True, padx=3)

        self.card_leaf = StatCard(self.kpi_frame, title="Max Leaf Error", value="--", subtext="Tolerance: < 2.0 mm")
        self.card_leaf.pack(side="left", fill="both", expand=True, padx=3)

        self.card_qa = StatCard(self.kpi_frame, title="Delivery QA", value="--", subtext="Tolerance Check")
        self.card_qa.pack(side="left", fill="both", expand=True, padx=3)

        # Main Sub-Notebook Tabs
        self.sub_notebook = ttk.Notebook(self)
        self.sub_notebook.pack(fill="both", expand=True, padx=10, pady=(4, 8))

        # Tab 1: MLC Leaf Shapes
        self.tab_mlc = ttk.Frame(self.sub_notebook)
        self.sub_notebook.add(self.tab_mlc, text="🎯 MLC Leaf Shapes (BEV)")
        self.mlc_canvas = MLCCanvas(self.tab_mlc, on_frame_changed=self._on_mlc_frame_changed)
        self.mlc_canvas.pack(fill="both", expand=True)

        # Tab 2: Gantry Dynamics
        self.tab_gantry = ttk.Frame(self.sub_notebook)
        self.sub_notebook.add(self.tab_gantry, text="🔄 Gantry Trajectory & Dynamics")
        self.gantry_view = GantryView(self.tab_gantry, on_time_selected=self._on_gantry_time_selected)
        self.gantry_view.pack(fill="both", expand=True)

        # Tab 3: Error QA & Heatmaps
        self.tab_error = ttk.Frame(self.sub_notebook)
        self.sub_notebook.add(self.tab_error, text="📊 MLC QA & Error Heatmaps")
        self.error_view = ErrorView(self.tab_error)
        self.error_view.pack(fill="both", expand=True)

        # Tab 4: Raw Table Data
        self.tab_raw = ttk.Frame(self.sub_notebook)
        self.sub_notebook.add(self.tab_raw, text="📋 Raw Data Channels")
        self._build_raw_table(self.tab_raw)

    def _build_raw_table(self, parent: ttk.Frame) -> None:
        """Builds raw data table preview."""
        top_bar = ttk.Frame(parent)
        top_bar.pack(fill="x", padx=6, pady=4)

        ttk.Label(top_bar, text="Search Column / Channel:", font=AppTheme.FONT_BODY_BOLD).pack(side="left", padx=4)
        self.raw_search_var = tk.StringVar()
        self.raw_search_entry = ttk.Entry(top_bar, textvariable=self.raw_search_var, width=25)
        self.raw_search_entry.pack(side="left", padx=4)
        self.raw_search_entry.bind("<KeyRelease>", lambda e: self._filter_raw_columns())

        self.lbl_raw_info = ttk.Label(top_bar, text="Showing first 200 rows", font=AppTheme.FONT_SMALL, foreground=AppTheme.TEXT_SECONDARY)
        self.lbl_raw_info.pack(side="right", padx=6)

        table_frame = ttk.Frame(parent)
        table_frame.pack(fill="both", expand=True, padx=6, pady=4)

        self.raw_tree = ttk.Treeview(table_frame, show="headings")
        raw_scroll_y = ttk.Scrollbar(table_frame, orient="vertical", command=self.raw_tree.yview)
        raw_scroll_x = ttk.Scrollbar(table_frame, orient="horizontal", command=self.raw_tree.xview)
        self.raw_tree.configure(yscrollcommand=raw_scroll_y.set, xscrollcommand=raw_scroll_x.set)

        self.raw_tree.pack(side="left", fill="both", expand=True)
        raw_scroll_y.pack(side="right", fill="y")
        raw_scroll_x.pack(side="bottom", fill="x")

    def open_trf_file(self) -> None:
        """Opens file chooser to load a .trf file."""
        filepath = filedialog.askopenfilename(
            title="Select Elekta Linac TRF File",
            filetypes=[("TRF Log Files", "*.trf"), ("All Files", "*.*")]
        )
        if not filepath:
            return

        try:
            dataset = TRFReader.read_file(filepath)
            self.load_dataset(dataset, source_name=filepath)
        except Exception as e:
            messagebox.showerror(
                "Error Loading TRF",
                f"Failed to decode TRF file:\n{e}\n\nPlease verify that the file is a valid Elekta TRF binary."
            )

    def load_sample_data(self) -> None:
        """Generates and loads a realistic synthetic Elekta Unity delivery dataset."""
        dataset = TRFReader.create_synthetic_dataset(num_points=600)
        self.load_dataset(dataset, source_name="Sample Elekta Unity VMAT prostate delivery (Synthetic)")

    def load_dataset(self, dataset: TRFDataset, source_name: str = "") -> None:
        """Loads a dataset into all views and computes stats."""
        self.dataset = dataset
        self.analyzer = TRFAnalyzer(dataset, beam_only=self.beam_only_var.get())

        # Update File Info label
        self.lbl_file_info.config(text=f"Loaded: {source_name}")

        self._update_kpis()

        # Propagate to subviews
        self.mlc_canvas.set_analyzer(self.analyzer)
        self.gantry_view.set_analyzer(self.analyzer)
        self.error_view.set_analyzer(self.analyzer)
        self._populate_raw_table()

    def _update_kpis(self) -> None:
        """Updates KPI cards from active analyzer statistics."""
        if not self.dataset or not self.analyzer:
            return

        hdr = self.dataset.header
        self.card_machine.update_data(hdr.machine or "Unity", "Elekta Linac")
        self.card_field.update_data(hdr.field_name or "Field", hdr.field_label or "Field Label")
        self.card_mu.update_data(f"{hdr.mu:.1f} MU" if hdr.mu > 0 else f"{self.analyzer.stats.total_mu:.1f} MU", "Delivered")

        stats = self.analyzer.stats
        if stats:
            g_status = "PASS" if stats.gantry_max_error_deg <= 1.0 else "FAIL"
            self.card_gantry.update_data(f"{stats.gantry_max_error_deg:.2f}°", f"RMS: {stats.gantry_rms_error_deg:.2f}°", g_status)

            l_status = "PASS" if stats.overall_max_leaf_error_mm <= 1.0 else ("WARN" if stats.overall_max_leaf_error_mm <= 2.0 else "FAIL")
            self.card_leaf.update_data(f"{stats.overall_max_leaf_error_mm:.2f} mm", stats.worst_leaf_name, l_status)

            qa_status = "PASS" if (g_status == "PASS" and l_status != "FAIL") else "FAIL"
            qa_sub = f"{stats.pct_samples_within_2mm:.1f}% in tol"
            self.card_qa.update_data(qa_status, qa_sub, qa_status)

    def _on_beam_only_toggle(self) -> None:
        """Callback when user toggles Delivery Only (MU > 0)."""
        if self.analyzer:
            self.analyzer.set_beam_only(self.beam_only_var.get())
            self._update_kpis()
            self.error_view.refresh()

    def _on_mlc_frame_changed(self, frame_idx: int) -> None:
        """Callback when MLC canvas frame advances."""
        if self.analyzer and frame_idx < len(self.analyzer.df):
            time_s = float(self.analyzer.df.index[frame_idx])
            self.gantry_view.update_cursor(time_s)

    def _on_gantry_time_selected(self, time_s: float) -> None:
        """Callback when user clicks a point on the gantry timeline."""
        if self.analyzer and len(self.analyzer.df) > 0:
            times = self.analyzer.df.index.to_numpy()
            idx = int(np.argmin(np.abs(times - time_s)))
            self.mlc_canvas.set_frame(idx)

    def _populate_raw_table(self) -> None:
        """Populates the raw dataframe table preview."""
        if not self.dataset:
            return

        df = self.dataset.dataframe
        self.raw_tree.delete(*self.raw_tree.get_children())

        # Select a subset of representative columns for quick inspection
        all_cols = list(df.columns)
        search = self.raw_search_var.get().lower().strip()
        if search:
            display_cols = [c for c in all_cols if search in c.lower()]
        else:
            display_cols = ["Step Gantry/Scaled Actual (deg)", "Step Gantry/Positional Error (deg)", "Step Dose/Actual Value (Mu)"]
            display_cols += [c for c in all_cols if "Leaf 24" in c or "Leaf 40" in c or "X1 Diaphragm" in c][:10]

        # Always include Time column first
        cols = ["Time (s)"] + display_cols
        self.raw_tree["columns"] = cols
        for c in cols:
            self.raw_tree.heading(c, text=c)
            self.raw_tree.column(c, width=130, anchor="e")

        preview_df = df.iloc[:200]
        for time_val, row in preview_df.iterrows():
            vals = [f"{time_val:.2f}"] + [f"{float(row[c]):.2f}" if (c in row and isinstance(row[c], (int, float, np.number))) else str(row.get(c, "")) for c in display_cols]
            self.raw_tree.insert("", "end", values=vals)

        self.lbl_raw_info.config(text=f"Showing {len(preview_df)} of {len(df)} rows | {len(all_cols)} channels available")

    def _filter_raw_columns(self) -> None:
        self._populate_raw_table()
