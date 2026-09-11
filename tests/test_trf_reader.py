"""Tests for TRF Reader and dataset mapping."""

import unittest
from core.trf_reader import TRFReader


class TestTRFReader(unittest.TestCase):

    def test_synthetic_dataset_creation(self):
        dataset = TRFReader.create_synthetic_dataset(num_points=100)

        # Verify Header
        self.assertIn("Unity", dataset.header.machine)
        self.assertEqual(dataset.header.mu, 250.0)

        # Verify columns mapping
        self.assertEqual(len(dataset.y1_actual_cols), 80)
        self.assertEqual(len(dataset.y2_actual_cols), 80)
        self.assertEqual(len(dataset.y1_error_cols), 80)
        self.assertEqual(len(dataset.y2_error_cols), 80)

        # Verify axes
        self.assertIsNotNone(dataset.gantry_actual_col)
        self.assertIsNotNone(dataset.gantry_error_col)
        self.assertIsNotNone(dataset.jaw_x1_col)
        self.assertIsNotNone(dataset.jaw_x2_col)

        # Check dataframe size
        self.assertEqual(len(dataset.dataframe), 100)

    def test_trf_header_mu_scaling(self):
        """Verifies that raw header MU (stored in 0.1 MU units / dMU) is correctly divided by 10.0."""
        from unittest.mock import MagicMock

        raw_hdr = MagicMock()
        raw_hdr.machine = "Unity-01"
        raw_hdr.date = "2026-09-10 10:15:32"
        raw_hdr.timezone = "+00:00"
        raw_hdr.field_label = "1-1"
        raw_hdr.field_name = "VMAT_PROSTATE"
        raw_hdr.mu = 7614.0  # 7614.0 in raw header corresponds to 761.4 MU
        raw_hdr.version = 2

        header = TRFReader._build_header(raw_hdr)
        self.assertAlmostEqual(header.mu, 761.4, places=2)
        self.assertEqual(header.machine, "Unity-01")
        self.assertEqual(header.field_name, "VMAT_PROSTATE")


if __name__ == "__main__":
    unittest.main()

