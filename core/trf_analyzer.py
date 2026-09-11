"""Analysis engine for Elekta Linac TRF datasets."""

from typing import Any, Dict, List, Optional, Tuple
import numpy as np
import pandas as pd

from core.models import DeliveryQAStats, LeafErrorStats, TRFDataset


class TRFAnalyzer:
    """Analyzes trajectory delivery data to evaluate MLC, Gantry, and Jaw accuracy."""

    def __init__(self, dataset: TRFDataset, beam_only: bool = False):
        self.dataset = dataset
        self.df = dataset.dataframe
        self.beam_only = beam_only
        self.active_df = self._get_active_df()
        self.stats: Optional[DeliveryQAStats] = None
        self.leaf_stats: List[LeafErrorStats] = []
        self._analyze()

    def set_beam_only(self, beam_only: bool) -> None:
        """Toggles between beam-on delivery only and full recording."""
        self.beam_only = beam_only
        self.active_df = self._get_active_df()
        self._analyze()

    def _get_active_df(self) -> pd.DataFrame:
        """Extracts beam-on segment if beam_only is True, else full dataframe."""
        if self.beam_only and self.dataset.dose_mu_col and self.dataset.dose_mu_col in self.df:
            dose = self.df[self.dataset.dose_mu_col]
            mask = dose > 0
            if mask.any():
                return self.df[mask]
        return self.df

    def _analyze(self) -> None:
        """Computes comprehensive delivery and error metrics."""
        df = self.active_df
        total_samples = len(df)
        if total_samples == 0:
            return

        duration = float(df.index[-1] - df.index[0]) if len(df.index) > 1 else 0.0

        # Gantry metrics
        g_start, g_end, g_max_err, g_mean_err, g_rms_err = 0.0, 0.0, 0.0, 0.0, 0.0
        if self.dataset.gantry_actual_col and self.dataset.gantry_actual_col in df:
            g_series = df[self.dataset.gantry_actual_col].dropna()
            if not g_series.empty:
                g_start = float(g_series.iloc[0])
                g_end = float(g_series.iloc[-1])

        if self.dataset.gantry_error_col and self.dataset.gantry_error_col in df:
            g_err_series = df[self.dataset.gantry_error_col].dropna().abs()
            if not g_err_series.empty:
                g_max_err = float(g_err_series.max())
                g_mean_err = float(g_err_series.mean())
                g_rms_err = float(np.sqrt(np.mean(df[self.dataset.gantry_error_col] ** 2)))

        # Diaphragm / Jaw errors
        x1_max_err = 0.0
        x2_max_err = 0.0
        if self.dataset.jaw_x1_err_col and self.dataset.jaw_x1_err_col in df:
            x1_max_err = float(df[self.dataset.jaw_x1_err_col].abs().max())
        if self.dataset.jaw_x2_err_col and self.dataset.jaw_x2_err_col in df:
            x2_max_err = float(df[self.dataset.jaw_x2_err_col].abs().max())

        # MLC Leaf statistics for Y1 (1..80) and Y2 (1..80)
        self.leaf_stats = []
        all_errors = []

        # Analyze Bank Y1
        y1_max_err, y1_worst = 0.0, 1
        y1_rms_list = []
        for i, col in enumerate(self.dataset.y1_error_cols, start=1):
            if col in df:
                series = df[col].dropna()
                abs_s = series.abs()
                max_e = float(abs_s.max()) if not abs_s.empty else 0.0
                mean_e = float(abs_s.mean()) if not abs_s.empty else 0.0
                rms_e = float(np.sqrt(np.mean(series ** 2))) if not series.empty else 0.0
                p1 = float((abs_s <= 1.0).mean() * 100.0) if not abs_s.empty else 100.0
                p2 = float((abs_s <= 2.0).mean() * 100.0) if not abs_s.empty else 100.0

                l_stat = LeafErrorStats(
                    leaf_number=i,
                    bank="Y1",
                    max_error_mm=max_e,
                    mean_error_mm=mean_e,
                    rms_error_mm=rms_e,
                    pct_within_1mm=p1,
                    pct_within_2mm=p2,
                )
                self.leaf_stats.append(l_stat)
                all_errors.append(abs_s.values)
                y1_rms_list.append(rms_e)
                if max_e > y1_max_err:
                    y1_max_err = max_e
                    y1_worst = i

        y1_overall_rms = float(np.mean(y1_rms_list)) if y1_rms_list else 0.0

        # Analyze Bank Y2
        y2_max_err, y2_worst = 0.0, 1
        y2_rms_list = []
        for i, col in enumerate(self.dataset.y2_error_cols, start=1):
            if col in df:
                series = df[col].dropna()
                abs_s = series.abs()
                max_e = float(abs_s.max()) if not abs_s.empty else 0.0
                mean_e = float(abs_s.mean()) if not abs_s.empty else 0.0
                rms_e = float(np.sqrt(np.mean(series ** 2))) if not series.empty else 0.0
                p1 = float((abs_s <= 1.0).mean() * 100.0) if not abs_s.empty else 100.0
                p2 = float((abs_s <= 2.0).mean() * 100.0) if not abs_s.empty else 100.0

                l_stat = LeafErrorStats(
                    leaf_number=i,
                    bank="Y2",
                    max_error_mm=max_e,
                    mean_error_mm=mean_e,
                    rms_error_mm=rms_e,
                    pct_within_1mm=p1,
                    pct_within_2mm=p2,
                )
                self.leaf_stats.append(l_stat)
                all_errors.append(abs_s.values)
                y2_rms_list.append(rms_e)
                if max_e > y2_max_err:
                    y2_max_err = max_e
                    y2_worst = i

        y2_overall_rms = float(np.mean(y2_rms_list)) if y2_rms_list else 0.0

        # Overall leaf stats
        overall_max = max(y1_max_err, y2_max_err)
        worst_leaf_name = f"Y1 Leaf {y1_worst}" if y1_max_err >= y2_max_err else f"Y2 Leaf {y2_worst}"
        overall_rms = float(np.mean(y1_rms_list + y2_rms_list)) if (y1_rms_list or y2_rms_list) else 0.0

        pct_within_1mm = 100.0
        pct_within_2mm = 100.0
        if all_errors:
            concat_errors = np.concatenate(all_errors)
            pct_within_1mm = float((concat_errors <= 1.0).mean() * 100.0)
            pct_within_2mm = float((concat_errors <= 2.0).mean() * 100.0)

        # Delivered MU
        delivered_mu = 0.0
        if self.dataset.dose_mu_col and self.dataset.dose_mu_col in df:
            delivered_mu = float(df[self.dataset.dose_mu_col].max())
        elif self.dataset.header.mu > 0:
            delivered_mu = self.dataset.header.mu

        self.stats = DeliveryQAStats(
            total_samples=total_samples,
            duration_seconds=duration,
            total_mu=delivered_mu,
            gantry_start_deg=g_start,
            gantry_end_deg=g_end,
            gantry_max_error_deg=g_max_err,
            gantry_mean_error_deg=g_mean_err,
            gantry_rms_error_deg=g_rms_err,
            y1_max_error_mm=y1_max_err,
            y1_rms_error_mm=y1_overall_rms,
            y1_worst_leaf=y1_worst,
            y2_max_error_mm=y2_max_err,
            y2_rms_error_mm=y2_overall_rms,
            y2_worst_leaf=y2_worst,
            overall_max_leaf_error_mm=overall_max,
            overall_rms_leaf_error_mm=overall_rms,
            worst_leaf_name=worst_leaf_name,
            pct_samples_within_1mm=pct_within_1mm,
            pct_samples_within_2mm=pct_within_2mm,
            x1_max_error_mm=x1_max_err,
            x2_max_error_mm=x2_max_err,
        )

        self.dataset.qa_stats = self.stats
        self.dataset.leaf_stats = self.leaf_stats

    def get_leaf_error_heatmap_matrix(self, bank: str = "Y1") -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
        """
        Returns:
            matrix: 2D array of shape (num_leaves, num_timestamps)
            leaf_numbers: 1D array of leaf numbers
            timestamps: 1D array of time values
        """
        df = self.active_df
        timestamps = df.index.to_numpy()
        cols = self.dataset.y1_error_cols if bank == "Y1" else self.dataset.y2_error_cols

        matrix_rows = []
        leaf_nums = []
        for i, col in enumerate(cols, start=1):
            if col in df:
                matrix_rows.append(df[col].to_numpy())
                leaf_nums.append(i)

        if not matrix_rows:
            return np.zeros((1, len(timestamps))), np.array([1]), timestamps

        matrix = np.array(matrix_rows)
        return matrix, np.array(leaf_nums), timestamps

    def get_aperture_at_index(self, index: int) -> Dict[str, Any]:
        """
        Extracts leaf and jaw positions at a specific row index.
        Returns:
            Dict containing y1_positions, y2_positions, x1_jaw, x2_jaw, gantry_angle, mu, time_s
        """
        df = self.df
        row = df.iloc[index]
        time_s = float(df.index[index])

        # Leaves Y1 & Y2 (up to 80 leaves)
        # In Elekta Unity TRF logs, Y1 leaf actual positions are recorded as positive when open.
        # For isocenter coordinates, Bank Y1 is on the negative axis, so sign is inverted (positive becomes negative, negative becomes positive).
        y1_pos = [-float(row[col]) for col in self.dataset.y1_actual_cols if col in row]
        y2_pos = [float(row[col]) for col in self.dataset.y2_actual_cols if col in row]

        # Leaf errors
        y1_err = [float(row[col]) for col in self.dataset.y1_error_cols if col in row]
        y2_err = [float(row[col]) for col in self.dataset.y2_error_cols if col in row]

        # Jaws (X1 = Top, X2 = Bottom; distance from isocenter in mm)
        x1_jaw = float(row[self.dataset.jaw_x1_col]) if self.dataset.jaw_x1_col and self.dataset.jaw_x1_col in row else 287.0
        x2_jaw = float(row[self.dataset.jaw_x2_col]) if self.dataset.jaw_x2_col and self.dataset.jaw_x2_col in row else 287.0

        # Gantry
        g_angle = float(row[self.dataset.gantry_actual_col]) if self.dataset.gantry_actual_col in row else 0.0
        g_err = float(row[self.dataset.gantry_error_col]) if self.dataset.gantry_error_col in row else 0.0

        # MU
        mu = float(row[self.dataset.dose_mu_col]) if self.dataset.dose_mu_col in row else 0.0

        # Dose Rate (MU/min)
        dose_rate = 0.0
        if self.dataset.dose_rate_col and self.dataset.dose_rate_col in row:
            try:
                dose_rate = float(row[self.dataset.dose_rate_col])
            except (ValueError, TypeError):
                dose_rate = 0.0

        # Gating State (motion monitoring / beam hold)
        gating_enabled = False
        if self.dataset.gating_col and self.dataset.gating_col in row:
            raw_gate = row[self.dataset.gating_col]
            try:
                gating_enabled = bool(float(raw_gate) > 0.5)
            except (ValueError, TypeError):
                gating_enabled = str(raw_gate).strip().lower() in ("1", "true", "enabled", "on", "active", "gate", "gating")

        return {
            "index": index,
            "time_s": time_s,
            "y1_pos": y1_pos,
            "y2_pos": y2_pos,
            "y1_err": y1_err,
            "y2_err": y2_err,
            "x1_jaw": x1_jaw,
            "x2_jaw": x2_jaw,
            "gantry_angle": g_angle,
            "gantry_error": g_err,
            "mu": mu,
            "dose_rate": dose_rate,
            "gating": gating_enabled,
        }

