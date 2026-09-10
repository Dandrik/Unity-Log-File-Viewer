"""Gantry angle and positional error dynamics visualizer."""

import tkinter as tk
from tkinter import ttk
from typing import Callable, Optional
import numpy as np

import matplotlib
matplotlib.use("TkAgg")
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure

from core.trf_analyzer import TRFAnalyzer
from gui.styles import AppTheme


class GantryView(ttk.Frame):
    """Visualizes Gantry angle trajectory and positional error curves."""

    def __init__(self, parent, on_time_selected: Optional[Callable[[float], None]] = None, **kwargs):
        super().__init__(parent, **kwargs)
        self.on_time_selected = on_time_selected
        self.analyzer: Optional[TRFAnalyzer] = None

        self.fig = Figure(figsize=(6, 4.5), dpi=100)
        self.fig.patch.set_facecolor(AppTheme.BG_MAIN)

        self.ax1 = self.fig.add_subplot(2, 1, 1)
        self.ax2 = self.fig.add_subplot(2, 1, 2, sharex=self.ax1)
        self.fig.tight_layout(pad=2.5)

        self.canvas = FigureCanvasTkAgg(self.fig, master=self)
        self.canvas_widget = self.canvas.get_tk_widget()
        self.canvas_widget.pack(fill="both", expand=True)

        self.cursor1 = None
        self.cursor2 = None
        self.canvas.mpl_connect("button_press_event", self._on_click)

    def set_analyzer(self, analyzer: TRFAnalyzer) -> None:
        """Plots Gantry angle and error data from the analyzer."""
        self.analyzer = analyzer
        df = analyzer.df

        self.ax1.clear()
        self.ax2.clear()

        times = df.index.to_numpy()
        gantry_act_col = analyzer.dataset.gantry_actual_col
        gantry_err_col = analyzer.dataset.gantry_error_col

        if gantry_act_col and gantry_act_col in df:
            gantry_act = df[gantry_act_col].to_numpy()
            self.ax1.plot(times, gantry_act, color="#0284c7", linewidth=1.8, label="Actual Gantry Angle")

            # If error is available, plot planned
            if gantry_err_col and gantry_err_col in df:
                gantry_err = df[gantry_err_col].to_numpy()
                gantry_plan = gantry_act - gantry_err
                self.ax1.plot(times, gantry_plan, color="#64748b", linestyle="--", linewidth=1.2, label="Planned Gantry")
            self.ax1.set_ylabel("Gantry Angle (°)", fontsize=9, fontweight="bold")
            self.ax1.set_title("Gantry Position Trajectory", fontsize=10, fontweight="bold")
            self.ax1.grid(True, linestyle=":", alpha=0.6)
            self.ax1.legend(loc="upper right", fontsize=8)

        if gantry_err_col and gantry_err_col in df:
            gantry_err = df[gantry_err_col].to_numpy()
            self.ax2.plot(times, gantry_err, color="#dc2626", linewidth=1.2, label="Positional Error")
            # Shaded tolerance bands
            self.ax2.axhline(0, color="#94a3b8", linewidth=0.8)
            self.ax2.axhline(1.0, color="#d97706", linestyle=":", linewidth=1, label="Warning (±1.0°)")
            self.ax2.axhline(-1.0, color="#d97706", linestyle=":", linewidth=1)
            self.ax2.axhspan(-0.5, 0.5, color="#16a34a", alpha=0.12, label="Nominal (±0.5°)")

            self.ax2.set_xlabel("Time (seconds)", fontsize=9, fontweight="bold")
            self.ax2.set_ylabel("Error (°)", fontsize=9, fontweight="bold")
            self.ax2.set_title("Gantry Positional Error", fontsize=10, fontweight="bold")
            self.ax2.grid(True, linestyle=":", alpha=0.6)
            self.ax2.legend(loc="upper right", fontsize=8)

        # Add vertical cursor lines for timeline tracking
        if len(times) > 0:
            self.cursor1 = self.ax1.axvline(times[0], color="#e11d48", linestyle="-", linewidth=1.5, alpha=0.85)
            self.cursor2 = self.ax2.axvline(times[0], color="#e11d48", linestyle="-", linewidth=1.5, alpha=0.85)

        self.fig.tight_layout(pad=2.2)
        self.canvas.draw_idle()

    def update_cursor(self, time_s: float) -> None:
        """Moves vertical cursor line to current time."""
        if self.cursor1 and self.cursor2:
            self.cursor1.set_xdata([time_s, time_s])
            self.cursor2.set_xdata([time_s, time_s])
            self.canvas.draw_idle()

    def _on_click(self, event) -> None:
        """Handles click on plot to seek to that timestamp."""
        if event.inaxes in (self.ax1, self.ax2) and event.xdata is not None:
            if self.on_time_selected:
                self.on_time_selected(float(event.xdata))

