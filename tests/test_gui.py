"""Automated test for GUI initialization and rendering."""

import unittest
import os
import sys

# Ensure project root is in path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from gui.app import UnityLogViewerApp


class TestGUI(unittest.TestCase):

    def setUp(self):
        self.app = UnityLogViewerApp()
        self.app.withdraw()  # Hide window during automated test

    def tearDown(self):
        self.app.destroy()

    def test_gui_initialization_and_sample_load(self):
        """Verifies that all GUI components, canvas, and matplotlib figures load and render."""
        # Process pending events
        self.app.update()

        # Load sample TRF data
        self.app.trf_view.load_sample_data()
        self.app.update()

        # Verify TRF datasets loaded
        self.assertIsNotNone(self.app.trf_view.dataset)
        self.assertIsNotNone(self.app.trf_view.analyzer)
        self.assertEqual(self.app.trf_view.card_machine.value_label.cget("text"), "Unity-001 (7T/Linac)")

        # Verify MLC Canvas rendered
        self.app.trf_view.mlc_canvas.seek_last()
        self.app.update()
        self.assertEqual(
            self.app.trf_view.mlc_canvas.current_frame,
            self.app.trf_view.mlc_canvas.total_frames - 1
        )

        # Verify Text Log sample load
        self.app.text_log_view.load_sample_log()
        self.app.update()
        self.assertGreater(len(self.app.text_log_view.active_entries), 0)
        self.assertGreater(len(self.app.text_log_view.tree.get_children()), 0)

    def test_bev_scaling_with_window_resize(self):
        """Verifies that the BEV canvas scales proportionally when resized."""
        self.app.trf_view.load_sample_data()

        class MockEvent:
            def __init__(self, w, h):
                self.width = w
                self.height = h

        # Small window size
        self.app.trf_view.mlc_canvas._on_resize(MockEvent(600, 500))
        scale_small = self.app.trf_view.mlc_canvas.scale

        # Large window size (maximized)
        self.app.trf_view.mlc_canvas._on_resize(MockEvent(1200, 900))
        scale_large = self.app.trf_view.mlc_canvas.scale

        self.assertGreater(scale_large, scale_small)

    def test_unity_field_geometry(self):
        """Verifies Elekta Unity 57.4 cm x 22.0 cm field size and 7.175 mm leaf pitch."""
        from gui.components.mlc_canvas import (
            UNITY_FIELD_STACK_MM,
            UNITY_FIELD_TRAVEL_MM,
            UNITY_LEAF_WIDTH_MM,
            UNITY_LEAF_COUNT,
            UNITY_STACK_LIMIT_MM,
        )
        self.assertEqual(UNITY_FIELD_STACK_MM, 574.0)
        self.assertEqual(UNITY_FIELD_TRAVEL_MM, 220.0)
        self.assertEqual(UNITY_LEAF_WIDTH_MM, 7.175)
        self.assertEqual(UNITY_LEAF_COUNT, 80)
        self.assertEqual(UNITY_STACK_LIMIT_MM, 287.0)

        self.app.trf_view.load_sample_data()
        canvas = self.app.trf_view.mlc_canvas
        self.assertGreater(canvas.scale, 0.0)

        # Hover test: near top of stack (Leaf 1) and near bottom of stack (Leaf 80)
        class MockMouseEvent:
            def __init__(self, x, y):
                self.x = x
                self.y = y

        # Top of leaf stack
        top_y = canvas.cy - (UNITY_STACK_LIMIT_MM * canvas.scale) + 2
        canvas._on_mouse_hover(MockMouseEvent(canvas.cx, top_y))
        self.assertIn("Leaf 01", canvas.lbl_hover.cget("text"))

        # Bottom of leaf stack
        bot_y = canvas.cy + (UNITY_STACK_LIMIT_MM * canvas.scale) - 2
        canvas._on_mouse_hover(MockMouseEvent(canvas.cx, bot_y))
        self.assertIn("Leaf 80", canvas.lbl_hover.cget("text"))

    def test_y2_orientation_selection(self):
        """Verifies that switching Y2 orientation (Right, Left, Top, Bottom) updates canvas."""
        self.app.trf_view.load_sample_data()
        canvas = self.app.trf_view.mlc_canvas
        for ori in ["Right", "Left", "Top", "Bottom"]:
            canvas.y2_combo.set(ori)
            canvas._on_y2_orientation_changed()
            self.assertEqual(canvas.y2_orientation, ori)
            self.assertGreater(len(canvas.canvas.find_withtag("leaf")), 0)
            self.assertGreater(len(canvas.canvas.find_withtag("jaw")), 0)


if __name__ == "__main__":
    unittest.main()

