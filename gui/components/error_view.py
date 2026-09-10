"""MLC Leaf Error QA Analysis view including heatmaps and RMS bar charts."""

import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from typing import Optional
import numpy as np

import matplotlib
matplotlib.use("TkAgg")
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure

from core.trf_analyzer import TRFAnalyzer
from gui.styles import AppTheme


class ErrorView(ttk.Frame):
    """Provides deep QA inspection of MLC leaf errors: 2D heatmaps and RMS profiles."""

    def __init__(self, parent, **kwargs):
        super().__init__(parent, **kwargs)
        self.analyzer: Optional[TRFAnalyzer] = None

        self._build_ui()

    def _build_ui(self) -> None:
        """Constructs error analysis sub-tabs and controls."""
        # Top toolbar
        self.toolbar = ttk.Frame(self)
        self.toolbar.pack(fill="x", padx=6, pady=4)

        ttk.Label(self.toolbar, text="MLC Bank:", font=AppTheme.FONT_BODY_BOLD).pack(side="left", padx=(0, 4))
        self.bank_var = tk.StringVar(value="Y1")
        self.bank_combo = ttk.Combobox(self.toolbar, textvariable=self.bank_var, values=["Y1", "Y2"], width=6, state="readonly")
        self.bank_combo.pack(side="left", padx=4)
        self.bank_combo.bind("<<ComboboxSelected>>", self._on_bank_changed)

        self.btn_export = ttk.Button(self.toolbar, text="💾 Export Error CSV", style="Secondary.TButton", command=self._export_csv)
        self.btn_export.pack(side="right", padx=4)

        # Tabbed Notebook for Heatmap vs RMS Profile vs Table
        self.notebook = ttk.Notebook(self)
        self.notebook.pack(fill="both", expand=True, padx=4, pady=4)

        # Tab 1: Heatmap
        self.tab_heatmap = ttk.Frame(self.notebook)
        self.notebook.add(self.tab_heatmap, text="📊 Leaf Error Heatmap")

        self.fig_heatmap = Figure(figsize=(7, 4.5), dpi=100)
        self.fig_heatmap.patch.set_facecolor(AppTheme.BG_MAIN)
        self.ax_heatmap = self.fig_heatmap.add_subplot(1, 1, 1)
        self.canvas_heatmap = FigureCanvasTkAgg(self.fig_heatmap, master=self.tab_heatmap)
        self.canvas_heatmap.get_tk_widget().pack(fill="both", expand=True)

        # Tab 2: RMS Bar Chart
        self.tab_rms = ttk.Frame(self.notebook)
        self.notebook.add(self.tab_rms, text="📈 RMS Error per Leaf")

        self.fig_rms = Figure(figsize=(7, 4.5), dpi=100)
        self.fig_rms.patch.set_facecolor(AppTheme.BG_MAIN)
        self.ax_rms = self.fig_rms.add_subplot(1, 1, 1)
        self.canvas_rms = FigureCanvasTkAgg(self.fig_rms, master=self.tab_rms)
        self.canvas_rms.get_tk_widget().pack(fill="both", expand=True)

        # Tab 3: Offending Leaves Table
        self.tab_table = ttk.Frame(self.notebook)
        self.notebook.add(self.tab_table, text="📋 Worst Performing Leaves")

        cols = ("Rank", "Bank", "Leaf", "MaxError", "RMSError", "Within1mm", "Status")
        self.tree = ttk.Treeview(self.tab_table, columns=cols, show="headings", height=14)
        self.tree.heading("Rank", text="#")
        self.tree.heading("Bank", text="Bank")
        self.tree.heading("Leaf", text="Leaf Number")
        self.tree.heading("MaxError", text="Max Error (mm)")
        self.tree.heading("RMSError", text="RMS Error (mm)")
        self.tree.heading("Within1mm", text="% ≤ 1.0 mm")
        self.tree.heading("Status", text="Status")

        self.tree.column("Rank", width=40, anchor="center")
        self.tree.column("Bank", width=60, anchor="center")
        self.tree.column("Leaf", width=90, anchor="center")
        self.tree.column("MaxError", width=120, anchor="e")
        self.tree.column("RMSError", width=120, anchor="e")
        self.tree.column("Within1mm", width=100, anchor="e")
        self.tree.column("Status", width=90, anchor="center")

        scroll = ttk.Scrollbar(self.tab_table, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=scroll.set)
        self.tree.pack(side="left", fill="both", expand=True)
        scroll.pack(side="right", fill="y")

    def set_analyzer(self, analyzer: TRFAnalyzer) -> None:
        """Sets analyzer and plots data."""
        self.analyzer = analyzer
        self.refresh()

    def refresh(self) -> None:
        """Refreshes all plots and table."""
        if not self.analyzer:
            return
        self._plot_heatmap()
        self._plot_rms()
        self._populate_table()

    def _plot_heatmap(self) -> None:
        """Plots 2D error heatmap."""
        self.ax_heatmap.clear()
        bank = self.bank_var.get()
        matrix, leaves, times = self.analyzer.get_leaf_error_heatmap_matrix(bank)

        # Plot absolute error matrix
        abs_matrix = np.abs(matrix)
        extent = [times[0], times[-1], leaves[-1], leaves[0]] if len(times) > 1 else [0, 1, 80, 1]

        im = self.ax_heatmap.imshow(
            abs_matrix,
            aspect="auto",
            cmap="YlOrRd",
            extent=extent,
            vmin=0.0,
            vmax=max(1.5, float(abs_matrix.max()))
        )

        self.ax_heatmap.set_title(f"Bank {bank} Leaf Positional Error Heatmap (|Error| mm)", fontsize=10, fontweight="bold")
        self.ax_heatmap.set_xlabel("Time (seconds)", fontsize=9, fontweight="bold")
        self.ax_heatmap.set_ylabel("Leaf Number (1 to 80)", fontsize=9, fontweight="bold")

        # Colorbar
        if hasattr(self, "_cb_heatmap") and self._cb_heatmap:
            self._cb_heatmap.remove()
        self._cb_heatmap = self.fig_heatmap.colorbar(im, ax=self.ax_heatmap, orientation="vertical", pad=0.02)
        self._cb_heatmap.set_label("Error (mm)", fontsize=8)

        self.fig_heatmap.tight_layout(pad=2.0)
        self.canvas_heatmap.draw_idle()

    def _plot_rms(self) -> None:
        """Plots RMS error bar chart across all 80 leaf pairs."""
        self.ax_rms.clear()
        leaf_stats = self.analyzer.leaf_stats

        y1_rms = [s.rms_error_mm for s in leaf_stats if s.bank == "Y1"]
        y2_rms = [s.rms_error_mm for s in leaf_stats if s.bank == "Y2"]
        leaves = np.arange(1, len(y1_rms) + 1)

        width = 0.4
        self.ax_rms.bar(leaves - width / 2, y1_rms, width=width, color="#2563eb", label="Bank Y1 RMS (mm)")
        self.ax_rms.bar(leaves + width / 2, y2_rms, width=width, color="#0891b2", label="Bank Y2 RMS (mm)")

        # Tolerance reference lines
        self.ax_rms.axhline(0.5, color="#16a34a", linestyle="--", linewidth=1, label="Nominal Limit (0.5 mm)")
        self.ax_rms.axhline(1.0, color="#dc2626", linestyle=":", linewidth=1.2, label="Action Limit (1.0 mm)")

        self.ax_rms.set_title("Root-Mean-Square (RMS) Positional Error by Leaf", fontsize=10, fontweight="bold")
        self.ax_rms.set_xlabel("Leaf Number (1 to 80)", fontsize=9, fontweight="bold")
        self.ax_rms.set_ylabel("RMS Error (mm)", fontsize=9, fontweight="bold")
        self.ax_rms.set_xlim(0, len(y1_rms) + 1)
        self.ax_rms.grid(True, linestyle=":", alpha=0.5)
        self.ax_rms.legend(loc="upper right", fontsize=8)

        self.fig_rms.tight_layout(pad=2.0)
        self.canvas_rms.draw_idle()

    def _populate_table(self) -> None:
        """Populates table of worst performing leaves sorted by max error."""
        self.tree.delete(*self.tree.get_children())
        stats = list(self.analyzer.leaf_stats)
        # Sort descending by max_error_mm
        stats.sort(key=lambda s: s.max_error_mm, reverse=True)

        for rank, s in enumerate(stats[:30], start=1):
            status = "PASS"
            if s.max_error_mm > 2.0:
                status = "FAIL"
            elif s.max_error_mm > 1.0:
                status = "WARN"

            self.tree.insert(
                "",
                "end",
                values=(
                    rank,
                    s.bank,
                    f"Leaf {s.leaf_number}",
                    f"{s.max_error_mm:.2f}",
                    f"{s.rms_error_mm:.3f}",
                    f"{s.pct_within_1mm:.1f}%",
                    status
                )
            )

    def _on_bank_changed(self, event=None) -> None:
        if self.analyzer:
            self._plot_heatmap()

    def _export_csv(self) -> None:
        """Exports leaf error stats to a CSV file."""
        if not self.analyzer or not self.analyzer.leaf_stats:
            messagebox.showwarning("No Data", "No TRF error data available to export.")
            return

        filepath = filedialog.asksaveasfilename(
            title="Export MLC Error Statistics",
            defaultextension=".csv",
            filetypes=[("CSV Files", "*.csv"), ("All Files", "*.*")]
        )
        if not filepath:
            return

        try:
            import pandas as pd
            records = [
                {
                    "Bank": s.bank,
                    "Leaf": s.leaf_number,
                    "MaxError_mm": s.max_error_mm,
                    "MeanError_mm": s.mean_error_mm,
                    "RMSError_mm": s.rms_error_mm,
                    "PctWithin1mm": s.pct_within_1mm,
                    "PctWithin2mm": s.pct_within_2mm,
                }
                for s in self.analyzer.leaf_stats
            ]
            pd.DataFrame(records).to_csv(filepath, index=False)
            messagebox.showinfo("Export Successful", f"Saved MLC error statistics to:\n{filepath}")
        except Exception as e:
            messagebox.showerror("Export Failed", f"Could not save CSV file:\n{e}")

