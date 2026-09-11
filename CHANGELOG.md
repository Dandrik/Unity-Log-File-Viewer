# Changelog

All notable changes to the **Elekta Unity MR-Linac Log & TRF File Viewer** are documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

---

## [Unreleased] - 2026-09-11

### Added
- **Gating Indicator Box**:
  - Added a dedicated status indicator box labeled **Gating** in the dose rate subwindow directly to the right of the vertical bar graph.
  - Box turns **bright red** (`#dc2626` background, `#ef4444` border) with bold white text and an `ENABLED` badge when motion tracking or beam hold gating is active.
  - Displays dark navy (`#0b1120`, `#334155` border) with muted slate text and `DISABLED` badge when gating is inactive.
  - Automatically detects gating channels from TRF logs (channels containing `Gating`, `gate`, `beam hold`, or Elekta Unity EDLI interlock item `2546`).
- **Dose Rate Display & Vertical Bar Graph**:
  - Added real-time instantaneous dose rate readout (`Dose Rate: <val> MU/min`) positioned directly below the treatment timestamps card on the deep blue canvas background.
  - Added a calibrated vertical bar graph underneath the readout:
    - Bottom of scale: **0 MU/min**
    - Top of scale: **500 MU/min**
    - Major ticks and labels at `0 MU/min` and `500 MU/min`.
    - Intermediate scale ticks at `100`, `200`, `300`, and `400` MU/min with clean left-aligned typography.
    - Proportional amber radiation beam fill (`#f59e0b`), bright cap highlight line (`#fef08a`), and pointer needle indicating instantaneous delivery rate.
- **Treatment Timestamps Card**:
  - Added formatted timestamp card directly on the deep blue canvas background (`#0f172a`) to the right of the MLC display:
    - **Tx Start**: Treatment start date and time (`YYYY-MM-DD HH:MM:SS`) parsed from the TRF header.
    - **Current CP**: Active control point date and time (`YYYY-MM-DD HH:MM:SS`), highlighted in bright cyan (`#38bdf8`) and dynamically advancing as the slider scrubs or playback animates.
    - **Tx End**: Calculated treatment end date and time (`YYYY-MM-DD HH:MM:SS`).
- **Bank Y2 Orientation Selector**:
  - Added a dropdown selector allowing users to position Bank Y2 at `Top` (default), `Bottom`, `Right`, or `Left`.
  - Isotropically updates leaf stack geometry, diaphragm orientations, labels, and hover hit-testing.
- **Automated Test Coverage**:
  - Added `test_unity_field_geometry`: Validates 57.4 cm $\times$ 22.0 cm field bounds, 7.175 mm leaf pitch, 80 leaf pairs, and leaf hover hit-testing.
  - Added `test_y2_orientation_selection`: Tests orientation switching across all 4 modes (`Top`, `Bottom`, `Right`, `Left`).
  - Added `test_treatment_playback_datetime_display`: Validates start, current CP, and end timestamp calculations and slider updates.
  - Added `test_treatment_playback_doserate_display`: Validates dose rate extraction, readout formatting, and 0 vs 500 MU/min bar graph scaling.
  - Added `test_treatment_playback_gating_box`: Tests Gating box rendering, normal state (`#0b1120`, `DISABLED`), and active red alert state (`#dc2626`, `ENABLED`).

### Changed
- **Tab Renaming**:
  - Renamed the primary collimation visualization tab from **MLC Leaf Shape (BEV)** to **🎯 Treatment Playback**.
- **Elekta Unity Collimator Physical Calibration**:
  - Replaced conventional 40 cm $\times$ 40 cm generic linac assumptions with physical **Elekta Unity MR-Linac** specifications:
    - **Source-to-Axis Distance (SAD)**: 143.5 cm (1435 mm).
    - **Cross-Plane Field Dimension**: 57.4 cm (574.0 mm) spanning $\pm 287.0\text{ mm}$ across the 80-leaf stack.
    - **Leaf Pitch**: 7.175 mm per leaf at isocenter ($5.0\text{ mm} \times \frac{1435}{1000}$).
    - **In-Plane Field Dimension**: 22.0 cm (220.0 mm) spanning $\pm 110.0\text{ mm}$ in leaf travel.
    - **Carriage Park Walls**: $\pm 165.0\text{ mm}$ (accommodates leaf retraction/park positions).
    - **Diaphragm System**: Diaphragms X1 (Red) and X2 (Green) move along the cross-plane 57.4 cm axis, accurately shielding outer leaf pairs.
- **Bank Y1 Coordinate Sign Calibration**:
  - Calibrated Bank Y1 leaf position sign: in Unity TRF logs, Y1 actual positions are recorded as positive magnitudes when open; inverted sign to map to negative isocenter coordinates so apertures open conformally between $Y_1$ (negative) and $Y_2$ (positive).
- **Typography & Font Scaling**:
  - Scaled all BEV/Treatment Playback canvas text, readouts, and labels 1.5x larger for high visibility.
- **Header Bar Cleanup**:
  - Streamlined the top readout bar to cleanly present `Time`, `Gantry`, `MU`, `X1`, and `X2`, keeping the viewport uncluttered.

---

## [1.0.0] - 2026-09-08

### Added
- Initial release of the **Elekta Unity MR-Linac Log & TRF File Viewer**:
  - **TRF Delivery Analyzer**:
    - High-frequency (25 Hz) binary TRF decoding via `pymedphys`.
    - Real-time Beam's Eye View (BEV) 2D MLC leaf and diaphragm animation.
    - Gantry angle and error tracking with tolerance envelopes ($\pm 0.5^\circ$, $\pm 1.0^\circ$).
    - 2D Leaf positional error heatmap across all 80 leaf pairs over time.
    - RMS error bar charts and worst-performing leaves rank table.
    - Raw 25 Hz delivery channel table browser.
  - **Machine Event & Text Log Viewer**:
    - Multi-line traceback bundling and regex-enabled smart text log parser.
    - Severity filtering (`CRITICAL`, `ERROR`, `WARN`, `INFO`, `DEBUG`).
    - Subsystem filtering and log detail modal with clipboard copying.
  - **CLI Arguments**:
    - `--sample`: Pre-loads synthetic Unity VMAT arc and sample service logs.
    - `--trf <path>`: Directly opens a specified TRF file.
    - `--log <path>`: Directly opens a specified machine text log.

