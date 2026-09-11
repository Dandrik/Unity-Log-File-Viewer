"""TRF file reader and dataset constructor for Elekta Unity Linac logs."""

import os
from typing import Dict, List, Optional, Tuple
import numpy as np
import pandas as pd

from core.models import TRFDataset, TRFHeader


class TRFReader:
    """Reads and parses Elekta Linac TRF binary files."""

    @staticmethod
    def read_file(filepath: str) -> TRFDataset:
        """Reads a .trf file, seamlessly supporting Elekta Unity MR-Linac extensions."""
        from pymedphys._trf.decode.constants import CONFIG
        from pymedphys._trf.decode.partition import split_into_header_table
        from pymedphys._trf.decode.header import decode_header
        from pymedphys._trf.decode.table import decode_trf_table

        with open(filepath, "rb") as f:
            trf_contents = f.read()

        trf_header_bytes, trf_table_bytes = split_into_header_table(trf_contents)
        raw_header = decode_header(trf_header_bytes)
        header_df = pd.DataFrame([raw_header])

        # Register any Elekta Unity specific channels dynamically to prevent KeyError
        parts = raw_header.item_parts
        keys = [
            f"{parts[i]}_{parts[i+1]}"
            for i in range(0, raw_header.item_parts_length, 2)
        ]
        for k in keys:
            if k not in CONFIG["item_part_names"]:
                CONFIG["item_part_names"][k] = f"Unity/{k}"

        table_df = decode_trf_table(trf_table_bytes, header_df)

        # Parse Header
        header = TRFHeader(
            machine=str(raw_header.machine or ""),
            date=str(raw_header.date or ""),
            timezone=str(raw_header.timezone or ""),
            field_label=str(raw_header.field_label or ""),
            field_name=str(raw_header.field_name or ""),
            mu=float(raw_header.mu) if raw_header.mu else 0.0,
            version=int(raw_header.version) if raw_header.version else 0,
        )

        # Construct Dataset
        return TRFReader._build_dataset(header, table_df)

    @staticmethod
    def _build_dataset(header: TRFHeader, df: pd.DataFrame) -> TRFDataset:
        """Maps columns to standard MLC, Gantry, Jaw, and Dose channels."""
        columns = list(df.columns)

        # MLC Y1 Leaf Actuals (1..80) and Errors
        y1_actuals = []
        y1_errors = []
        for i in range(1, 81):
            act = f"Y1 Leaf {i}/Scaled Actual (mm)"
            err = f"Y1 Leaf {i}/Positional Error (mm)"
            if act in columns:
                y1_actuals.append(act)
            if err in columns:
                y1_errors.append(err)

        # MLC Y2 Leaf Actuals (1..80) and Errors
        y2_actuals = []
        y2_errors = []
        for i in range(1, 81):
            act = f"Y2 Leaf {i}/Scaled Actual (mm)"
            err = f"Y2 Leaf {i}/Positional Error (mm)"
            if act in columns:
                y2_actuals.append(act)
            if err in columns:
                y2_errors.append(err)

        # Gantry
        gantry_act = next((c for c in columns if "Gantry" in c and "Actual" in c), None)
        gantry_err = next((c for c in columns if "Gantry" in c and "Error" in c), None)

        # Collimator
        collimator_act = next((c for c in columns if "Collimator" in c and "Actual" in c), None)

        # Diaphragms / Jaws
        jaw_x1 = next((c for c in columns if "X1 Diaphragm" in c and "Actual" in c), None)
        jaw_x2 = next((c for c in columns if "X2 Diaphragm" in c and "Actual" in c), None)
        jaw_x1_err = next((c for c in columns if "X1 Diaphragm" in c and "Error" in c), None)
        jaw_x2_err = next((c for c in columns if "X2 Diaphragm" in c and "Error" in c), None)

        # Dose
        dose_mu = next((c for c in columns if "Step Dose" in c and "Actual" in c), None)
        dose_rate = next((c for c in columns if "Dose Rate" in c and "Actual" in c), None)
        gating = next((c for c in columns if any(k in c.lower() for k in ["gating", "gate", "beam hold", "beam_hold", "2546"])), None)

        return TRFDataset(
            header=header,
            dataframe=df,
            y1_actual_cols=y1_actuals,
            y2_actual_cols=y2_actuals,
            y1_error_cols=y1_errors,
            y2_error_cols=y2_errors,
            gantry_actual_col=gantry_act,
            gantry_error_col=gantry_err,
            collimator_col=collimator_act,
            jaw_x1_col=jaw_x1,
            jaw_x2_col=jaw_x2,
            jaw_x1_err_col=jaw_x1_err,
            jaw_x2_err_col=jaw_x2_err,
            dose_mu_col=dose_mu,
            dose_rate_col=dose_rate,
            gating_col=gating,
        )

    @staticmethod
    def create_synthetic_dataset(num_points: int = 500, time_step: float = 0.04) -> TRFDataset:
        """Generates realistic synthetic Elekta Unity TRF data for demonstration and testing."""
        np.random.seed(42)
        times = np.round(np.arange(num_points) * time_step, 2)

        data = {}

        # Gantry: rotating arc from 180 deg to 360/0 to 179 deg
        gantry_ideal = 180.0 + (180.0 * (times / times[-1]))
        gantry_noise = np.random.normal(0, 0.08, size=num_points)
        # Add intermittent small lag
        gantry_err = gantry_noise + 0.15 * np.sin(times / 2.0)
        data["Step Gantry/Scaled Actual (deg)"] = gantry_ideal + gantry_err
        data["Step Gantry/Positional Error (deg)"] = gantry_err

        # Collimator: fixed at 0 with small jitter
        data["Step Collimator/Scaled Actual (deg)"] = np.random.normal(0, 0.02, size=num_points)
        data["Step Collimator/Positional Error (deg)"] = np.random.normal(0, 0.01, size=num_points)

        # Diaphragms / Jaws: X1 at +80 mm (Top), X2 at +80 mm (Bottom) with slight movement
        x1_base = 75.0 + 5.0 * np.sin(times / 5.0)
        x2_base = 75.0 - 5.0 * np.sin(times / 5.0)
        data["X1 Diaphragm/Scaled Actual (mm)"] = x1_base + np.random.normal(0, 0.1, num_points)
        data["X2 Diaphragm/Scaled Actual (mm)"] = x2_base + np.random.normal(0, 0.1, num_points)
        data["X1 Diaphragm/Positional Error (mm)"] = np.random.normal(0, 0.1, num_points)
        data["X2 Diaphragm/Positional Error (mm)"] = np.random.normal(0, 0.1, num_points)

        # Dose: linearly increasing MU
        total_mu = 250.0
        data["Step Dose/Actual Value (Mu)"] = np.linspace(0, total_mu, num_points)
        dose_rates = np.full(num_points, 450.0) + np.random.normal(0, 5.0, num_points)

        # Gating (motion tracking beam hold): active during samples 180-220 and 340-370
        gating_arr = np.zeros(num_points, dtype=int)
        gating_arr[180:220] = 1
        gating_arr[340:370] = 1
        dose_rates[180:220] = 0.0
        dose_rates[340:370] = 0.0
        data["Actual Dose Rate/Actual Value (Mu/min)"] = dose_rates
        data["Gating/Actual Value (None)"] = gating_arr

        # 80 Leaf Pairs (Agility MLC)
        # Generate an aperture (e.g. shaped like a target tumor volume that shifts)
        leaf_indices = np.arange(1, 81)
        # Central leaves open, outer leaves closed
        center = 40.5
        opening_profile = np.maximum(0.0, 60.0 - 2.5 * np.abs(leaf_indices - center))

        for idx, leaf_num in enumerate(leaf_indices):
            # In Elekta Unity TRF files, both Bank Y1 and Bank Y2 positions are recorded as positive magnitudes when open
            aperture_half = opening_profile[idx] / 2.0
            y1_nominal = aperture_half + 10.0 * np.sin(times / 3.0 + idx * 0.1)
            y2_nominal = aperture_half + 10.0 * np.sin(times / 3.0 + idx * 0.1)

            # In Elekta Agility coordinate convention:
            # Y1 leaves are negative when open, Y2 leaves are positive when open
            # (or Y2 Scaled Actual is inverted in pymedphys)
            # Standard error model: mostly Gaussian < 0.3mm, with Leaf 24 and 58 having slightly higher lag
            err_scale = 0.4 if leaf_num in (24, 58) else 0.12
            y1_err = np.random.normal(0, err_scale, num_points)
            y2_err = np.random.normal(0, err_scale, num_points)

            # Introduce an occasional spike on leaf 24 (e.g. motor resistance)
            if leaf_num == 24:
                y1_err[150:180] += 1.25

            data[f"Y1 Leaf {leaf_num}/Scaled Actual (mm)"] = y1_nominal + y1_err
            data[f"Y1 Leaf {leaf_num}/Positional Error (mm)"] = y1_err

            data[f"Y2 Leaf {leaf_num}/Scaled Actual (mm)"] = y2_nominal + y2_err
            data[f"Y2 Leaf {leaf_num}/Positional Error (mm)"] = y2_err

        df = pd.DataFrame(data, index=times)

        header = TRFHeader(
            machine="Unity-001 (7T/Linac)",
            date="2026-09-10 10:15:32 Z",
            timezone="+00:00",
            field_label="Field 1",
            field_name="VMAT Prostate Arc",
            mu=total_mu,
            version=4
        )

        return TRFReader._build_dataset(header, df)

