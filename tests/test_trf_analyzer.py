"""Tests for TRF Analyzer."""

import unittest
from core.trf_reader import TRFReader
from core.trf_analyzer import TRFAnalyzer


class TestTRFAnalyzer(unittest.TestCase):

    def setUp(self):
        self.dataset = TRFReader.create_synthetic_dataset(num_points=200)
        self.analyzer = TRFAnalyzer(self.dataset)

    def test_metrics_calculation(self):
        stats = self.analyzer.stats
        self.assertIsNotNone(stats)
        self.assertEqual(stats.total_samples, 200)
        self.assertGreater(stats.duration_seconds, 0)
        self.assertGreater(stats.overall_max_leaf_error_mm, 0)
        self.assertGreaterEqual(stats.pct_samples_within_2mm, 90.0)

        # Leaf 24 was deliberately perturbed in synthetic data
        self.assertIn("24", stats.worst_leaf_name)

    def test_heatmap_matrix(self):
        matrix, leaves, times = self.analyzer.get_leaf_error_heatmap_matrix("Y1")
        self.assertEqual(matrix.shape[0], 80)
        self.assertEqual(matrix.shape[1], 200)
        self.assertEqual(len(leaves), 80)
        self.assertEqual(len(times), 200)

    def test_aperture_snapshot(self):
        snap = self.analyzer.get_aperture_at_index(50)
        self.assertEqual(len(snap["y1_pos"]), 80)
        self.assertEqual(len(snap["y2_pos"]), 80)
        self.assertGreater(snap["x1_jaw"], 0)
        self.assertGreater(snap["x2_jaw"], 0)
        self.assertGreater(snap["time_s"], 0)
        self.assertIn("dose_rate", snap)
        self.assertIsInstance(snap["dose_rate"], float)
        self.assertGreater(snap["dose_rate"], 400.0)
        self.assertIn("gating", snap)
        self.assertIsInstance(snap["gating"], bool)


if __name__ == "__main__":
    unittest.main()

