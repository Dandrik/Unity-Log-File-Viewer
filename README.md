# Elekta Unity MR-Linac Log & TRF File Viewer

A Python desktop GUI application built for the **Elekta Unity MR-Linac system** to load, visualize, and analyze:
1. **TRF (Treatment Record File) Delivery Logs**: Decode high-frequency (25 Hz) binary delivery trajectory logs, visualize **MLC leaf shapes (Beam's Eye View)**, monitor **Gantry angle & error dynamics**, and analyze **positional error heatmaps & RMS profiles**.
2. **Machine Event & Subsystem Text Logs**: Parse, search, filter, and inspect service logs, hardware interlocks, and subsystem diagnostics with multi-line traceback support.

---

## Key Capabilities

### 🎯 Treatment Playback (Beam's Eye View)
* **Elekta Unity Physical Collimator Calibration**:
  * Real-time 2D rendering calibrated to exact **Elekta Unity MR-Linac** physical geometry:
    * **Cross-plane leaf stack**: **57.4 cm (574.0 mm)** spanning $\pm 287.0\text{ mm}$ at isocenter ($SAD = 143.5\text{ cm}$).
    * **Leaf pitch**: **7.175 mm** width per leaf at isocenter ($5.0\text{ mm} \times \frac{1435}{1000}$).
    * **In-plane leaf travel**: **22.0 cm (220.0 mm)** spanning $\pm 110.0\text{ mm}$.
    * **Carriage park boundaries**: $\pm 165.0\text{ mm}$ accommodating retracted/parked leaves.
    * **Diaphragm shielding**: X1 (Red) and X2 (Green) cross-plane diaphragms accurately shielding outer leaves.
  * Fully calibrated Bank Y1 coordinate sign mapping (negative isocenter aperture coordinates).
* **Configurable Bank Y2 Orientation**:
  * Combobox selector to display Bank Y2 at **`Top`** (default), **`Bottom`**, **`Right`**, or **`Left`** with isotropic canvas scaling.
* **Treatment Timestamps & Real-Time Delivery Scrubbing**:
  * Displayed directly on the deep blue canvas background (`#0f172a`) to the right of the MLC display:
    * **Tx Start**: Delivery start date and time (`YYYY-MM-DD HH:MM:SS`) parsed from the TRF header.
    * **Current CP**: Active control point timestamp highlighted in sky blue (`#38bdf8`), advancing in real time during scrub or playback.
    * **Tx End**: Calculated delivery completion date and time.
* **Instantaneous Dose Rate & Vertical Bar Graph**:
  * Real-time numeric readout (`Dose Rate: <val> MU/min`) with beam amber radiation highlighting.
  * Calibrated vertical bar graph from **0 MU/min** at the bottom to **500 MU/min** at the top, featuring scale ticks (0, 100, 200, 300, 400, 500 MU/min), active proportional fill, and indicator needle.
* **Real-Time Gating Indicator Box**:
  * Dedicated interlock indicator box located in the dose rate subwindow to the right of the bar graph.
  * Automatically turns **bright red** (`#dc2626` / `#ef4444`) with bold white text and `ENABLED` badge when motion tracking or beam hold gating is active.
  * Displays dark navy (`#0b1120`) with muted slate text and `DISABLED` badge when gating is inactive.
  * Native detection of TRF gating channels (`Gating`, `beam hold`, and Unity EDLI channel `2546`).
* **Real-Time Gantry Angle & Inward Radiation Beam Indicator**:
  * Positioned directly below the dose rate and gating card on the deep blue canvas background.
  * Live numeric readout (`Gantry Angle: <val>°`) with instantaneous positional error tracking (`±<err>°`).
  * Pure black circle (`#000000`) representing the gantry ring with cardinal ticks and labels (`0°`, `90°`, `180°`, `270°`) following IEC 61217 coordinates (0° overhead, clockwise).
  * Central isocenter crosshairs (`+`) and a prominent red arrow (`#ef4444`) pointing **in** from the black circle perimeter towards the center in the direction the gantry is positioned, clearly depicting the radiation beam entry direction.
* **High-Visibility Scaled Typography**:
  * All canvas readouts, axis labels, and beam metric texts are scaled 1.5x larger for optimal viewing on clinical monitors.
* **Delivered Monitor Unit (MU) Calibration & Real-Time Tracking**:
  * Accurate calibration for Elekta TRF binary header format (stored in tenths of an MU / $0.1\text{ MU}$), displaying true delivered dose (e.g. `761.4 MU`) in the summary KPI card above playback.
  * Monotonic multi-control-point cumulative MU reconstruction dynamically advances the `MU: ...` playback indicator from `0.0 MU` to the full delivered dose during animation and scrubbing.
* **Playback & Inspection Controls**:
  * Interactive timeline scrubber, frame step controls, and variable-speed animation (1x, 2x, 5x, 10x).
  * Color-coded error tagging directly on individual leaves (green: nominal, amber: > 1.0 mm, red: > 2.0 mm).
  * Live hover tooltip displaying exact leaf positions, positional errors, and aperture gap.

### 📈 Gantry Position & Dynamics
* **Dual-Subplot Visualization**: Gantry Angle (Actual vs Planned) and instantaneous Gantry Positional Error.
* **Tolerance Envelopes**: Shaded tolerance bands (nominal $\pm 0.5^\circ$, warning $\pm 1.0^\circ$).
* **Interactive Scrubbing**: Click directly on the trajectory curve to jump to any point in the treatment delivery.

### 🔬 Comprehensive Quality Assurance & Error Metrics
* **2D Leaf Error Heatmap**: Error magnitude (|Error| mm) mapped across all 80 leaves vs delivery time.
* **RMS Error Bar Chart**: Root-Mean-Square error per leaf for Bank Y1 and Bank Y2 with tolerance threshold lines.
* **Worst Performing Leaves Table**: Rank-ordered list identifying leaves with highest peak error or RMS deviation.
* **Export to CSV**: Export leaf error statistics and tolerance summaries for clinical records.
* **Raw Delivery Channels Browser**: Searchable table viewer across all recorded delivery channels at 25 Hz.

### 📋 Machine Event & Text Log Viewer
* **Smart Parsing**: Auto-extracts timestamps, log severity levels (`CRITICAL`, `ERROR`, `WARN`, `INFO`, `DEBUG`), and subsystems/components (`LinacState`, `MRAcquisition`, `MLCService`, `BeamControl`, `SafetyInterlock`, etc.).
* **Multi-line Continuation**: Cleanly bundles stack traces and error details with parent log records.
* **Live Filtering**:
  * Real-time text search with Regex and Case Sensitivity toggles.
  * Severity level multi-select checkboxes.
  * Subsystem dropdown filter.
* **Detail Inspector**: Displays full message text, stack traces, and provides one-click clipboard copying.
* **Export**: Export filtered results to `.txt` or `.csv`.

---

## Installation & Setup

Ensure Python 3.10+ is installed. Install the dependencies using pip:

```bash
pip install -r requirements.txt
```

### Dependencies
* `pandas`: Delivery data manipulation and analysis
* `pymedphys`: Decoding of Elekta Linac binary `.trf` log files
* `matplotlib`: Embedded time-series trajectory and heatmap charts
* `numpy`: Array math, RMS calculations, and fast metric aggregation

---

## Launching the Application

### Standard GUI Launch:
```bash
python main.py
```

### Quick Sample Mode (Pre-loads synthetic Unity VMAT arc & sample log):
```bash
python main.py --sample
```

### Launch with a specific file:
```bash
python main.py --trf "path/to/treatment_delivery.trf"
python main.py --log "path/to/unity_service.log"
```

---

## Running the Automated Test Suite

Run all unit and GUI integration tests:
```bash
python -m unittest discover -s tests
```

---

## Changelog

For a detailed history of all changes, enhancements, and calibrations, see [CHANGELOG.md](CHANGELOG.md).


