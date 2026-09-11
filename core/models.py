"""Data models for Elekta Unity Log and TRF File Viewer."""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional
import pandas as pd


@dataclass
class LogEntry:
    """Represents a single parsed text log record."""
    line_number: int
    raw_text: str
    timestamp: Optional[str] = None
    level: str = "INFO"
    component: str = "System"
    message: str = ""
    details: str = ""


@dataclass
class TRFHeader:
    """Metadata parsed from Elekta TRF header."""
    machine: str = ""
    date: str = ""
    timezone: str = ""
    field_label: str = ""
    field_name: str = ""
    mu: float = 0.0
    version: int = 0


@dataclass
class LeafErrorStats:
    """Statistical summary of positional errors for a specific leaf."""
    leaf_number: int
    bank: str  # 'Y1' or 'Y2'
    max_error_mm: float = 0.0
    mean_error_mm: float = 0.0
    rms_error_mm: float = 0.0
    pct_within_1mm: float = 100.0
    pct_within_2mm: float = 100.0


@dataclass
class DeliveryQAStats:
    """Delivery Quality Assurance summary for a TRF recording."""
    total_samples: int = 0
    duration_seconds: float = 0.0
    total_mu: float = 0.0

    # Gantry metrics
    gantry_start_deg: float = 0.0
    gantry_end_deg: float = 0.0
    gantry_max_error_deg: float = 0.0
    gantry_mean_error_deg: float = 0.0
    gantry_rms_error_deg: float = 0.0

    # MLC Y1 metrics (80 leaves)
    y1_max_error_mm: float = 0.0
    y1_rms_error_mm: float = 0.0
    y1_worst_leaf: int = 0

    # MLC Y2 metrics (80 leaves)
    y2_max_error_mm: float = 0.0
    y2_rms_error_mm: float = 0.0
    y2_worst_leaf: int = 0

    # Combined MLC metrics
    overall_max_leaf_error_mm: float = 0.0
    overall_rms_leaf_error_mm: float = 0.0
    worst_leaf_name: str = ""
    pct_samples_within_1mm: float = 100.0
    pct_samples_within_2mm: float = 100.0

    # Diaphragms / Jaws
    x1_max_error_mm: float = 0.0
    x2_max_error_mm: float = 0.0


@dataclass
class TRFDataset:
    """Contains all decoded data, mappings, and computed metrics for a TRF file."""
    header: TRFHeader
    dataframe: pd.DataFrame
    y1_actual_cols: List[str] = field(default_factory=list)
    y2_actual_cols: List[str] = field(default_factory=list)
    y1_error_cols: List[str] = field(default_factory=list)
    y2_error_cols: List[str] = field(default_factory=list)
    gantry_actual_col: Optional[str] = None
    gantry_error_col: Optional[str] = None
    collimator_col: Optional[str] = None
    jaw_x1_col: Optional[str] = None
    jaw_x2_col: Optional[str] = None
    jaw_x1_err_col: Optional[str] = None
    jaw_x2_err_col: Optional[str] = None
    dose_mu_col: Optional[str] = None
    dose_rate_col: Optional[str] = None
    gating_col: Optional[str] = None
    qa_stats: Optional[DeliveryQAStats] = None
    leaf_stats: List[LeafErrorStats] = field(default_factory=list)

