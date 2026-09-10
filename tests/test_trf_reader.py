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


if __name__ == "__main__":
    unittest.main()

