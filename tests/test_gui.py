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

        # Hover test: near start of stack (Leaf 1) and near end of stack (Leaf 80)
        class MockMouseEvent:
            def __init__(self, x, y):
                self.x = x
                self.y = y

        # Default orientation is "Top" (horizontal leaf stack along X)
        self.assertEqual(canvas.y2_orientation, "Top")
        left_x = canvas.cx - (UNITY_STACK_LIMIT_MM * canvas.scale) + 2
        canvas._on_mouse_hover(MockMouseEvent(left_x, canvas.cy))
        self.assertIn("Leaf 01", canvas.lbl_hover.cget("text"))

        right_x = canvas.cx + (UNITY_STACK_LIMIT_MM * canvas.scale) - 2
        canvas._on_mouse_hover(MockMouseEvent(right_x, canvas.cy))
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
    def test_treatment_playback_datetime_display(self):
        """Verifies treatment start, current control point, and treatment end timestamps."""
        self.app.trf_view.load_sample_data()
        canvas = self.app.trf_view.mlc_canvas

        # Start date/time should be parsed from header (2026-09-10 10:15:32)
        self.assertEqual(canvas.lbl_tx_start.cget("text"), "2026-09-10 10:15:32")

        # Frame 0: Current CP should equal Start date/time
        self.assertEqual(canvas.lbl_tx_cp.cget("text"), "2026-09-10 10:15:32")

        # End date/time should reflect the full duration (23.96s -> 10:15:55)
        self.assertEqual(canvas.lbl_tx_end.cget("text"), "2026-09-10 10:15:55")

        # Seek to last frame: Current CP should update to match End date/time
        canvas.seek_last()
        self.assertEqual(canvas.lbl_tx_cp.cget("text"), canvas.lbl_tx_end.cget("text"))

        # Seek to frame 0: Current CP should return to Start date/time
        canvas.seek_first()
        self.assertEqual(canvas.lbl_tx_cp.cget("text"), canvas.lbl_tx_start.cget("text"))

    def test_treatment_playback_doserate_display(self):
        """Verifies dose rate readout and vertical bar graph on the Treatment Playback canvas."""
        self.app.trf_view.load_sample_data()
        canvas = self.app.trf_view.mlc_canvas

        # Initial dose rate from synthetic data should be ~450 MU/min
        self.assertGreater(canvas.current_dose_rate, 400.0)
        self.assertTrue(canvas.lbl_dose_rate.cget("text").endswith("MU/min"))

        # Canvas items tagged with 'doserate' must be drawn
        doserate_items = canvas.canvas.find_withtag("doserate")
        self.assertGreater(len(doserate_items), 5)

        # Explicitly verify 0.0 MU/min render (bar empty, label 0.0 MU/min)
        canvas._draw_doserate(0.0)
        self.assertEqual(canvas.lbl_dose_rate.cget("text"), "0.0 MU/min")
        zero_items = canvas.canvas.find_withtag("doserate")
        self.assertGreater(len(zero_items), 5)

        # Explicitly verify 500.0 MU/min render
        canvas._draw_doserate(500.0)
        self.assertEqual(canvas.lbl_dose_rate.cget("text"), "500.0 MU/min")
        full_items = canvas.canvas.find_withtag("doserate")
        self.assertGreater(len(full_items), 5)

    def test_treatment_playback_gating_box(self):
        """Verifies Gating box inside doserate subwindow turning red when enabled."""
        self.app.trf_view.load_sample_data()
        canvas = self.app.trf_view.mlc_canvas

        # Normal/disabled state
        canvas._draw_doserate(450.0, is_gating=False)
        self.assertEqual(canvas.lbl_gating.cget("text"), "DISABLED")
        disabled_rects = [
            i for i in canvas.canvas.find_withtag("doserate")
            if canvas.canvas.type(i) == "rectangle" and canvas.canvas.itemcget(i, "fill") == "#0b1120"
        ]
        # Should have meter trough and gating box in #0b1120
        self.assertGreaterEqual(len(disabled_rects), 2)

        # Gated/enabled state (red box #dc2626, label ENABLED)
        canvas._draw_doserate(0.0, is_gating=True)
        self.assertEqual(canvas.lbl_gating.cget("text"), "ENABLED")
        red_rects = [
            i for i in canvas.canvas.find_withtag("doserate")
            if canvas.canvas.type(i) == "rectangle" and canvas.canvas.itemcget(i, "fill") == "#dc2626"
        ]
        self.assertEqual(len(red_rects), 1)

        # Check "Gating" text item
        gating_texts = [
            i for i in canvas.canvas.find_withtag("doserate")
            if canvas.canvas.type(i) == "text" and canvas.canvas.itemcget(i, "text") == "Gating"
        ]
        self.assertEqual(len(gating_texts), 1)
        self.assertEqual(canvas.canvas.itemcget(gating_texts[0], "fill"), "#ffffff")


if __name__ == "__main__":
    unittest.main()

