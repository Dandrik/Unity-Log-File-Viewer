"""Tests for text log parser."""

import unittest
from core.text_log_parser import TextLogParser


SAMPLE_LOG_TEXT = """
2026-09-10 08:30:01.102 [LinacController] INFO - System initialization complete. Subsystems armed.
2026-09-10 08:30:05.450 [MLCService] WARN - Leaf 24 calibration delta exceeds nominal threshold (0.42 mm).
2026-09-10 08:30:12.890 [GantryDriver] ERROR - Positional lag detected on Gantry axis at 182.4 deg.
    Error code: ERR_GANTRY_LAG_0x4F
    Stack trace: at UnityLinac.Axis.Monitor() in axis_monitor.cs:line 142
2026-09-10 08:30:15.000 [SafetyInterlock] CRITICAL - Radiation beam interrupted by hardware interlock #12.
2026-09-10 08:30:20.111 [RFSubsystem] DEBUG - Magnetron AFC tuning parameter: 14.85 kV.
"""


class TestTextLogParser(unittest.TestCase):

    def setUp(self):
        self.parser = TextLogParser()

    def test_parse_sample_log(self):
        entries = self.parser.parse_text(SAMPLE_LOG_TEXT)
        self.assertEqual(len(entries), 5)

        # Check line 1
        self.assertEqual(entries[0].level, "INFO")
        self.assertEqual(entries[0].component, "LinacController")
        self.assertIn("initialization complete", entries[0].message)

        # Check multi-line traceback on entry 3 (ERROR)
        self.assertEqual(entries[2].level, "ERROR")
        self.assertEqual(entries[2].component, "GantryDriver")
        self.assertIn("ERR_GANTRY_LAG_0x4F", entries[2].details)

        # Check critical entry
        self.assertEqual(entries[3].level, "CRITICAL")
        self.assertEqual(entries[3].component, "SafetyInterlock")

    def test_filter_by_level(self):
        self.parser.parse_text(SAMPLE_LOG_TEXT)
        errors = self.parser.filter_entries(levels=["ERROR", "CRITICAL"])
        self.assertEqual(len(errors), 2)
        levels = {e.level for e in errors}
        self.assertEqual(levels, {"ERROR", "CRITICAL"})

    def test_search_query(self):
        self.parser.parse_text(SAMPLE_LOG_TEXT)
        matches = self.parser.filter_entries(search_query="Leaf 24")
        self.assertEqual(len(matches), 1)
        self.assertEqual(matches[0].component, "MLCService")

    def test_regex_search(self):
        self.parser.parse_text(SAMPLE_LOG_TEXT)
        matches = self.parser.filter_entries(search_query=r"ERR_GANTRY_[A-Z0-9_]+", is_regex=True)
        self.assertEqual(len(matches), 1)
        self.assertEqual(matches[0].component, "GantryDriver")

    def test_summary_stats(self):
        self.parser.parse_text(SAMPLE_LOG_TEXT)
        stats = self.parser.get_summary_stats()
        self.assertEqual(stats["TOTAL"], 5)
        self.assertEqual(stats["INFO"], 1)
        self.assertEqual(stats["WARN"], 1)
        self.assertEqual(stats["ERROR"], 1)
        self.assertEqual(stats["CRITICAL"], 1)
        self.assertEqual(stats["DEBUG"], 1)


if __name__ == "__main__":
    unittest.main()

