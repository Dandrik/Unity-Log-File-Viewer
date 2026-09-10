"""Interactive 2D Beam's Eye View (BEV) MLC Leaf Shape visualizer."""

import tkinter as tk
from tkinter import ttk
from typing import Callable, Dict, List, Optional
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

        # Display parameters (mm to pixels)
        self.canvas_width = 540
        self.canvas_height = 540
        self.scale = 1.0
        self.cx = self.canvas_width / 2.0
        self.cy = self.canvas_height / 2.0
        self.y2_orientation = "Right"  # "Right", "Left", "Top", or "Bottom"
        self._update_scale()

        self._build_ui()

    def _update_scale(self) -> None:
        """Calculates isotropic scaling factor to fit 57.4 cm x 22.0 cm field (plus leaf park margins)."""
        w = max(50, self.canvas_width)
        h = max(50, self.canvas_height)
        self.cx = w / 2.0
        self.cy = h / 2.0

        if self.y2_orientation in ("Right", "Left"):
            # Leaf travel is horizontal (~360 mm span), leaf stack is vertical (~614 mm span)
            span_x = (UNITY_PARK_WALL_MM * 2.0) + 30.0
            span_y = UNITY_FIELD_STACK_MM + 40.0
        else:
            # Leaf stack is horizontal (~614 mm span), leaf travel is vertical (~360 mm span)
            span_x = UNITY_FIELD_STACK_MM + 40.0
            span_y = (UNITY_PARK_WALL_MM * 2.0) + 30.0

        scale_x = max(10.0, w - 30.0) / span_x
        scale_y = max(10.0, h - 30.0) / span_y
        self.scale = max(0.1, min(scale_x, scale_y))

    def _build_ui(self) -> None:
        """Constructs canvas and animation controls."""
        # Top info header
        self.info_frame = ttk.Frame(self)
        self.info_frame.pack(fill="x", padx=4, pady=(0, 4))

        self.lbl_time = ttk.Label(self.info_frame, text="Time: 0.00 s", font=AppTheme.FONT_BODY_BOLD)
        self.lbl_time.pack(side="left", padx=6)

        self.lbl_gantry = ttk.Label(self.info_frame, text="Gantry: --°", font=AppTheme.FONT_BODY_BOLD)
        self.lbl_gantry.pack(side="left", padx=12)

        self.lbl_mu = ttk.Label(self.info_frame, text="MU: 0.0", font=AppTheme.FONT_BODY)
        self.lbl_mu.pack(side="left", padx=6)

        self.lbl_x1 = ttk.Label(self.info_frame, text="X1: -- mm", font=AppTheme.FONT_BODY_BOLD, foreground="#ef4444")
        self.lbl_x1.pack(side="left", padx=8)

        self.lbl_x2 = ttk.Label(self.info_frame, text="X2: -- mm", font=AppTheme.FONT_BODY_BOLD, foreground="#22c55e")
        self.lbl_x2.pack(side="left", padx=8)

        self.lbl_hover = ttk.Label(self.info_frame, text="", font=AppTheme.FONT_MONO, foreground=AppTheme.TEXT_SECONDARY)
        self.lbl_hover.pack(side="right", padx=6)

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
        self.lbl_step_counter = ttk.Label(self.ctrl_frame, text="Step: 0 / 0", font=AppTheme.FONT_MONO, width=18)
        self.lbl_step_counter.pack(side="left", padx=4)

        # Speed Dropdown
        ttk.Label(self.ctrl_frame, text="Speed:", font=AppTheme.FONT_SMALL).pack(side="left", padx=(6, 2))
        self.speed_combo = ttk.Combobox(self.ctrl_frame, values=["1x", "2x", "5x", "10x"], width=5, state="readonly")
        self.speed_combo.set("1x")
        self.speed_combo.bind("<<ComboboxSelected>>", self._on_speed_changed)
        self.speed_combo.pack(side="left", padx=2)

        # Y2 Bank Position Dropdown
        ttk.Label(self.ctrl_frame, text="Y2 Bank:", font=AppTheme.FONT_SMALL).pack(side="left", padx=(8, 2))
        self.y2_combo = ttk.Combobox(self.ctrl_frame, values=["Right", "Left", "Top", "Bottom"], width=7, state="readonly")
        self.y2_combo.set("Right")
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

    def set_analyzer(self, analyzer: TRFAnalyzer) -> None:
        """Loads dataset and initializes timeline."""
        self.analyzer = analyzer
        self.total_frames = len(analyzer.df)
        self.current_frame = 0
        self.slider.config(to=max(0, self.total_frames - 1))
        self.slider_var.set(0)
        self.lbl_step_counter.config(text=f"Step: 1 / {self.total_frames}")
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
            self.canvas.create_text(self.cx, fy1 - 10, text="Max Field: 22.0 × 57.4 cm (Elekta Unity)", fill="#64748b", font=("Segoe UI", 8), anchor="s", tags="grid")
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
            self.canvas.create_text(self.cx, fy1 - 10, text="Max Field: 57.4 × 22.0 cm (Elekta Unity)", fill="#64748b", font=("Segoe UI", 8), anchor="s", tags="grid")

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

            x1_label_y = y1_px - 8 if (y1_px - 8) > (top_limit_px + 6) else y1_px + 12
            self.canvas.create_text(self.cx, x1_label_y, text=f"▲ X1 Diaphragm ({raw_x1:.1f} mm)", fill="#f87171", font=("Segoe UI", 9, "bold"), anchor="center", tags="jaw")
            x2_label_y = y2_px + 8 if (y2_px + 8) < (bot_limit_px - 6) else y2_px - 12
            self.canvas.create_text(self.cx, x2_label_y, text=f"▼ X2 Diaphragm ({raw_x2:.1f} mm)", fill="#4ade80", font=("Segoe UI", 9, "bold"), anchor="center", tags="jaw")

            if ori == "Right":
                self.canvas.create_text(left_wall_px + 35, top_limit_px - 8, text="◀ Bank Y1", fill="#60a5fa", font=("Segoe UI", 9, "bold"), anchor="s", tags="jaw")
                self.canvas.create_text(right_wall_px - 35, top_limit_px - 8, text="Bank Y2 ▶", fill="#22d3ee", font=("Segoe UI", 9, "bold"), anchor="s", tags="jaw")
            else:
                self.canvas.create_text(left_wall_px + 35, top_limit_px - 8, text="◀ Bank Y2", fill="#22d3ee", font=("Segoe UI", 9, "bold"), anchor="s", tags="jaw")
                self.canvas.create_text(right_wall_px - 35, top_limit_px - 8, text="Bank Y1 ▶", fill="#60a5fa", font=("Segoe UI", 9, "bold"), anchor="s", tags="jaw")

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

                self.canvas.create_text(x1_px, top_wall_px - 8, text=f"◀ X1 ({raw_x1:.1f} mm)", fill="#f87171", font=("Segoe UI", 8, "bold"), anchor="s", tags="jaw")
                self.canvas.create_text(x2_px, top_wall_px - 8, text=f"X2 ({raw_x2:.1f} mm) ▶", fill="#4ade80", font=("Segoe UI", 8, "bold"), anchor="s", tags="jaw")

                self.canvas.create_text(self.cx, top_wall_px + 14, text="▲ Bank Y2", fill="#22d3ee", font=("Segoe UI", 9, "bold"), anchor="center", tags="jaw")
                self.canvas.create_text(self.cx, bot_wall_px - 14, text="Bank Y1 ▼", fill="#60a5fa", font=("Segoe UI", 9, "bold"), anchor="center", tags="jaw")
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

                self.canvas.create_text(x2_px, top_wall_px - 8, text=f"◀ X2 ({raw_x2:.1f} mm)", fill="#4ade80", font=("Segoe UI", 8, "bold"), anchor="s", tags="jaw")
                self.canvas.create_text(x1_px, top_wall_px - 8, text=f"X1 ({raw_x1:.1f} mm) ▶", fill="#f87171", font=("Segoe UI", 8, "bold"), anchor="s", tags="jaw")

                self.canvas.create_text(self.cx, top_wall_px + 14, text="▲ Bank Y1", fill="#60a5fa", font=("Segoe UI", 9, "bold"), anchor="center", tags="jaw")
                self.canvas.create_text(self.cx, bot_wall_px - 14, text="Bank Y2 ▼", fill="#22d3ee", font=("Segoe UI", 9, "bold"), anchor="center", tags="jaw")

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

