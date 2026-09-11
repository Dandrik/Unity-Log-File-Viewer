"""Unit and integration tests for Elekta Unity SDD Package Handler and Navigator."""

import os
import io
import zipfile
import unittest
from datetime import datetime
import pandas as pd

from core.sdd_package import SDDPackage, SDDTRFEntry, SDDLogEntry, SDDMachineInfo
from core.trf_reader import TRFReader
from gui.app import UnityLogViewerApp
from gui.components.sdd_navigator import SDDNavigatorDialog


class TestSDDPackage(unittest.TestCase):
    """Tests for SDDPackage indexer, parser, and extractor."""

    @classmethod
    def setUpClass(cls):
        # Create a realistic synthetic SDD zip package for automated CI
        cls.temp_dir = os.path.join(os.path.dirname(__file__), "temp_sdd")
        os.makedirs(cls.temp_dir, exist_ok=True)
        cls.synthetic_zip_path = os.path.join(cls.temp_dir, "SDD+TRCC-NRT-999999+2+1+1+1+9999+1+EB+20260909+120000.zip")

        # Build synthetic TRFs
        ds_clinical = TRFReader.create_synthetic_dataset(num_points=50)

        # Encode a synthetic TRF-like stream or use mock bytes
        with zipfile.ZipFile(cls.synthetic_zip_path, "w") as z:
            # Add manifest
            manifest_content = (
                "RTD Linac Console Manifest File\t\tCreated:9/9/2026 12:00:00\n"
                "Host Name . . . . . . . . . . . . : TRCC-NRT-999999\n"
                "IPv4 Address. . . . . . . . . . . : 192.168.150.1\n"
                "OS Name\tMicrosoft Windows 10 Enterprise LTSC\n"
                "Version\t10.0.17763 Build 17763\n"
            )
            z.writestr("RTDManifest.txt", manifest_content)

            # Add machine log
            log_content = (
                "2026-09-09 12:00:01 [INFO] [GantryControl] Gantry subsystem ready\n"
                "2026-09-09 12:00:02 [INFO] [MLCController] All 80 leaf pairs calibrated\n"
                "2026-09-09 12:00:03 [WARN] [BurHwModule] X20Sl8100 status OK\n"
            )
            z.writestr("LOGFILE000009999", log_content)

            # Add mock TRFs with naming convention
            z.writestr("26_09_09 10_00_00 Z Warmup.trf", b"mock_warmup_bytes")
            z.writestr("26_09_09 10_15_00 Z DailyQA3.trf", b"mock_dailyqa_bytes")
            z.writestr("26_09_09 11_30_00 Z 1_1.trf", b"mock_clinical_bytes")

    @classmethod
    def tearDownClass(cls):
        # Cleanup synthetic zip
        if os.path.exists(cls.synthetic_zip_path):
            try:
                os.remove(cls.synthetic_zip_path)
            except OSError:
                pass
        if os.path.exists(cls.temp_dir):
            try:
                os.rmdir(cls.temp_dir)
            except OSError:
                pass

    def test_synthetic_sdd_metadata_and_categories(self):
        """Verifies metadata extraction, categories, and file discovery on synthetic SDD."""
        pkg = SDDPackage.open(self.synthetic_zip_path)
        self.assertEqual(pkg.machine_info.machine_id, "TRCC-NRT-999999")
        self.assertEqual(pkg.machine_info.export_timestamp, "2026-09-09 12:00:00")
        self.assertEqual(pkg.machine_info.os_name, "Microsoft Windows 10 Enterprise LTSC")
        self.assertIn("192.168.150.1", pkg.machine_info.ip_addresses)

        # Verify TRF discovery
        self.assertEqual(len(pkg.trf_entries), 3)
        categories = {e.display_name: e.category for e in pkg.trf_entries}
        self.assertEqual(categories["26_09_09 10_00_00 Z Warmup.trf"], "Warmup")
        self.assertEqual(categories["26_09_09 10_15_00 Z DailyQA3.trf"], "Daily QA")
        self.assertEqual(categories["26_09_09 11_30_00 Z 1_1.trf"], "Clinical Treatment")

        # Verify log discovery
        self.assertEqual(len(pkg.log_entries), 2)
        log_names = [e.display_name for e in pkg.log_entries]
        self.assertIn("LOGFILE000009999", log_names)
        self.assertIn("RTDManifest.txt", log_names)

        # Test log text reading
        txt = pkg.get_log_text("LOGFILE000009999")
        self.assertIn("GantryControl", txt)
        self.assertIn("MLCController", txt)

        pkg.close()

    def test_real_clinical_sdd_package_if_available(self):
        """Tests complete discovery and in-memory TRF decoding from real clinical SDD zip if present."""
        real_zip = r"C:\Users\USNelRog\OneDrive - Elekta\Desktop\SDD+TRCC-NRT-600064+2+1+1+1+12568+1+EB+20260908+145318.zip"
        if not os.path.isfile(real_zip):
            self.skipTest("Clinical SDD package zip not found on system.")

        pkg = SDDPackage.open(real_zip)
        self.assertEqual(pkg.machine_info.machine_id, "TRCC-NRT-600064")
        self.assertEqual(pkg.machine_info.export_timestamp, "2026-09-08 14:53:18")
        self.assertEqual(len(pkg.trf_entries), 57)
        self.assertGreater(len(pkg.log_entries), 50)

        # Check category distribution
        cats = [e.category for e in pkg.trf_entries]
        self.assertIn("Warmup", cats)
        self.assertIn("Daily QA", cats)
        self.assertIn("Clinical Treatment", cats)

        # Test decode of a real clinical beam directly from zip in memory
        clinical_entry = next((e for e in pkg.trf_entries if e.display_name == "26_09_03 12_07_07 Z 1_1.trf"), None)
        self.assertIsNotNone(clinical_entry)
        self.assertGreater(clinical_entry.mu, 700.0)

        dataset = pkg.read_trf_dataset(clinical_entry)
        self.assertGreater(len(dataset.dataframe), 5000)
        self.assertEqual(dataset.header.machine, "600064")

        # Test log decoding
        log_sample = pkg.log_entries[0]
        log_text = pkg.get_log_text(log_sample.filename)
        self.assertGreater(len(log_text), 0)

        pkg.close()

    def test_sdd_navigator_dialog_gui(self):
        """Verifies SDD Navigator dialog rendering, search filter, and load callbacks."""
        app = UnityLogViewerApp()
        app.withdraw()

        pkg = SDDPackage.open(self.synthetic_zip_path)

        loaded_trf = []
        loaded_log = []

        def on_trf(p, e):
            loaded_trf.append(e.display_name)

        def on_log(p, e):
            loaded_log.append(e.display_name)

        dlg = SDDNavigatorDialog(app, pkg, on_load_trf=on_trf, on_load_log=on_log)
        app.update()

        # Check treeview rows and high-contrast category tag colors
        rows = dlg.tree_trf.get_children()
        self.assertEqual(len(rows), 3)
        self.assertEqual(str(dlg.tree_trf.tag_configure("clinical", "foreground")), "#0f172a")
        self.assertEqual(str(dlg.tree_trf.tag_configure("qa", "foreground")), "#0369a1")
        self.assertEqual(str(dlg.tree_trf.tag_configure("warmup", "foreground")), "#b45309")
        self.assertEqual(str(dlg.tree_trf.tag_configure("shape", "foreground")), "#6d28d9")

        # Test Category Filter -> Warmup
        dlg.trf_cat_var.set("Warmup")
        dlg._apply_trf_filters()
        app.update()
        warmup_rows = dlg.tree_trf.get_children()
        self.assertEqual(len(warmup_rows), 1)

        # Test Search Filter
        dlg.trf_cat_var.set("All")
        dlg.trf_search_var.set("DailyQA")
        dlg._apply_trf_filters()
        app.update()
        qa_rows = dlg.tree_trf.get_children()
        self.assertEqual(len(qa_rows), 1)

        # Test Reset
        dlg._reset_trf_filters()
        app.update()
        self.assertEqual(len(dlg.tree_trf.get_children()), 3)

        # Test Selection and Load callback
        dlg.tree_trf.selection_set(rows[0])
        dlg._on_load_selected_trf()
        self.assertEqual(len(loaded_trf), 1)

        # Test Log Tab selection
        log_rows = dlg.tree_log.get_children()
        self.assertEqual(len(log_rows), 2)
        dlg.tree_log.selection_set(log_rows[0])
        dlg._on_load_selected_log()
        self.assertEqual(len(loaded_log), 1)

        dlg.destroy()
        pkg.close()
        app.destroy()


if __name__ == "__main__":
    unittest.main()

