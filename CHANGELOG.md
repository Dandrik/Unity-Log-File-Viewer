# Changelog

All notable changes to the **Elekta Unity MR-Linac Log & TRF File Viewer** are documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

---

## [Unreleased] - 2026-09-11

- **Elekta Unity SDD (Service Diagnostic Data) Package Support**:
  - Added native support for opening complete Elekta Unity SDD `.zip` packages (e.g. `SDD+TRCC-NRT-600064+...zip`) and extracted directories without requiring manual decompression.
  - Implemented `core/sdd_package.py` providing zero-extraction streaming indexing: reads the first 16 KB of each `.trf` in the zip archive to index timestamps, field names, and delivered MUs in under 100 ms for 50+ deliveries.
  - Added delivery category classification based on field naming heuristics (`Warmup`, `Daily QA`, `Shape / Test`, `Clinical Treatment`).
  - Added in-memory binary decoding via `TRFReader.read_bytes(trf_contents, source_name)` to eliminate intermediate disk writes.
  - Added log string ingestion via `TextLogView.load_raw_text(text, source_name)` with automatic UTF-8 / UTF-16 decoding and .NET serialized logger unmasking.
  - Built interactive `SDDNavigatorDialog` (`gui/components/sdd_navigator.py`) with:
    - **Header bar**: Linac ID badge (`TRCC-NRT-600064`), export timestamp, package filename, delivery count, and log file count badges.
    - **Treatment Deliveries tab**: Search filter, category dropdown, sortable Treeview table (Date/Time, Plan/Field, Category, Delivered MU, Size, Filename), and one-click "Load into Viewer" button. Calibrated category row typography (`clinical`: dark slate `#0f172a`, `Daily QA`: deep sky blue `#0369a1`, `Warmup`: rich amber `#b45309`, `Shape / Test`: deep purple `#6d28d9`) for crisp, high-contrast legibility against the white table background.
    - **Subsystem Logs tab**: Searchable treeview of `LOGFILE00000xxxx` event logs and diagnostics with one-click "Load into Text Log Viewer" button.
    - **Machine Info & Manifest tab**: Formatted machine specifications (Machine ID, Windows OS, IPs) and full searchable RTD Manifest.
  - Added quick launch button `📦 Open SDD Package (.zip)` in the top application header and File menu items (`Ctrl+Shift+O` and `Ctrl+B`).
  - Added automated unit and GUI integration tests in `tests/test_sdd.py`.
- **Linac State & MLC State Machine Status Card**:
  - Added real-time **Linac State** and **MLC State** telemetry card positioned directly below the Total Dose graph on the deep blue canvas background.
  - Added parenthesized integer code display to both **Linac State** and **MLC State** readouts (e.g. `Radiation On (42)`, `Move Only (39)`, `MLC OK (1)`, `Leaves not Ready Y2 (7300)`, `Incorrect Sequence ID (7015)`).
  - Line 1 displays **Linac State** (`Linac State: <state> (<code_id>)`) with an active status dot:
    - `Radiation On (42)`: amber indicator dot and text during beam-on delivery.
    - `Move Only (39)`: sky blue indicator dot during gantry and MLC repositioning.
    - `Intersegment (41)`: soft blue indicator dot between segments.
    - `Terminated Ok (46)`: emerald green indicator dot upon successful treatment finish.
    - `Terminated Fault (47)`: bright red indicator dot upon fault termination.
  - Line 2 displays **MLC State** (`MLC State: <state> (<code_id>)`) with active status dot, full Elekta MLC Controller codes decoding, and leaf tolerance logic:
    - Added dedicated module `core/mlc_codes.py` defining over 400 official Elekta hardware status, interlock, positioning, and fault codes (7000–8238), `ELEKTA_LINAC_CODES` (0–47), bidirectional lookups, and helper functions `format_linac_state` and `format_mlc_state`.
    - Integrated with TRF channel `Mlc Status/Actual Value (None)` to dynamically decode hardware states including `MLC OK (1)`, `Leaves not Ready Y2 (7300)`, `Leaves not Ready Y1 (7310)`, `Incorrect Sequence ID (7015)`, `Diaphragm Position X2 (7460)`, `All Voltage Rails (7615)`, `Prescription Not OK (7000/8050)`, `Out of tolerance` (8040/8041), and leaf loss/pot/sensor faults (8101–8238).
    - Added physical leaf bank readiness tolerance fallback ($\le 1.0\text{ mm}$ tolerance threshold) returning `MLC OK (1)`, `Leaves not Ready Y2 (7300)`, `Leaves not Ready Y1 (7310)`, and `Leaves not Ready Y1 & Y2 (7300 & 7310)`.
    - Enhanced color-coded status styling: emerald green for OK/Ready, amber for movement/not ready, bright red for faults/interlocks/errors/timeouts, and sky blue for positions and hardware rails.
    - Calibrated status dot alignment (`box_x1 + 110px`) and state text offset (`box_x1 + 124px`) to provide ample breathing room and eliminate any visual overlap with the `"State:"` text labels.
    - Added dynamic typography scaling (size 7 for > 30 characters, size 8 for > 22 characters, size 9 for > 16 characters) to guarantee clean fit without clipping.
    - Updated unit test `test_treatment_playback_linac_and_mlc_state_card` in `tests/test_gui.py` asserting code lookups, frame transitions, and real clinical binary TRF file decoding with parenthesized codes.
- **Bug Fix - Consecutive TRF File Loading**:
  - Resolved `'NoneType' object has no attribute 'set_subplotspec'` error occurring when opening or loading a different `.trf` file while a dataset was already loaded.
  - Root Cause: In `gui/components/error_view.py`, `self._cb_heatmap.remove()` attempted to restore subplotspec attributes on an axes cleared by `self.ax_heatmap.clear()`, causing Matplotlib's internal colorbar deallocation to fail.
  - Fix: Updated `ErrorView._plot_heatmap` to cleanly reset the figure via `self.fig_heatmap.clear()`, restore background theme facecolor, and cleanly recreate the main subplot axes before attaching the colorbar.
  - Added automated test `test_consecutive_trf_dataset_loads` validating consecutive dataset reloads (both synthetic and real clinical binaries) and bank toggles.
- **Control Point Delivered Dose & Progress Bar**:
  - Added real-time control point delivered dose readout (`CP Dose: <delivered> / <target> MU`) with percentage badge positioned directly below the control point card.
  - Added horizontal bar graph illustrating current control point dose progress with amber radiation fill (`#d97706`), bright gold cap line (`#fbbf24`), dark trough (`#0b1120`), and sub-labels (`0.0 MU` and target step MU).
- **Treatment Total Delivered Dose & Progress Bar**:
  - Added real-time total treatment delivered dose readout (`Total Dose: <cumulative> / <total> MU`) with overall completion percentage badge positioned directly below the control point dose card.
  - Added horizontal bar graph illustrating overall treatment dose delivery with emerald green fill (`#059669`), bright mint cap line (`#34d399`), dark trough (`#0b1120`), and sub-labels (`0.0 MU` and total planned MU).
- **Control Point Readout & Horizontal Progress Bar**:
  - Added real-time control point readout (`Control Point: <current>/<total>`) along with completion percentage badge (e.g. `Control Point: 1/50` | `10%`) positioned directly below the gantry display card.
  - Added a calibrated horizontal progress bar showing fractional delivery progress ($CP / CP_{total}$) with dark recessed trough (`#0b1120`), vibrant cyan progress fill (`#0284c7`), and bright leading-edge cap line (`#38bdf8`).
  - Added sub-labels indicating the starting control point (`CP 1`) and final control point (`CP <total>`) underneath the bar.
  - Added automatic detection of TRF control point channels (e.g. `Control point/Actual Value (None)`) in `TRFReader` and passed per-frame values in `TRFAnalyzer.get_aperture_at_index`.
- **Gantry Angle & Radiation Beam Direction Circle**:
  - Added real-time numeric Gantry Angle readout (`Gantry Angle: <val>°` with error tracking `(±<err>°)`) positioned directly below the dose rate and gating card.
  - Added pure black circular gantry indicator (`fill="#000000"`) below the readout with IEC 61217 cardinal markings (`0°` top, `90°` right, `180°` bottom, `270°` left) and central isocenter crosshairs (`+`).
  - Added dynamic red arrow (`#ef4444`, `arrow="last"`) pointing inward from the perimeter of the circle towards the isocenter in the direction the gantry is positioned, accompanied by a radiation source origin dot on the perimeter.
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
  - Added `test_treatment_playback_gantry_circle`: Verifies gantry angle label formatting, `gantry_display` canvas items, pure black circle (`#000000`), inward red arrow (`#ef4444`), and custom angle redraw.
  - Added `test_treatment_playback_control_point_display`: Verifies control point text formatting (`Control Point 1/50`), progress bar fill, and custom CP redraw.
  - Added `test_treatment_playback_cp_and_total_dose_cards`: Verifies Control Point delivered dose and treatment total delivered dose card rendering, labels, and horizontal bar fill.
  - Added `test_trf_header_mu_scaling`: Verifies that raw binary header MU (in 0.1 MU / dMU units) is divided by 10.0 to convert to true Monitor Units.
  - Added `test_cumulative_mu_and_total_mu`: Verifies total MU in summary stats and monotonic cumulative MU progression during scrubbing.
  - Added `test_delivered_mu_card_display`: Verifies that the Delivered MU KPI card above Treatment Playback correctly displays formatted MU.

### Fixed
- **Delivered MU Header Scale Factor (10x Calibration)**:
  - Fixed a $10\times$ factor discrepancy in the **Delivered MU** KPI stat card above the Treatment Playback window (e.g. displaying `7614.0 MU` instead of `761.4 MU`).
  - Elekta Unity TRF binary headers record Monitor Units in tenths of an MU ($0.1\text{ MU}$ / dMU); calibrated `TRFReader._build_header` to divide raw header MU by $10.0$.
  - Implemented multi-control-point cumulative MU precomputation in `TRFAnalyzer._precompute_cumulative_mu` so that the `MU: ...` playback indicator and delivery statistics accurately track cumulative dose from 0.0 MU up to the true total delivered MU across the entire field.

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

