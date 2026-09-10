"""Launcher script for Elekta Unity Log & TRF File Viewer."""

import argparse
import sys
import os

# Add workspace directory to python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from gui.app import UnityLogViewerApp
from core.trf_reader import TRFReader


def main():
    parser = argparse.ArgumentParser(description="Elekta Unity MR-Linac Log and TRF Delivery File Viewer")
    parser.add_argument("--trf", type=str, help="Path to .trf delivery log file to open on startup")
    parser.add_argument("--log", type=str, help="Path to machine text log file to open on startup")
    parser.add_argument("--sample", action="store_true", help="Automatically load sample TRF and text log data on startup")

    args = parser.parse_args()

    app = UnityLogViewerApp()

    # Pre-load files if requested
    if args.trf and os.path.exists(args.trf):
        try:
            dataset = TRFReader.read_file(args.trf)
            app.trf_view.load_dataset(dataset, source_name=args.trf)
            app.notebook.select(0)
        except Exception as e:
            print(f"Error loading TRF on startup: {e}")
    elif args.sample:
        app.trf_view.load_sample_data()
        app.text_log_view.load_sample_log()

    if args.log and os.path.exists(args.log):
        try:
            app.text_log_view.parser.parse_file(args.log)
            app.text_log_view.lbl_file_info.config(text=f"Loaded: {args.log}")
            app.text_log_view._on_logs_loaded()
            if not args.trf:
                app.notebook.select(1)
        except Exception as e:
            print(f"Error loading text log on startup: {e}")

    app.mainloop()


if __name__ == "__main__":
    main()

