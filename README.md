# Elekta Unity MR-Linac Log & TRF File Viewer

A Python desktop GUI application built for the **Elekta Unity MR-Linac system** to load, visualize, and analyze:
1. **TRF (Treatment Record File) Delivery Logs**: Decode high-frequency (25 Hz) binary delivery trajectory logs, visualize **MLC leaf shapes (Beam's Eye View)**, monitor **Gantry angle & error dynamics**, and analyze **positional error heatmaps & RMS profiles**.
2. **Machine Event & Subsystem Text Logs**: Parse, search, filter, and inspect service logs, hardware interlocks, and subsystem diagnostics with multi-line traceback support.

---

## Key Capabilities

### 🎯 TRF Delivery & MLC Leaf Shape Analyzer
* **Beam's Eye View (BEV) Visualizer**:
  * Real-time 2D rendering of all **80 Agility MLC leaf pairs** (Bank Y1 & Bank Y2).
  * Clear aperture boundary and X1/X2 Diaphragm/Jaw position overlays.
  * Interactive timeline scrubber, step-by-step frame controls, and animation playback (1x, 2x, 5x, 10x speeds).
  * Color-coded error tagging directly on individual leaves (green: nominal, amber: > 1.0 mm, red: > 2.0 mm).
  * Live hover tooltip displaying exact leaf positions, positional errors, and aperture gap.
* **Gantry Position & Dynamics**:
  * Dual-subplot visualization: Gantry Angle (Actual vs Planned) and instantaneous Gantry Positional Error.
  * Shaded tolerance bands (nominal $\pm 0.5^\circ$, warning $\pm 1.0^\circ$).
  * Interactive click-to-scrub on the trajectory curve to jump to any point in the treatment delivery.
* **Comprehensive Quality Assurance & Error Metrics**:
  * **2D Leaf Error Heatmap**: Error magnitude (|Error| mm) mapped across all 80 leaves vs delivery time.
  * **RMS Error Bar Chart**: Root-Mean-Square error per leaf for Bank Y1 and Bank Y2 with tolerance threshold lines.
  * **Worst Performing Leaves Table**: Rank-ordered list identifying leaves with highest peak error or RMS deviation.
  * **Export to CSV**: Export leaf error statistics and tolerance summaries for clinical records.
* **Raw Delivery Channels Browser**:
  * Searchable table viewer across all recorded delivery channels at 25 Hz.

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

