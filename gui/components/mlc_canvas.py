"""Interactive 2D Beam's Eye View (BEV) MLC Leaf Shape visualizer."""

import tkinter as tk
from tkinter import ttk
from typing import Callable, Dict, List, Optional
from datetime import datetime, timedelta
import math
from core.trf_analyzer import TRFAnalyzer
from gui.styles import AppTheme


# Elekta Unity MR-Linac Collimation Geometry Constants
UNITY_SAD_MM = 1435.0          # Source-to-Axis Distance (143.5 cm)
UNITY_LEAF_COUNT = 80          # 80 leaf pairs (160 leaves total)
UNITY_FIELD_STACK_MM = 574.0   # Max field dimension across leaf stack (57.4 cm, cross-plane)
UNITY_LEAF_WIDTH_MM = UNITY_FIELD_STACK_MM / UNITY_LEAF_COUNT  # 7.175 mm leaf width at isocenter
UNITY_FIELD_TRAVEL_MM = 220.0  # Max active field dimension in leaf travel direction (22.0 cm, in-plane)
UNITY_TRAVEL_LIMIT_MM = UNITY_FIELD_TRAVEL_MM / 2.0  # +/- 110.0 mm active field boundary from isocenter
UNITY_PARK_WALL_MM = 165.0     # Leaf carriage / retraction park wall boundary (+/- 165.0 mm)
UNITY_STACK_LIMIT_MM = UNITY_FIELD_STACK_MM / 2.0    # +/- 287.0 mm leaf stack boundary from isocenter

# BEV Scaled Fonts (1.5x larger for high visibility)
FONT_BEV_HEADER_BOLD = ("Segoe UI", 14, "bold")
FONT_BEV_HEADER = ("Segoe UI", 14)
FONT_BEV_MONO = ("Consolas", 14)
FONT_BEV_LABEL = ("Segoe UI", 12)
FONT_BEV_LABEL_BOLD = ("Segoe UI", 12, "bold")
FONT_BEV_CANVAS_LARGE = ("Segoe UI", 14, "bold")
FONT_BEV_CANVAS_MEDIUM = ("Segoe UI", 12, "bold")
FONT_BEV_CANVAS_SMALL = ("Segoe UI", 12)
FONT_BEV_DT_LABEL = ("Segoe UI", 11)
FONT_BEV_DT_LABEL_BOLD = ("Segoe UI", 11, "bold")
FONT_BEV_DT_VAL = ("Consolas", 11)
FONT_BEV_DT_VAL_BOLD = ("Consolas", 11, "bold")
FONT_BEV_GATE_LABEL = ("Segoe UI", 13, "bold")
FONT_BEV_GATE_STATUS = ("Segoe UI", 10, "bold")


class MLCCanvas(ttk.Frame):
    """Visualizes Agility MLC 80 leaf pairs, jaws, aperture, and errors in real-time."""

    def __init__(self, parent, on_frame_changed: Optional[Callable[[int], None]] = None, **kwargs):
        super().__init__(parent, **kwargs)
        self.on_frame_changed = on_frame_changed
        self.analyzer: Optional[TRFAnalyzer] = None
        self.current_frame = 0
        self.total_frames = 0
        self.is_playing = False
        self.play_speed = 1.0  # multiplier
        self._anim_job: Optional[str] = None
        self.start_datetime: Optional[datetime] = None
        self.current_datetime: Optional[datetime] = None
        self.end_datetime: Optional[datetime] = None
        self.current_dose_rate: float = 0.0
        self.current_gating: bool = False
        self.current_gantry_angle: float = 0.0
        self.current_gantry_error: float = 0.0

        # Display parameters (mm to pixels)
        self.canvas_width = 540
        self.canvas_height = 540
        self.scale = 1.0
        self.cx = self.canvas_width / 2.0
        self.cy = self.canvas_height / 2.0
        self.y2_orientation = "Top"  # "Top", "Bottom", "Right", or "Left"
        self._update_scale()

        self._build_ui()

    def _update_scale(self) -> None:
        """Calculates isotropic scaling factor to fit 57.4 cm x 22.0 cm field (plus leaf park margins)."""
        w = max(50, self.canvas_width)
        h = max(50, self.canvas_height)

        if self.y2_orientation in ("Right", "Left"):
            # Leaf travel is horizontal (~360 mm span), leaf stack is vertical (~614 mm span)
            span_x = (UNITY_PARK_WALL_MM * 2.0) + 40.0
            span_y = UNITY_FIELD_STACK_MM + 55.0
        else:
            # Leaf stack is horizontal (~614 mm span), leaf travel is vertical (~360 mm span)
            span_x = UNITY_FIELD_STACK_MM + 55.0
            span_y = (UNITY_PARK_WALL_MM * 2.0) + 40.0

        if w >= 800:
            # Reserve space on the right for treatment timestamps block on the blue background
            right_panel_px = 280.0
            w_avail = w - right_panel_px
            self.cx = max(100.0, (w_avail / 2.0) + 15.0)
            self.cy = h / 2.0
            scale_x = max(10.0, w_avail - 30.0) / span_x
        else:
            self.cx = w / 2.0
            self.cy = h / 2.0
            scale_x = max(10.0, w - 30.0) / span_x

        scale_y = max(10.0, h - 30.0) / span_y
        self.scale = max(0.1, min(scale_x, scale_y))

    def _build_ui(self) -> None:
        """Constructs canvas and animation controls."""
        # Top info header (1.5x larger text)
        self.info_frame = ttk.Frame(self)
        self.info_frame.pack(fill="x", padx=6, pady=(2, 6))

        self.lbl_time = ttk.Label(self.info_frame, text="Time: 0.00 s", font=FONT_BEV_HEADER_BOLD)
        self.lbl_time.pack(side="left", padx=8)

        self.lbl_gantry = ttk.Label(self.info_frame, text="Gantry: --°", font=FONT_BEV_HEADER_BOLD)
        self.lbl_gantry.pack(side="left", padx=14)

        self.lbl_mu = ttk.Label(self.info_frame, text="MU: 0.0", font=FONT_BEV_HEADER)
        self.lbl_mu.pack(side="left", padx=8)

        self.lbl_x1 = ttk.Label(self.info_frame, text="X1: -- mm", font=FONT_BEV_HEADER_BOLD, foreground="#ef4444")
        self.lbl_x1.pack(side="left", padx=10)

        self.lbl_x2 = ttk.Label(self.info_frame, text="X2: -- mm", font=FONT_BEV_HEADER_BOLD, foreground="#22c55e")
        self.lbl_x2.pack(side="left", padx=10)

        self.lbl_hover = ttk.Label(self.info_frame, text="", font=FONT_BEV_MONO, foreground=AppTheme.TEXT_SECONDARY)
        self.lbl_hover.pack(side="right", padx=12)

        # Compatibility labels for unit tests & headless inspectors
        self.lbl_tx_start = ttk.Label(self, text="--")
        self.lbl_tx_cp = ttk.Label(self, text="--")
        self.lbl_tx_end = ttk.Label(self, text="--")
        self.lbl_dose_rate = ttk.Label(self, text="--")
        self.lbl_gating = ttk.Label(self, text="DISABLED")
        self.lbl_gantry_angle = ttk.Label(self, text="0.0°")

        # Scrubber bar pinned to the bottom (always visible)
        self.ctrl_frame = ttk.Frame(self, style="Card.TFrame", padding=(8, 6))
        self.ctrl_frame.pack(side="bottom", fill="x", padx=6, pady=(2, 4))

        # Buttons
        self.btn_first = ttk.Button(self.ctrl_frame, text="⏮", width=3, style="Secondary.TButton", command=self.seek_first)
        self.btn_first.pack(side="left", padx=2)

        self.btn_prev = ttk.Button(self.ctrl_frame, text="◀", width=3, style="Secondary.TButton", command=lambda: self.step_prev(1))
        self.btn_prev.pack(side="left", padx=2)

        self.btn_play = ttk.Button(self.ctrl_frame, text="▶ Play", width=8, style="Primary.TButton", command=self.toggle_play)
        self.btn_play.pack(side="left", padx=4)

        self.btn_next = ttk.Button(self.ctrl_frame, text="▶", width=3, style="Secondary.TButton", command=lambda: self.step_next(1))
        self.btn_next.pack(side="left", padx=2)

        self.btn_last = ttk.Button(self.ctrl_frame, text="⏭", width=3, style="Secondary.TButton", command=self.seek_last)
        self.btn_last.pack(side="left", padx=2)

        # Time slider (scrub by clicking or dragging)
        self.slider_var = tk.DoubleVar(value=0)
        self.slider = ttk.Scale(
            self.ctrl_frame,
            from_=0,
            to=100,
            orient="horizontal",
            variable=self.slider_var,
            command=self._on_slider_change
        )
        self.slider.pack(side="left", fill="x", expand=True, padx=8)

        # Step / Frame Counter
        self.lbl_step_counter = ttk.Label(self.ctrl_frame, text="Step: 0 / 0", font=FONT_BEV_MONO, width=22)
        self.lbl_step_counter.pack(side="left", padx=6)

        # Speed Dropdown
        ttk.Label(self.ctrl_frame, text="Speed:", font=FONT_BEV_LABEL_BOLD).pack(side="left", padx=(8, 3))
        self.speed_combo = ttk.Combobox(self.ctrl_frame, values=["1x", "2x", "5x", "10x"], width=5, state="readonly", font=FONT_BEV_LABEL)
        self.speed_combo.set("1x")
        self.speed_combo.bind("<<ComboboxSelected>>", self._on_speed_changed)
        self.speed_combo.pack(side="left", padx=2)

        # Y2 Bank Position Dropdown
        ttk.Label(self.ctrl_frame, text="Y2 Bank:", font=FONT_BEV_LABEL_BOLD).pack(side="left", padx=(10, 3))
        self.y2_combo = ttk.Combobox(self.ctrl_frame, values=["Top", "Bottom", "Right", "Left"], width=7, state="readonly", font=FONT_BEV_LABEL)
        self.y2_combo.set("Top")
        self.y2_combo.bind("<<ComboboxSelected>>", self._on_y2_orientation_changed)
        self.y2_combo.pack(side="left", padx=2)

        # Canvas with Card border taking remaining central area
        self.canvas_card = ttk.Frame(self, style="Card.TFrame")
        self.canvas_card.pack(side="top", fill="both", expand=True, padx=4, pady=2)

        self.canvas = tk.Canvas(
            self.canvas_card,
            bg="#0f172a",  # Deep dark background for high contrast
            highlightthickness=0
        )
        self.canvas.pack(fill="both", expand=True, padx=4, pady=4)

        self.canvas.bind("<Configure>", self._on_resize)
        self.canvas.bind("<Motion>", self._on_mouse_hover)
        self.canvas.bind("<MouseWheel>", self._on_mouse_wheel)

        # Global keyboard shortcuts when viewing
        self.bind("<Left>", lambda e: self.step_prev(5))
        self.bind("<Right>", lambda e: self.step_next(5))

        # Initial background draw
        self._draw_axes()

    @staticmethod
    def _parse_datetime(date_str: str) -> Optional[datetime]:
        """Parses a TRF date string into a datetime object."""
        if not date_str or not date_str.strip():
            return None
        s = date_str.strip()
        try:
            from dateutil import parser
            return parser.parse(s, yearfirst=True)
        except Exception:
            pass
        for fmt in ("%y/%m/%d %H:%M:%S", "%Y-%m-%d %H:%M:%S", "%Y/%m/%d %H:%M:%S", "%d/%m/%Y %H:%M:%S"):
            try:
                clean = s.rstrip(" Z").strip()
                return datetime.strptime(clean, fmt)
            except Exception:
                continue
        return None

    def set_analyzer(self, analyzer: TRFAnalyzer) -> None:
        """Loads dataset and initializes timeline."""
        self.analyzer = analyzer
        self.total_frames = len(analyzer.df)
        self.current_frame = 0
        self.slider.config(to=max(0, self.total_frames - 1))
        self.slider_var.set(0)
        self.lbl_step_counter.config(text=f"Step: 1 / {self.total_frames}")

        # Compute Start and End datetimes
        header_date = getattr(analyzer.dataset.header, "date", "") if analyzer.dataset else ""
        self.start_datetime = self._parse_datetime(header_date)
        if self.start_datetime and len(analyzer.df) > 0:
            t0 = float(analyzer.df.index[0])
            t_end = float(analyzer.df.index[-1])
            duration_s = max(0.0, t_end - t0)
            self.end_datetime = self.start_datetime + timedelta(seconds=duration_s)
            self.current_datetime = self.start_datetime
            self.lbl_tx_start.config(text=self.start_datetime.strftime("%Y-%m-%d %H:%M:%S"))
            self.lbl_tx_end.config(text=self.end_datetime.strftime("%Y-%m-%d %H:%M:%S"))
        else:
            self.end_datetime = None
            self.current_datetime = None
            self.lbl_tx_start.config(text="--")
            self.lbl_tx_end.config(text="--")

        self.render_current_frame()

    def render_current_frame(self) -> None:
        """Renders the MLC leaves and jaws at current frame."""
        if not self.analyzer or self.total_frames == 0:
            return

        frame_data = self.analyzer.get_aperture_at_index(self.current_frame)
        self._update_readout(frame_data)
        self._draw_mlc(frame_data)

        if self.on_frame_changed:
            self.on_frame_changed(self.current_frame)

    def _update_readout(self, data: Dict) -> None:
        """Updates numeric labels."""
        self.lbl_time.config(text=f"Time: {data['time_s']:.2f} s")
        err_str = f" (Err: {data['gantry_error']:+.2f}°)" if abs(data['gantry_error']) > 0.01 else ""
        self.lbl_gantry.config(text=f"Gantry: {data['gantry_angle']:.1f}°{err_str}")
        self.lbl_mu.config(text=f"MU: {data['mu']:.1f}")
        raw_x1 = data.get("x1_jaw", UNITY_STACK_LIMIT_MM)
        raw_x2 = data.get("x2_jaw", UNITY_STACK_LIMIT_MM)
        self.lbl_x1.config(text=f"X1: {raw_x1:.1f} mm")
        self.lbl_x2.config(text=f"X2: {raw_x2:.1f} mm")

        # Update Current Control Point Date & Time
        if self.start_datetime and self.analyzer and len(self.analyzer.df) > 0:
            t0 = float(self.analyzer.df.index[0])
            t_curr = max(0.0, data["time_s"] - t0)
            self.current_datetime = self.start_datetime + timedelta(seconds=t_curr)
            self.lbl_tx_cp.config(text=self.current_datetime.strftime("%Y-%m-%d %H:%M:%S"))
        else:
            self.current_datetime = None
            self.lbl_tx_cp.config(text="--")

        # Update Current Dose Rate (MU/min)
        self.current_dose_rate = float(data.get("dose_rate", 0.0))

        # Update Current Gating State
        self.current_gating = bool(data.get("gating", False))
        self.lbl_gating.config(text="ENABLED" if self.current_gating else "DISABLED")

        # Update Current Gantry Angle & Error
        self.current_gantry_angle = float(data.get("gantry_angle", 0.0))
        self.current_gantry_error = float(data.get("gantry_error", 0.0))
        self.lbl_gantry_angle.config(text=f"{self.current_gantry_angle:.1f}°")

    def _draw_axes(self) -> None:
        """Draws isocenter crosshairs, 50mm grid ticks, and the 57.4 x 22.0 cm field frame."""
        self.canvas.delete("all")
        w = self.canvas_width
        h = self.canvas_height

        # Grid lines (every 50 mm)
        step_50 = 50.0 * self.scale
        for i in range(-5, 6):
            if i == 0:
                continue
            offset = i * step_50
            x = self.cx + offset
            y = self.cy + offset
            dash_pat = (1, 3) if abs(i) % 2 != 0 else (2, 4)
            color = "#172554" if abs(i) % 2 != 0 else "#1e293b"
            if 0 <= x <= w:
                self.canvas.create_line(x, 0, x, h, fill=color, dash=dash_pat, tags="grid")
            if 0 <= y <= h:
                self.canvas.create_line(0, y, w, y, fill=color, dash=dash_pat, tags="grid")

        # Center Crosshairs
        self.canvas.create_line(self.cx, 0, self.cx, h, fill=AppTheme.MLC_CROSSHAIR, width=1, dash=(4, 4), tags="grid")
        self.canvas.create_line(0, self.cy, w, self.cy, fill=AppTheme.MLC_CROSSHAIR, width=1, dash=(4, 4), tags="grid")

        # Elekta Unity 57.4 cm x 22.0 cm Maximum Collimator Field Boundary
        if self.y2_orientation in ("Right", "Left"):
            fx1 = self.cx - (UNITY_TRAVEL_LIMIT_MM * self.scale)
            fx2 = self.cx + (UNITY_TRAVEL_LIMIT_MM * self.scale)
            fy1 = self.cy - (UNITY_STACK_LIMIT_MM * self.scale)
            fy2 = self.cy + (UNITY_STACK_LIMIT_MM * self.scale)

            # Max active field boundary (22.0 cm x 57.4 cm)
            self.canvas.create_rectangle(fx1, fy1, fx2, fy2, outline="#475569", width=1, dash=(4, 4), tags="grid")

            # Carriage park / retraction guidelines
            px1 = self.cx - (UNITY_PARK_WALL_MM * self.scale)
            px2 = self.cx + (UNITY_PARK_WALL_MM * self.scale)
            self.canvas.create_line(px1, fy1 - 6, px1, fy2 + 6, fill="#334155", width=1, dash=(2, 3), tags="grid")
            self.canvas.create_line(px2, fy1 - 6, px2, fy2 + 6, fill="#334155", width=1, dash=(2, 3), tags="grid")

            # Field dimension label
            self.canvas.create_text(self.cx, fy1 - 12, text="Max Field: 22.0 × 57.4 cm (Elekta Unity)", fill="#64748b", font=FONT_BEV_CANVAS_SMALL, anchor="s", tags="grid")
        else:
            fx1 = self.cx - (UNITY_STACK_LIMIT_MM * self.scale)
            fx2 = self.cx + (UNITY_STACK_LIMIT_MM * self.scale)
            fy1 = self.cy - (UNITY_TRAVEL_LIMIT_MM * self.scale)
            fy2 = self.cy + (UNITY_TRAVEL_LIMIT_MM * self.scale)

            # Max active field boundary (57.4 cm x 22.0 cm)
            self.canvas.create_rectangle(fx1, fy1, fx2, fy2, outline="#475569", width=1, dash=(4, 4), tags="grid")

            # Carriage park / retraction guidelines
            py1 = self.cy - (UNITY_PARK_WALL_MM * self.scale)
            py2 = self.cy + (UNITY_PARK_WALL_MM * self.scale)
            self.canvas.create_line(fx1 - 6, py1, fx2 + 6, py1, fill="#334155", width=1, dash=(2, 3), tags="grid")
            self.canvas.create_line(fx1 - 6, py2, fx2 + 6, py2, fill="#334155", width=1, dash=(2, 3), tags="grid")

            # Field dimension label
            self.canvas.create_text(self.cx, fy1 - 12, text="Max Field: 57.4 × 22.0 cm (Elekta Unity)", fill="#64748b", font=FONT_BEV_CANVAS_SMALL, anchor="s", tags="grid")

        # Always draw treatment timestamps, dose rate bar, and gantry indicator on the blue background to the right of the MLC display
        self._draw_datetimes()
        self._draw_doserate(self.current_dose_rate, self.current_gating)
        self._draw_gantry(self.current_gantry_angle, self.current_gantry_error)

    def _on_y2_orientation_changed(self, event=None) -> None:
        """Handles change in Y2 bank orientation (Right, Left, Top, Bottom)."""
        new_ori = self.y2_combo.get()
        if new_ori in ("Right", "Left", "Top", "Bottom"):
            self.y2_orientation = new_ori
            self._update_scale()
            self._draw_axes()
            if self.analyzer and self.total_frames > 0:
                self.render_current_frame()

    def _draw_mlc(self, data: Dict) -> None:
        """Draws all 80 leaf pairs and aperture opening according to y2_orientation."""
        self.canvas.delete("leaf")
        self.canvas.delete("aperture")
        self.canvas.delete("jaw")

        y1_positions = data["y1_pos"]
        y2_positions = data["y2_pos"]
        y1_errors = data.get("y1_err", [])
        y2_errors = data.get("y2_err", [])

        num_leaves = min(len(y1_positions), len(y2_positions), UNITY_LEAF_COUNT)
        if num_leaves == 0:
            return

        leaf_size_px = UNITY_LEAF_WIDTH_MM * self.scale
        raw_x1 = data.get("x1_jaw", UNITY_STACK_LIMIT_MM)
        raw_x2 = data.get("x2_jaw", UNITY_STACK_LIMIT_MM)

        ori = self.y2_orientation

        if ori in ("Right", "Left"):
            # Horizontal leaf travel (along X axis), vertical leaf stack (along Y axis)
            left_wall_px = self.cx - (UNITY_PARK_WALL_MM * self.scale)
            right_wall_px = self.cx + (UNITY_PARK_WALL_MM * self.scale)
            top_limit_px = self.cy - (UNITY_STACK_LIMIT_MM * self.scale)
            bot_limit_px = self.cy + (UNITY_STACK_LIMIT_MM * self.scale)

            for i in range(num_leaves):
                y_top_px = top_limit_px + i * leaf_size_px
                y_bot_px = y_top_px + leaf_size_px

                y1_val = y1_positions[i]
                y2_val = y2_positions[i]
                y1_err = abs(y1_errors[i]) if i < len(y1_errors) else 0.0
                y2_err = abs(y2_errors[i]) if i < len(y2_errors) else 0.0

                color_y1 = AppTheme.MLC_ERROR_FAIL if y1_err > 2.0 else (AppTheme.MLC_ERROR_WARN if y1_err > 1.0 else AppTheme.MLC_Y1)
                color_y2 = AppTheme.MLC_ERROR_FAIL if y2_err > 2.0 else (AppTheme.MLC_ERROR_WARN if y2_err > 1.0 else AppTheme.MLC_Y2)

                if ori == "Right":
                    # Y1 from left wall, Y2 from right wall
                    y1_tip_px = self.cx + (y1_val * self.scale)
                    y2_tip_px = self.cx + (y2_val * self.scale)

                    if y1_tip_px < y2_tip_px:
                        self.canvas.create_rectangle(y1_tip_px, y_top_px, y2_tip_px, y_bot_px, fill=AppTheme.MLC_APERTURE, outline="", tags="aperture")
                    self.canvas.create_rectangle(left_wall_px, y_top_px, y1_tip_px, y_bot_px, fill=color_y1, outline="#1e293b", width=1, tags=("leaf", f"leaf_y1_{i+1}"))
                    self.canvas.create_rectangle(y2_tip_px, y_top_px, right_wall_px, y_bot_px, fill=color_y2, outline="#1e293b", width=1, tags=("leaf", f"leaf_y2_{i+1}"))
                else:
                    # Y2 from left wall, Y1 from right wall
                    y2_tip_px = self.cx - (y2_val * self.scale)
                    y1_tip_px = self.cx - (y1_val * self.scale)

                    if y2_tip_px < y1_tip_px:
                        self.canvas.create_rectangle(y2_tip_px, y_top_px, y1_tip_px, y_bot_px, fill=AppTheme.MLC_APERTURE, outline="", tags="aperture")
                    self.canvas.create_rectangle(left_wall_px, y_top_px, y2_tip_px, y_bot_px, fill=color_y2, outline="#1e293b", width=1, tags=("leaf", f"leaf_y2_{i+1}"))
                    self.canvas.create_rectangle(y1_tip_px, y_top_px, right_wall_px, y_bot_px, fill=color_y1, outline="#1e293b", width=1, tags=("leaf", f"leaf_y1_{i+1}"))

            # Diaphragms for horizontal leaves (Horizontal Red/Green lines at Top and Bottom)
            y1_px = self.cy - (raw_x1 * self.scale)
            y2_px = self.cy + (raw_x2 * self.scale)

            # Shading for X1 Diaphragm (blocks from top limit down to y1_px)
            clamp_y1 = max(top_limit_px, min(y1_px, bot_limit_px))
            if clamp_y1 > top_limit_px:
                self.canvas.create_rectangle(left_wall_px - 4, top_limit_px, right_wall_px + 4, clamp_y1, fill="#0f172a", stipple="gray50", outline="", tags="jaw")

            # Shading for X2 Diaphragm (blocks from y2_px down to bottom limit)
            clamp_y2 = max(top_limit_px, min(y2_px, bot_limit_px))
            if clamp_y2 < bot_limit_px:
                self.canvas.create_rectangle(left_wall_px - 4, clamp_y2, right_wall_px + 4, bot_limit_px, fill="#0f172a", stipple="gray50", outline="", tags="jaw")

            if top_limit_px <= y1_px <= bot_limit_px:
                self.canvas.create_line(left_wall_px - 8, y1_px, right_wall_px + 8, y1_px, fill="#ef4444", width=2, tags="jaw")
            if top_limit_px <= y2_px <= bot_limit_px:
                self.canvas.create_line(left_wall_px - 8, y2_px, right_wall_px + 8, y2_px, fill="#22c55e", width=2, tags="jaw")

            x1_label_y = y1_px - 14 if (y1_px - 14) > (top_limit_px + 8) else y1_px + 16
            self.canvas.create_text(self.cx, x1_label_y, text=f"▲ X1 Diaphragm ({raw_x1:.1f} mm)", fill="#f87171", font=FONT_BEV_CANVAS_LARGE, anchor="center", tags="jaw")
            x2_label_y = y2_px + 14 if (y2_px + 14) < (bot_limit_px - 8) else y2_px - 16
            self.canvas.create_text(self.cx, x2_label_y, text=f"▼ X2 Diaphragm ({raw_x2:.1f} mm)", fill="#4ade80", font=FONT_BEV_CANVAS_LARGE, anchor="center", tags="jaw")

            if ori == "Right":
                self.canvas.create_text(left_wall_px + 50, top_limit_px - 12, text="◀ Bank Y1", fill="#60a5fa", font=FONT_BEV_CANVAS_LARGE, anchor="s", tags="jaw")
                self.canvas.create_text(right_wall_px - 50, top_limit_px - 12, text="Bank Y2 ▶", fill="#22d3ee", font=FONT_BEV_CANVAS_LARGE, anchor="s", tags="jaw")
            else:
                self.canvas.create_text(left_wall_px + 50, top_limit_px - 12, text="◀ Bank Y2", fill="#22d3ee", font=FONT_BEV_CANVAS_LARGE, anchor="s", tags="jaw")
                self.canvas.create_text(right_wall_px - 50, top_limit_px - 12, text="Bank Y1 ▶", fill="#60a5fa", font=FONT_BEV_CANVAS_LARGE, anchor="s", tags="jaw")

        else:
            # Vertical leaf travel (along Y axis) - Top or Bottom
            top_wall_px = self.cy - (UNITY_PARK_WALL_MM * self.scale)
            bot_wall_px = self.cy + (UNITY_PARK_WALL_MM * self.scale)
            left_limit_px = self.cx - (UNITY_STACK_LIMIT_MM * self.scale)
            right_limit_px = self.cx + (UNITY_STACK_LIMIT_MM * self.scale)

            for i in range(num_leaves):
                y1_val = y1_positions[i]
                y2_val = y2_positions[i]
                y1_err = abs(y1_errors[i]) if i < len(y1_errors) else 0.0
                y2_err = abs(y2_errors[i]) if i < len(y2_errors) else 0.0

                color_y1 = AppTheme.MLC_ERROR_FAIL if y1_err > 2.0 else (AppTheme.MLC_ERROR_WARN if y1_err > 1.0 else AppTheme.MLC_Y1)
                color_y2 = AppTheme.MLC_ERROR_FAIL if y2_err > 2.0 else (AppTheme.MLC_ERROR_WARN if y2_err > 1.0 else AppTheme.MLC_Y2)

                if ori == "Top":
                    x_left_px = left_limit_px + i * leaf_size_px
                    x_right_px = x_left_px + leaf_size_px
                    # Y2 from Top wall, Y1 from Bottom wall
                    y2_tip_py = self.cy - (y2_val * self.scale)
                    y1_tip_py = self.cy - (y1_val * self.scale)

                    if y2_tip_py < y1_tip_py:
                        self.canvas.create_rectangle(x_left_px, y2_tip_py, x_right_px, y1_tip_py, fill=AppTheme.MLC_APERTURE, outline="", tags="aperture")
                    self.canvas.create_rectangle(x_left_px, top_wall_px, x_right_px, y2_tip_py, fill=color_y2, outline="#1e293b", width=1, tags=("leaf", f"leaf_y2_{i+1}"))
                    self.canvas.create_rectangle(x_left_px, y1_tip_py, x_right_px, bot_wall_px, fill=color_y1, outline="#1e293b", width=1, tags=("leaf", f"leaf_y1_{i+1}"))
                else:
                    x_left_px = right_limit_px - (i + 1) * leaf_size_px
                    x_right_px = x_left_px + leaf_size_px
                    # Y1 from Top wall, Y2 from Bottom wall
                    y1_tip_py = self.cy + (y1_val * self.scale)
                    y2_tip_py = self.cy + (y2_val * self.scale)

                    if y1_tip_py < y2_tip_py:
                        self.canvas.create_rectangle(x_left_px, y1_tip_py, x_right_px, y2_tip_py, fill=AppTheme.MLC_APERTURE, outline="", tags="aperture")
                    self.canvas.create_rectangle(x_left_px, top_wall_px, x_right_px, y1_tip_py, fill=color_y1, outline="#1e293b", width=1, tags=("leaf", f"leaf_y1_{i+1}"))
                    self.canvas.create_rectangle(x_left_px, y2_tip_py, x_right_px, bot_wall_px, fill=color_y2, outline="#1e293b", width=1, tags=("leaf", f"leaf_y2_{i+1}"))

            # Diaphragms for vertical leaves (Vertical lines on Left and Right)
            if ori == "Top":
                x1_px = self.cx - (raw_x1 * self.scale)
                x2_px = self.cx + (raw_x2 * self.scale)

                clamp_x1 = max(left_limit_px, min(x1_px, right_limit_px))
                if clamp_x1 > left_limit_px:
                    self.canvas.create_rectangle(left_limit_px, top_wall_px - 4, clamp_x1, bot_wall_px + 4, fill="#0f172a", stipple="gray50", outline="", tags="jaw")
                clamp_x2 = max(left_limit_px, min(x2_px, right_limit_px))
                if clamp_x2 < right_limit_px:
                    self.canvas.create_rectangle(clamp_x2, top_wall_px - 4, right_limit_px, bot_wall_px + 4, fill="#0f172a", stipple="gray50", outline="", tags="jaw")

                if left_limit_px <= x1_px <= right_limit_px:
                    self.canvas.create_line(x1_px, top_wall_px - 8, x1_px, bot_wall_px + 8, fill="#ef4444", width=2, tags="jaw")
                if left_limit_px <= x2_px <= right_limit_px:
                    self.canvas.create_line(x2_px, top_wall_px - 8, x2_px, bot_wall_px + 8, fill="#22c55e", width=2, tags="jaw")

                self.canvas.create_text(x1_px, top_wall_px - 12, text=f"◀ X1 ({raw_x1:.1f} mm)", fill="#f87171", font=FONT_BEV_CANVAS_MEDIUM, anchor="s", tags="jaw")
                self.canvas.create_text(x2_px, top_wall_px - 12, text=f"X2 ({raw_x2:.1f} mm) ▶", fill="#4ade80", font=FONT_BEV_CANVAS_MEDIUM, anchor="s", tags="jaw")

                self.canvas.create_text(self.cx, top_wall_px + 20, text="▲ Bank Y2", fill="#22d3ee", font=FONT_BEV_CANVAS_LARGE, anchor="center", tags="jaw")
                self.canvas.create_text(self.cx, bot_wall_px - 20, text="Bank Y1 ▼", fill="#60a5fa", font=FONT_BEV_CANVAS_LARGE, anchor="center", tags="jaw")
            else:
                x1_px = self.cx + (raw_x1 * self.scale)
                x2_px = self.cx - (raw_x2 * self.scale)

                clamp_x2 = max(left_limit_px, min(x2_px, right_limit_px))
                if clamp_x2 > left_limit_px:
                    self.canvas.create_rectangle(left_limit_px, top_wall_px - 4, clamp_x2, bot_wall_px + 4, fill="#0f172a", stipple="gray50", outline="", tags="jaw")
                clamp_x1 = max(left_limit_px, min(x1_px, right_limit_px))
                if clamp_x1 < right_limit_px:
                    self.canvas.create_rectangle(clamp_x1, top_wall_px - 4, right_limit_px, bot_wall_px + 4, fill="#0f172a", stipple="gray50", outline="", tags="jaw")

                if left_limit_px <= x2_px <= right_limit_px:
                    self.canvas.create_line(x2_px, top_wall_px - 8, x2_px, bot_wall_px + 8, fill="#22c55e", width=2, tags="jaw")
                if left_limit_px <= x1_px <= right_limit_px:
                    self.canvas.create_line(x1_px, top_wall_px - 8, x1_px, bot_wall_px + 8, fill="#ef4444", width=2, tags="jaw")

                self.canvas.create_text(x2_px, top_wall_px - 12, text=f"◀ X2 ({raw_x2:.1f} mm)", fill="#4ade80", font=FONT_BEV_CANVAS_MEDIUM, anchor="s", tags="jaw")
                self.canvas.create_text(x1_px, top_wall_px - 12, text=f"X1 ({raw_x1:.1f} mm) ▶", fill="#f87171", font=FONT_BEV_CANVAS_MEDIUM, anchor="s", tags="jaw")

                self.canvas.create_text(self.cx, top_wall_px + 20, text="▲ Bank Y1", fill="#60a5fa", font=FONT_BEV_CANVAS_LARGE, anchor="center", tags="jaw")
                self.canvas.create_text(self.cx, bot_wall_px - 20, text="Bank Y2 ▼", fill="#22d3ee", font=FONT_BEV_CANVAS_LARGE, anchor="center", tags="jaw")

        # Always draw treatment timestamps, dose rate bar, and gantry indicator on the blue background to the right of the MLC display
        self._draw_datetimes()
        self._draw_doserate(self.current_dose_rate, self.current_gating)
        self._draw_gantry(self.current_gantry_angle, self.current_gantry_error)

    def _draw_datetimes(self) -> None:
        """Draws treatment timestamps to the right of the MLC display on top of the blue canvas background."""
        self.canvas.delete("datetime")

        w = self.canvas_width
        if self.y2_orientation in ("Right", "Left"):
            mlc_right_px = self.cx + (UNITY_PARK_WALL_MM * self.scale)
        else:
            mlc_right_px = self.cx + (UNITY_STACK_LIMIT_MM * self.scale)

        # Position to the right of the MLC display on top of the blue background
        if w >= 800:
            x_label = max(mlc_right_px + 28.0, w - 275.0)
        else:
            x_label = max(10.0, w - 270.0)

        x_val = x_label + 95.0
        y_base = 20.0

        # Subtle translucent / dark navy card on the blue background
        box_pad = 12.0
        box_w = 270.0
        box_h = 84.0
        self.canvas.create_rectangle(
            x_label - box_pad,
            y_base - 8.0,
            x_label - box_pad + box_w,
            y_base - 8.0 + box_h,
            fill="#131d35",
            outline="#334155",
            width=1,
            tags="datetime"
        )

        start_str = self.start_datetime.strftime("%Y-%m-%d %H:%M:%S") if self.start_datetime else "--"
        current_str = self.current_datetime.strftime("%Y-%m-%d %H:%M:%S") if self.current_datetime else "--"
        end_str = self.end_datetime.strftime("%Y-%m-%d %H:%M:%S") if self.end_datetime else "--"

        # Update compatibility labels
        self.lbl_tx_start.config(text=start_str)
        self.lbl_tx_cp.config(text=current_str)
        self.lbl_tx_end.config(text=end_str)

        # Row 1: Treatment Start Date & Time
        self.canvas.create_text(
            x_label, y_base + 8.0,
            text="Tx Start:",
            fill="#94a3b8",
            font=FONT_BEV_DT_LABEL_BOLD,
            anchor="w",
            tags="datetime"
        )
        self.canvas.create_text(
            x_val, y_base + 8.0,
            text=start_str,
            fill="#f8fafc",
            font=FONT_BEV_DT_VAL,
            anchor="w",
            tags="datetime"
        )

        # Row 2: Current Control Point Date & Time (Highlighted in cyan/sky blue)
        self.canvas.create_text(
            x_label, y_base + 34.0,
            text="Current CP:",
            fill="#38bdf8",
            font=FONT_BEV_DT_LABEL_BOLD,
            anchor="w",
            tags="datetime"
        )
        self.canvas.create_text(
            x_val, y_base + 34.0,
            text=current_str,
            fill="#38bdf8",
            font=FONT_BEV_DT_VAL_BOLD,
            anchor="w",
            tags="datetime"
        )

        # Row 3: Treatment End Date & Time
        self.canvas.create_text(
            x_label, y_base + 60.0,
            text="Tx End:",
            fill="#94a3b8",
            font=FONT_BEV_DT_LABEL_BOLD,
            anchor="w",
            tags="datetime"
        )
        self.canvas.create_text(
            x_val, y_base + 60.0,
            text=end_str,
            fill="#f8fafc",
            font=FONT_BEV_DT_VAL,
            anchor="w",
            tags="datetime"
        )

    def _draw_doserate(self, dose_rate: float, is_gating: Optional[bool] = None) -> None:
        """Draws current dose rate readout, vertical bar graph (0 - 500 MU/min), and Gating indicator box."""
        self.canvas.delete("doserate")

        if is_gating is not None:
            self.current_gating = is_gating
        else:
            is_gating = self.current_gating

        w = self.canvas_width
        if self.y2_orientation in ("Right", "Left"):
            mlc_right_px = self.cx + (UNITY_PARK_WALL_MM * self.scale)
        else:
            mlc_right_px = self.cx + (UNITY_STACK_LIMIT_MM * self.scale)

        # Position to the right of the MLC display on top of the blue background
        if w >= 800:
            x_label = max(mlc_right_px + 28.0, w - 275.0)
        else:
            x_label = max(10.0, w - 270.0)

        box_pad = 12.0
        box_w = 270.0
        box_x1 = x_label - box_pad
        box_x2 = box_x1 + box_w
        box_y1 = 104.0
        box_h = 190.0
        box_y2 = box_y1 + box_h

        # Translucent dark card
        self.canvas.create_rectangle(
            box_x1, box_y1, box_x2, box_y2,
            fill="#131d35",
            outline="#334155",
            width=1,
            tags="doserate"
        )

        # Update compatibility labels
        rate_str = f"{dose_rate:.1f} MU/min"
        self.lbl_dose_rate.config(text=rate_str)
        self.lbl_gating.config(text="ENABLED" if is_gating else "DISABLED")

        # Row 1: Dose Rate header readout
        self.canvas.create_text(
            box_x1 + 14.0, box_y1 + 16.0,
            text="Dose Rate:",
            fill="#94a3b8",
            font=FONT_BEV_DT_LABEL_BOLD,
            anchor="w",
            tags="doserate"
        )
        rate_color = "#fbbf24" if dose_rate > 0.1 else "#64748b"
        self.canvas.create_text(
            box_x1 + 104.0, box_y1 + 16.0,
            text=rate_str,
            fill=rate_color,
            font=FONT_BEV_DT_VAL_BOLD,
            anchor="w",
            tags="doserate"
        )

        # Vertical bar graph: 0 MU/min (bottom) to 500 MU/min (top)
        bar_x1 = box_x1 + 24.0
        bar_w = 22.0
        bar_x2 = bar_x1 + bar_w
        bar_top_y = box_y1 + 40.0
        bar_bot_y = box_y1 + 170.0
        bar_h = bar_bot_y - bar_top_y

        # Meter background trough
        self.canvas.create_rectangle(
            bar_x1, bar_top_y, bar_x2, bar_bot_y,
            fill="#0b1120",
            outline="#334155",
            width=1,
            tags="doserate"
        )

        # Radiation level fill
        frac = max(0.0, min(1.0, dose_rate / 500.0))
        if frac > 0.0:
            fill_top_y = bar_bot_y - (frac * bar_h)
            # Amber/gold beam color
            self.canvas.create_rectangle(
                bar_x1 + 1, fill_top_y, bar_x2 - 1, bar_bot_y - 1,
                fill="#f59e0b",
                outline="",
                tags="doserate"
            )
            # Bright yellow beam cap line
            self.canvas.create_line(
                bar_x1 + 1, fill_top_y, bar_x2 - 1, fill_top_y,
                fill="#fef08a",
                width=2,
                tags="doserate"
            )
            # Level indicator arrow / pointer on left side
            self.canvas.create_polygon(
                bar_x1 - 2, fill_top_y,
                bar_x1 - 8, fill_top_y - 4,
                bar_x1 - 8, fill_top_y + 4,
                fill="#fbbf24",
                outline="",
                tags="doserate"
            )

        # Scale ticks & labels
        ticks = [
            (500, bar_top_y, "500 MU/min", True),
            (400, bar_bot_y - 0.80 * bar_h, "400", False),
            (300, bar_bot_y - 0.60 * bar_h, "300", False),
            (200, bar_bot_y - 0.40 * bar_h, "200", False),
            (100, bar_bot_y - 0.20 * bar_h, "100", False),
            (0,   bar_bot_y, "0 MU/min", True),
        ]

        for val, ty, lbl, is_major in ticks:
            tick_len = 7 if is_major else 4
            tick_color = "#94a3b8" if is_major else "#475569"
            lbl_color = "#cbd5e1" if is_major else "#64748b"
            lbl_font = ("Segoe UI", 10, "bold") if is_major else ("Segoe UI", 9)

            self.canvas.create_line(
                bar_x2, ty, bar_x2 + tick_len, ty,
                fill=tick_color,
                width=1.5 if is_major else 1,
                tags="doserate"
            )
            self.canvas.create_text(
                bar_x2 + 10.0, ty,
                text=lbl,
                fill=lbl_color,
                font=lbl_font,
                anchor="w",
                tags="doserate"
            )

        # Gating box: located to the right of the bar graph inside the same subwindow
        # Turns bright red (#dc2626) when gating is enabled
        gate_x1 = box_x1 + 148.0
        gate_x2 = box_x1 + 254.0
        gate_y1 = box_y1 + 65.0
        gate_y2 = box_y1 + 145.0

        if is_gating:
            gate_fill = "#dc2626"
            gate_outline = "#ef4444"
            gate_text_color = "#ffffff"
            gate_status_text = "ENABLED"
            gate_status_color = "#fecaca"
            border_w = 2
        else:
            gate_fill = "#0b1120"
            gate_outline = "#334155"
            gate_text_color = "#64748b"
            gate_status_text = "DISABLED"
            gate_status_color = "#475569"
            border_w = 1

        self.canvas.create_rectangle(
            gate_x1, gate_y1, gate_x2, gate_y2,
            fill=gate_fill,
            outline=gate_outline,
            width=border_w,
            tags="doserate"
        )

        gx_center = (gate_x1 + gate_x2) / 2.0
        self.canvas.create_text(
            gx_center, gate_y1 + 26.0,
            text="Gating",
            fill=gate_text_color,
            font=FONT_BEV_GATE_LABEL,
            anchor="center",
            tags="doserate"
        )
        self.canvas.create_text(
            gx_center, gate_y1 + 52.0,
            text=gate_status_text,
            fill=gate_status_color,
            font=FONT_BEV_GATE_STATUS,
            anchor="center",
            tags="doserate"
        )

    def _draw_gantry(self, angle: Optional[float] = None, error: Optional[float] = None) -> None:
        """Draws Gantry angle readout and a black circle with a red arrow pointing towards the center in the gantry direction."""
        self.canvas.delete("gantry_display")

        if angle is not None:
            self.current_gantry_angle = angle
        else:
            angle = self.current_gantry_angle

        if error is not None:
            self.current_gantry_error = error
        else:
            error = self.current_gantry_error

        w = self.canvas_width
        if self.y2_orientation in ("Right", "Left"):
            mlc_right_px = self.cx + (UNITY_PARK_WALL_MM * self.scale)
        else:
            mlc_right_px = self.cx + (UNITY_STACK_LIMIT_MM * self.scale)

        # Position to the right of the MLC display on top of the blue background
        if w >= 800:
            x_label = max(mlc_right_px + 28.0, w - 275.0)
        else:
            x_label = max(10.0, w - 270.0)

        box_pad = 12.0
        box_w = 270.0
        box_x1 = x_label - box_pad
        box_x2 = box_x1 + box_w
        box_y1 = 306.0
        box_h = 175.0
        box_y2 = box_y1 + box_h

        # Translucent dark card
        self.canvas.create_rectangle(
            box_x1, box_y1, box_x2, box_y2,
            fill="#131d35",
            outline="#334155",
            width=1,
            tags="gantry_display"
        )

        # Update compatibility label
        ang_str = f"{angle:.1f}°"
        self.lbl_gantry_angle.config(text=ang_str)

        # Row 1: Gantry Angle header readout
        self.canvas.create_text(
            box_x1 + 14.0, box_y1 + 16.0,
            text="Gantry Angle:",
            fill="#94a3b8",
            font=FONT_BEV_DT_LABEL_BOLD,
            anchor="w",
            tags="gantry_display"
        )

        err_str = f" ({error:+.2f}°)" if abs(error) > 0.01 else ""
        self.canvas.create_text(
            box_x1 + 112.0, box_y1 + 16.0,
            text=f"{ang_str}{err_str}",
            fill="#38bdf8",
            font=FONT_BEV_DT_VAL_BOLD,
            anchor="w",
            tags="gantry_display"
        )

        # Black circle (pure black fill as requested)
        gcx = box_x1 + (box_w / 2.0)
        gcy = box_y1 + 100.0
        R = 46.0

        self.canvas.create_oval(
            gcx - R, gcy - R, gcx + R, gcy + R,
            fill="#000000",
            outline="#475569",
            width=2,
            tags="gantry_display"
        )

        # Cardinal ticks & labels (IEC 61217: 0° Top, 90° Right, 180° Bottom, 270° Left)
        cardinals = [
            (0,   "0°",   0,      -R - 7, "s"),
            (90,  "90°",  R + 7,  0,      "w"),
            (180, "180°", 0,      R + 7,  "n"),
            (270, "270°", -R - 7, 0,      "e"),
        ]
        for c_ang, c_lbl, lx_off, ly_off, anc in cardinals:
            rad_c = math.radians(c_ang)
            tx1 = gcx + (R - 4.0) * math.sin(rad_c)
            ty1 = gcy - (R - 4.0) * math.cos(rad_c)
            tx2 = gcx + R * math.sin(rad_c)
            ty2 = gcy - R * math.cos(rad_c)
            self.canvas.create_line(tx1, ty1, tx2, ty2, fill="#64748b", width=1, tags="gantry_display")
            self.canvas.create_text(
                gcx + lx_off, gcy + ly_off,
                text=c_lbl,
                fill="#64748b",
                font=("Segoe UI", 9),
                anchor=anc,
                tags="gantry_display"
            )

        # Subtle center isocenter crosshair
        self.canvas.create_line(gcx - 5, gcy, gcx + 5, gcy, fill="#334155", width=1, tags="gantry_display")
        self.canvas.create_line(gcx, gcy - 5, gcx, gcy + 5, fill="#334155", width=1, tags="gantry_display")
        self.canvas.create_oval(gcx - 2, gcy - 2, gcx + 2, gcy + 2, fill="#475569", outline="", tags="gantry_display")

        # Red arrow pointing in from the black circle towards the center in the direction the gantry is at
        rad = math.radians(angle)
        sx = gcx + (R - 2.0) * math.sin(rad)
        sy = gcy - (R - 2.0) * math.cos(rad)

        r_end = 10.0
        ex = gcx + r_end * math.sin(rad)
        ey = gcy - r_end * math.cos(rad)

        # Red arrow line with arrowhead pointing towards center
        self.canvas.create_line(
            sx, sy, ex, ey,
            fill="#ef4444",
            width=3,
            arrow="last",
            arrowshape=(12, 14, 5),
            tags="gantry_display"
        )

        # Radiation source dot at perimeter
        self.canvas.create_oval(
            sx - 4, sy - 4, sx + 4, sy + 4,
            fill="#ef4444",
            outline="#fca5a5",
            width=1,
            tags="gantry_display"
        )

    def _on_mouse_hover(self, event: tk.Event) -> None:
        """Shows leaf details on hover."""
        if not self.analyzer or self.total_frames == 0:
            return

        leaf_size_px = UNITY_LEAF_WIDTH_MM * self.scale
        if leaf_size_px <= 0:
            return

        if self.y2_orientation in ("Right", "Left"):
            top_y_px = self.cy - (UNITY_STACK_LIMIT_MM * self.scale)
            dy = event.y - top_y_px
            leaf_idx = int(dy / leaf_size_px) if 0 <= dy <= (UNITY_LEAF_COUNT * leaf_size_px) else -1
        elif self.y2_orientation == "Top":
            left_x_px = self.cx - (UNITY_STACK_LIMIT_MM * self.scale)
            dx = event.x - left_x_px
            leaf_idx = int(dx / leaf_size_px) if 0 <= dx <= (UNITY_LEAF_COUNT * leaf_size_px) else -1
        else:  # "Bottom"
            right_x_px = self.cx + (UNITY_STACK_LIMIT_MM * self.scale)
            dx = right_x_px - event.x
            leaf_idx = int(dx / leaf_size_px) if 0 <= dx <= (UNITY_LEAF_COUNT * leaf_size_px) else -1

        if 0 <= leaf_idx < UNITY_LEAF_COUNT:
            frame_data = self.analyzer.get_aperture_at_index(self.current_frame)
            y1 = frame_data["y1_pos"][leaf_idx] if leaf_idx < len(frame_data["y1_pos"]) else 0.0
            y2 = frame_data["y2_pos"][leaf_idx] if leaf_idx < len(frame_data["y2_pos"]) else 0.0
            y1_err = frame_data["y1_err"][leaf_idx] if leaf_idx < len(frame_data["y1_err"]) else 0.0
            y2_err = frame_data["y2_err"][leaf_idx] if leaf_idx < len(frame_data["y2_err"]) else 0.0
            gap = max(0.0, y2 - y1)

            self.lbl_hover.config(
                text=f"Leaf {leaf_idx+1:02d} | Y1: {y1:+.1f} mm (Err: {y1_err:+.2f}) | Y2: {y2:+.1f} mm (Err: {y2_err:+.2f}) | Gap: {gap:.1f} mm"
            )
            return

        self.lbl_hover.config(text="")

    def _on_mouse_wheel(self, event: tk.Event) -> None:
        """Mouse wheel scrolls forward/backward in time."""
        if self.total_frames == 0:
            return
        delta = 5 if event.delta > 0 else -5
        self.set_frame(self.current_frame + delta)

    def _on_resize(self, event: tk.Event) -> None:
        """Handles dynamic canvas resizing when window size changes."""
        w = event.width
        h = event.height
        if w < 50 or h < 50:
            return

        if abs(w - self.canvas_width) < 2 and abs(h - self.canvas_height) < 2:
            return

        self.canvas_width = w
        self.canvas_height = h
        self._update_scale()
        self._draw_axes()
        self.render_current_frame()

    # Timeline Controls
    def seek_first(self) -> None:
        self.set_frame(0)

    def seek_last(self) -> None:
        self.set_frame(max(0, self.total_frames - 1))

    def step_prev(self, count: int = 1) -> None:
        self.set_frame(max(0, self.current_frame - count))

    def step_next(self, count: int = 1) -> None:
        self.set_frame(min(self.total_frames - 1, self.current_frame + count))

    def set_frame(self, frame: int) -> None:
        """Sets active frame index."""
        if self.total_frames == 0:
            return
        self.current_frame = max(0, min(self.total_frames - 1, frame))
        self.slider_var.set(self.current_frame)
        self.lbl_step_counter.config(text=f"Step: {self.current_frame + 1} / {self.total_frames}")
        self.render_current_frame()

    def _on_slider_change(self, val_str: str) -> None:
        """Callback when user drags timeline slider."""
        try:
            val = int(float(val_str))
            if val != self.current_frame:
                self.current_frame = val
                self.lbl_step_counter.config(text=f"Step: {self.current_frame + 1} / {self.total_frames}")
                self.render_current_frame()
        except ValueError:
            pass

    def toggle_play(self) -> None:
        """Toggles play/pause delivery animation."""
        if self.is_playing:
            self.pause()
        else:
            self.play()

    def play(self) -> None:
        if self.total_frames == 0:
            return
        self.is_playing = True
        self.btn_play.config(text="⏸ Pause")
        self._animation_loop()

    def pause(self) -> None:
        self.is_playing = False
        self.btn_play.config(text="▶ Play")
        if self._anim_job:
            self.after_cancel(self._anim_job)
            self._anim_job = None

    def _animation_loop(self) -> None:
        if not self.is_playing:
            return

        if self.current_frame >= self.total_frames - 1:
            self.current_frame = 0  # Loop or stop
        else:
            self.current_frame += 1

        self.slider_var.set(self.current_frame)
        self.lbl_step_counter.config(text=f"Step: {self.current_frame + 1} / {self.total_frames}")
        self.render_current_frame()

        # Target 25 fps (~40 ms delay divided by speed)
        delay_ms = max(5, int(40 / self.play_speed))
        self._anim_job = self.after(delay_ms, self._animation_loop)

    def _on_speed_changed(self, event=None) -> None:
        txt = self.speed_combo.get().replace("x", "")
        try:
            self.play_speed = float(txt)
        except ValueError:
            self.play_speed = 1.0

