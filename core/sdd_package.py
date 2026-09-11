"""Elekta Unity & Linac SDD (Service Diagnostic Data) Package Handler.

Handles loading, indexing, and extraction of Elekta SDD diagnostic bundles
directly from .zip archives or extracted directories without requiring manual unzipping.
"""

import os
import re
import zipfile
from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, List, Optional, Tuple, Union

from pymedphys._trf.decode.partition import split_into_header_table
from pymedphys._trf.decode.header import decode_header
from core.models import TRFDataset
from core.trf_reader import TRFReader


@dataclass
class SDDTRFEntry:
    """Metadata record for a TRF delivery trajectory inside an SDD package."""
    filename: str          # Path within zip / directory
    display_name: str      # Basename of the file
    date: str              # Date string from header (e.g. '26/09/03')
    time: str              # Time string from header (e.g. '12:07:07')
    field_name: str        # Plan or field label (e.g. '1_1', 'DailyQA3')
    mu: float              # Delivered Monitor Units (scaled to true MU)
    file_size: int         # Size in bytes
    category: str          # 'Clinical Treatment', 'Daily QA', 'Warmup', 'Shape / Test'
    delivery_dt: Optional[datetime] = None  # Parsed datetime for sorting


@dataclass
class SDDLogEntry:
    """Metadata record for a machine or subsystem log file inside an SDD package."""
    filename: str
    display_name: str
    file_size: int
    category: str          # 'Machine Event Log', 'System Info', 'Manifest', 'Boot Log', 'Other'
    date_time: str = "--"  # Formatted datetime e.g. '2026-09-08 14:53:20'
    modified_dt: Optional[datetime] = None  # Parsed datetime for chronological sorting


@dataclass
class SDDMachineInfo:
    """Machine and console configuration metadata extracted from an SDD package."""
    machine_id: str = "Unknown Linac"
    package_name: str = ""
    export_timestamp: str = ""
    os_name: str = ""
    os_version: str = ""
    ip_addresses: List[str] = field(default_factory=list)
    raw_manifest: str = ""


class SDDPackage:
    """Represents an opened Elekta Service Diagnostic Data (SDD) package."""

    def __init__(self, path: str):
        self.path = os.path.abspath(path)
        self.name = os.path.basename(self.path)
        self.is_zip = os.path.isfile(self.path) and self.path.lower().endswith(".zip")
        self.is_dir = os.path.isdir(self.path)

        if not (self.is_zip or self.is_dir):
            raise ValueError(f"Path is neither a valid zip file nor a directory: {path}")

        self._zip_file: Optional[zipfile.ZipFile] = None
        if self.is_zip:
            self._zip_file = zipfile.ZipFile(self.path, "r")

        self.machine_info = SDDMachineInfo(package_name=self.name)
        self.trf_entries: List[SDDTRFEntry] = []
        self.log_entries: List[SDDLogEntry] = []
        self.other_files: List[str] = []

        self._index_package()

    @classmethod
    def open(cls, path: str) -> "SDDPackage":
        """Opens an SDD package from a .zip file or folder path."""
        return cls(path)

    def close(self) -> None:
        """Closes underlying zip file if opened."""
        if self._zip_file:
            try:
                self._zip_file.close()
            except Exception:
                pass
            self._zip_file = None

    def __enter__(self) -> "SDDPackage":
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        self.close()

    # -------------------------------------------------------------------------
    # Indexing
    # -------------------------------------------------------------------------

    def _get_file_list(self) -> List[Tuple[str, int, str, Optional[datetime]]]:
        """Returns list of (relative_path, size_bytes, date_time_str, dt_obj) for all files in the package."""
        if self.is_zip and self._zip_file:
            result = []
            for info in self._zip_file.infolist():
                if info.is_dir():
                    continue
                dt_obj = None
                date_str = "--"
                if info.date_time and len(info.date_time) >= 6:
                    try:
                        y, mo, d, h, mi, s = info.date_time[:6]
                        if y >= 1980 and 1 <= mo <= 12 and 1 <= d <= 31:
                            dt_obj = datetime(y, mo, d, h, mi, s)
                            date_str = dt_obj.strftime("%Y-%m-%d %H:%M:%S")
                    except (ValueError, OverflowError):
                        pass
                result.append((info.filename, info.file_size, date_str, dt_obj))
            return result
        elif self.is_dir:
            file_list = []
            for root, _, files in os.walk(self.path):
                for f in files:
                    full_p = os.path.join(root, f)
                    rel_p = os.path.relpath(full_p, self.path)
                    try:
                        sz = os.path.getsize(full_p)
                    except OSError:
                        sz = 0
                    dt_obj = None
                    date_str = "--"
                    try:
                        mtime = os.path.getmtime(full_p)
                        dt_obj = datetime.fromtimestamp(mtime)
                        date_str = dt_obj.strftime("%Y-%m-%d %H:%M:%S")
                    except (OSError, ValueError, OverflowError):
                        pass
                    file_list.append((rel_p, sz, date_str, dt_obj))
            return file_list
        return []

    def _read_raw_bytes(self, filename: str, max_bytes: Optional[int] = None) -> bytes:
        """Reads raw bytes from the package."""
        if self.is_zip and self._zip_file:
            with self._zip_file.open(filename, "r") as f:
                return f.read() if max_bytes is None else f.read(max_bytes)
        elif self.is_dir:
            full_path = os.path.join(self.path, filename)
            with open(full_path, "rb") as f:
                return f.read() if max_bytes is None else f.read(max_bytes)
        return b""

    def _index_package(self) -> None:
        """Discovers, parses, and categorizes all TRFs, logs, and manifest files."""
        files = self._get_file_list()

        # 1. Parse Machine Info from package name and manifest
        self._parse_machine_metadata(files)

        # 2. Index TRF treatment delivery files
        trf_files = [f for f in files if f[0].lower().endswith(".trf")]
        for rel_name, size, d_str, dt_obj in trf_files:
            try:
                # Read first 16 KB to parse the header instantaneously
                header_slice = self._read_raw_bytes(rel_name, max_bytes=16384)
                entry = self._parse_trf_header(rel_name, size, header_slice)
                self.trf_entries.append(entry)
            except Exception:
                # Fallback to basic file-based entry
                cat = self._classify_trf_category(rel_name, "")
                self.trf_entries.append(SDDTRFEntry(
                    filename=rel_name,
                    display_name=os.path.basename(rel_name),
                    date="--",
                    time="--",
                    field_name="--",
                    mu=0.0,
                    file_size=size,
                    category=cat,
                    delivery_dt=dt_obj
                ))

        # Sort TRFs chronologically by delivery datetime (or filename)
        self.trf_entries.sort(key=lambda e: (e.delivery_dt or datetime.min, e.display_name))

        # 3. Index Machine Event & Subsystem Logs
        for rel_name, size, d_str, dt_obj in files:
            lower = rel_name.lower()
            base = os.path.basename(rel_name)
            if lower.endswith(".trf"):
                continue

            if "logfile" in base.lower():
                self.log_entries.append(SDDLogEntry(
                    filename=rel_name,
                    display_name=base,
                    file_size=size,
                    category="Machine Event Log",
                    date_time=d_str,
                    modified_dt=dt_obj
                ))
            elif "manifest" in lower:
                self.log_entries.append(SDDLogEntry(
                    filename=rel_name,
                    display_name=base,
                    file_size=size,
                    category="Manifest",
                    date_time=d_str,
                    modified_dt=dt_obj
                ))
            elif "registry" in lower:
                self.log_entries.append(SDDLogEntry(
                    filename=rel_name,
                    display_name=base,
                    file_size=size,
                    category="Registry Dump",
                    date_time=d_str,
                    modified_dt=dt_obj
                ))
            elif "bootlog" in lower or "crashlog" in lower:
                self.log_entries.append(SDDLogEntry(
                    filename=rel_name,
                    display_name=base,
                    file_size=size,
                    category="RTC Boot/Crash Log",
                    date_time=d_str,
                    modified_dt=dt_obj
                ))
            elif lower.endswith(".txt") or lower.endswith(".log") or lower.endswith(".evt"):
                self.log_entries.append(SDDLogEntry(
                    filename=rel_name,
                    display_name=base,
                    file_size=size,
                    category="System Log",
                    date_time=d_str,
                    modified_dt=dt_obj
                ))
            else:
                self.other_files.append(rel_name)

        # Sort logs by category by default, then chronologically by timestamp
        self.log_entries.sort(key=lambda e: (e.category, e.modified_dt or datetime.min, e.display_name))

    def _parse_machine_metadata(self, files: List[Tuple]) -> None:
        """Extracts Linac ID, OS, software build, and timestamps from filename and manifest."""
        # Check filename pattern e.g. SDD+TRCC-NRT-600064+2+1+1+1+12568+1+EB+20260908+145318
        m_id = re.search(r"SDD\+([^+]+)\+", self.name, re.IGNORECASE)
        if m_id:
            self.machine_info.machine_id = m_id.group(1).strip()

        ts_match = re.search(r"(\d{4})(\d{2})(\d{2})\+(\d{2})(\d{2})(\d{2})", self.name)
        if ts_match:
            y, mo, d, h, mi, s = ts_match.groups()
            self.machine_info.export_timestamp = f"{y}-{mo}-{d} {h}:{mi}:{s}"

        # Inspect manifest file if present
        for item in files:
            rel_name = item[0]
            if "manifest" in rel_name.lower() and rel_name.lower().endswith(".txt"):
                try:
                    data = self._read_raw_bytes(rel_name, max_bytes=65536)
                    txt = data.decode("utf-8", errors="replace")
                    self.machine_info.raw_manifest = txt

                    # Hostname
                    m_host = re.search(r"Host Name[ .:]+([^\r\n]+)", txt)
                    if m_host and self.machine_info.machine_id == "Unknown Linac":
                        self.machine_info.machine_id = m_host.group(1).strip()

                    # Created timestamp
                    m_cr = re.search(r"Created:[ \t]*([^\r\n]+)", txt)
                    if m_cr and not self.machine_info.export_timestamp:
                        self.machine_info.export_timestamp = m_cr.group(1).strip()

                    # IP Addresses
                    ips = re.findall(r"IPv4 Address[ .:]+([0-9.]+)", txt)
                    self.machine_info.ip_addresses = list(set(ips))

                    # OS information
                    m_os = re.search(r"OS Name[ \t]+([^\r\n]+)", txt)
                    if m_os:
                        self.machine_info.os_name = m_os.group(1).strip()
                    m_ver = re.search(r"Version[ \t]+([^\r\n]+)", txt)
                    if m_ver:
                        self.machine_info.os_version = m_ver.group(1).strip()
                except Exception:
                    pass
                break

    def _parse_trf_header(self, rel_name: str, file_size: int, header_slice: bytes) -> SDDTRFEntry:
        """Parses TRF header bytes without decoding the full trajectory table."""
        h_bytes, _ = split_into_header_table(header_slice)
        raw_header = decode_header(h_bytes)

        date_str = str(getattr(raw_header, "date", "") or "").strip()
        time_str = str(getattr(raw_header, "time", "") or "").strip()
        field_str = str(getattr(raw_header, "field_label", "") or getattr(raw_header, "field_name", "") or "").strip()
        raw_mu = float(getattr(raw_header, "mu", 0) or 0)
        mu = raw_mu / 10.0 if raw_mu else 0.0

        # Attempt to parse date/time into datetime object
        dt_val = None
        if date_str and time_str:
            for fmt in ("%y/%m/%d %H:%M:%S", "%Y/%m/%d %H:%M:%S", "%d/%m/%y %H:%M:%S", "%d/%m/%Y %H:%M:%S"):
                try:
                    clean_ts = f"{date_str} {time_str}".replace("Z", "").strip()
                    dt_val = datetime.strptime(clean_ts, fmt)
                    break
                except ValueError:
                    pass

        # Fallback date parse from filename e.g. 26_09_03 12_07_07 Z 1_1.trf
        base = os.path.basename(rel_name)
        if not dt_val:
            fn_match = re.search(r"(\d{2})_(\d{2})_(\d{2})[ _](\d{2})_(\d{2})_(\d{2})", base)
            if fn_match:
                y, m, d, hh, mm, ss = [int(x) for x in fn_match.groups()]
                y_full = 2000 + y if y < 100 else y
                try:
                    dt_val = datetime(y_full, m, d, hh, mm, ss)
                    if not date_str:
                        date_str = f"{y:02d}/{m:02d}/{d:02d}"
                    if not time_str:
                        time_str = f"{hh:02d}:{mm:02d}:{ss:02d}"
                except ValueError:
                    pass

        category = self._classify_trf_category(base, field_str)

        return SDDTRFEntry(
            filename=rel_name,
            display_name=base,
            date=date_str or "--",
            time=time_str or "--",
            field_name=field_str or "--",
            mu=mu,
            file_size=file_size,
            category=category,
            delivery_dt=dt_val
        )

    def _classify_trf_category(self, filename: str, field_name: str) -> str:
        """Classifies TRF into clinical, QA, warmup, or test shape."""
        combined = f"{filename} {field_name}".upper()
        if "WARMUP" in combined or "WARM UP" in combined:
            return "Warmup"
        elif "DAILYQA" in combined or "DAILY QA" in combined or "QA" in combined:
            return "Daily QA"
        elif "CLOSED FIELD" in combined or "FIELD SHAPE" in combined or "SHAPE" in combined or "TEST" in combined:
            return "Shape / Test"
        else:
            return "Clinical Treatment"

    # -------------------------------------------------------------------------
    # Extraction & Reading
    # -------------------------------------------------------------------------

    def get_trf_bytes(self, filename: str) -> bytes:
        """Extracts complete raw bytes for a specific TRF file."""
        return self._read_raw_bytes(filename)

    def read_trf_dataset(self, entry_or_filename: Union[SDDTRFEntry, str]) -> TRFDataset:
        """Decodes a TRF file from the SDD package directly into a TRFDataset."""
        filename = entry_or_filename.filename if isinstance(entry_or_filename, SDDTRFEntry) else entry_or_filename
        trf_bytes = self.get_trf_bytes(filename)
        base = os.path.basename(filename)
        source_name = f"SDD [{self.machine_info.machine_id}]: {base}"
        return TRFReader.read_bytes(trf_bytes, source_name=source_name)

    def get_log_text(self, filename: str, max_bytes: int = 5000000) -> str:
        """Extracts and formats text from a log file inside the SDD package.

        Supports standard UTF-8/UTF-16 text files as well as serialized
        Elekta Atlantic/Unity logger files (LOGFILE00000xxxx).
        """
        raw_data = self._read_raw_bytes(filename, max_bytes=max_bytes)
        if not raw_data:
            return ""

        # 1. UTF-16 LE with BOM check
        if raw_data.startswith(b"\xff\xfe") or raw_data.startswith(b"\xfe\xff"):
            try:
                return raw_data.decode("utf-16", errors="replace")
            except Exception:
                pass

        # 2. Check if file is serialized Unity Atlantic Log (e.g. LOGFILE00000...)
        if b"Unity Log File Header" in raw_data or b"Elekta.Atlantic" in raw_data:
            extracted_lines = []
            for s in re.findall(b"[\x20-\x7e]{6,}", raw_data):
                line = s.decode("ascii", errors="replace").strip()
                if not line.startswith("Elekta.Atlantic") and not line.startswith("%Header"):
                    extracted_lines.append(line)
            header_notice = f"--- [Decoded Elekta Atlantic Log: {os.path.basename(filename)}] ---\n"
            return header_notice + "\n".join(extracted_lines)

        # 3. Standard text fallback (UTF-8 with replace)
        return raw_data.decode("utf-8", errors="replace")

