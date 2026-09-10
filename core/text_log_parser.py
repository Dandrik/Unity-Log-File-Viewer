"""Text and machine event log parser for Elekta Unity systems."""

import re
from datetime import datetime
from typing import Dict, List, Optional, Tuple
from core.models import LogEntry


# Common timestamp patterns encountered in medical and Linac logs
TIMESTAMP_PATTERNS = [
    # 2026-09-10 14:23:45.123 or 2026-09-10 14:23:45
    r"(\d{4}[-/]\d{2}[-/]\d{2}[ T]\d{2}:\d{2}:\d{2}(?:\.\d+)?)",
    # 10/09/2026 14:23:45 or 10/09/26 14:23:45
    r"(\d{2}[-/]\d{2}[-/]\d{2,4}[ T]\d{2}:\d{2}:\d{2}(?:\.\d+)?)",
    # ISO 8601 with optional timezone: 2026-09-10T14:23:45Z
    r"(\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.\d+)?(?:Z|[+-]\d{2}:?\d{2})?)",
]

LEVEL_PATTERN = re.compile(
    r"\b(CRITICAL|FATAL|ERROR|SEVERE|WARN(?:ING)?|INFO|DEBUG|TRACE)\b",
    re.IGNORECASE
)

COMPONENT_PATTERN = re.compile(
    r"\[([A-Za-z0-9_\-.: ]+)\]|\b([A-Za-z0-9_\-]+(?:Service|Manager|Controller|Driver|MLC|Gantry|Interlock|RF|MR|Beam|Dose))\b"
)


class TextLogParser:
    """Parses, filters, and analyzes text-based log files."""

    def __init__(self):
        self.entries: List[LogEntry] = []
        self._compiled_ts_regexes = [re.compile(p) for p in TIMESTAMP_PATTERNS]

    def parse_file(self, filepath: str) -> List[LogEntry]:
        """Parses a text log file into structured LogEntry records."""
        with open(filepath, "r", encoding="utf-8", errors="replace") as f:
            lines = f.readlines()
        return self.parse_lines(lines)

    def parse_text(self, text: str) -> List[LogEntry]:
        """Parses a raw log string."""
        return self.parse_lines(text.splitlines(keepends=True))

    def parse_lines(self, lines: List[str]) -> List[LogEntry]:
        """Parses a list of lines with support for multi-line stack traces."""
        self.entries = []
        current_entry: Optional[LogEntry] = None

        for line_idx, line in enumerate(lines, start=1):
            stripped = line.strip()
            if not stripped:
                continue

            ts, level, comp, msg = self._extract_log_line_parts(stripped)

            # Check if this line is indented continuation (stack trace, details)
            is_indented = line.startswith((" ", "\t"))

            # Determine if this line starts a new log entry
            is_new_entry = False
            if current_entry is None:
                is_new_entry = True
            elif is_indented:
                is_new_entry = False
            elif ts is not None:
                is_new_entry = True
            elif comp and comp != "System" and line.startswith(f"[{comp}]"):
                is_new_entry = True
            else:
                is_new_entry = False

            if is_new_entry:
                if current_entry is not None:
                    self.entries.append(current_entry)

                current_entry = LogEntry(
                    line_number=line_idx,
                    raw_text=stripped,
                    timestamp=ts,
                    level=level.upper() if level else "INFO",
                    component=comp or "General",
                    message=msg or stripped
                )
            else:
                # Append multi-line traceback or details to current entry
                if current_entry.details:
                    current_entry.details += "\n" + stripped
                else:
                    current_entry.details = stripped
                current_entry.raw_text += "\n" + stripped

        if current_entry is not None:
            self.entries.append(current_entry)

        return self.entries

    def _extract_log_line_parts(self, line: str) -> Tuple[Optional[str], Optional[str], Optional[str], Optional[str]]:
        """Extracts timestamp, log level, component name, and message body."""
        timestamp: Optional[str] = None
        for regex in self._compiled_ts_regexes:
            m = regex.search(line)
            if m:
                timestamp = m.group(1)
                break

        # Extract log level
        level_match = LEVEL_PATTERN.search(line)
        level = "INFO"
        if level_match:
            raw_lvl = level_match.group(1).upper()
            if raw_lvl in ("FATAL", "CRITICAL", "SEVERE"):
                level = "CRITICAL"
            elif raw_lvl in ("WARN", "WARNING"):
                level = "WARN"
            elif raw_lvl == "ERROR":
                level = "ERROR"
            elif raw_lvl == "DEBUG":
                level = "DEBUG"
            else:
                level = "INFO"

        # Extract component
        component = "System"
        comp_match = COMPONENT_PATTERN.search(line)
        if comp_match:
            component = comp_match.group(1) or comp_match.group(2)

        # Message is the line after cleaning timestamp and component if possible
        msg = line
        if timestamp:
            msg = msg.replace(timestamp, "", 1).strip()
        if comp_match:
            msg = msg.replace(comp_match.group(0), "", 1).strip()
        # Clean leading delimiters like "-", ":", "|"
        msg = re.sub(r"^[\s\-:|\[\]]+", "", msg).strip()

        return timestamp, level, component, msg

    def filter_entries(
        self,
        search_query: str = "",
        is_regex: bool = False,
        case_sensitive: bool = False,
        levels: Optional[List[str]] = None,
        component: Optional[str] = None,
    ) -> List[LogEntry]:
        """Filters entries according to search query, levels, and component."""
        results = self.entries

        # Filter by severity levels
        if levels:
            allowed_levels = {lvl.upper() for lvl in levels}
            results = [e for e in results if e.level in allowed_levels]

        # Filter by component
        if component and component != "All":
            results = [e for e in results if e.component == component]

        # Search query
        if search_query:
            if is_regex:
                try:
                    flags = 0 if case_sensitive else re.IGNORECASE
                    pattern = re.compile(search_query, flags)
                    results = [
                        e for e in results
                        if pattern.search(e.message) or pattern.search(e.raw_text) or pattern.search(e.details)
                    ]
                except re.error:
                    pass  # Return results as-is on invalid regex
            else:
                q = search_query if case_sensitive else search_query.lower()
                results = [
                    e for e in results
                    if (q in (e.message if case_sensitive else e.message.lower()))
                    or (q in (e.raw_text if case_sensitive else e.raw_text.lower()))
                ]

        return results

    def get_components(self) -> List[str]:
        """Returns sorted list of all unique component names."""
        comps = {e.component for e in self.entries if e.component}
        return ["All"] + sorted(comps)

    def get_summary_stats(self) -> Dict[str, int]:
        """Returns counts by log level and total count."""
        stats = {
            "TOTAL": len(self.entries),
            "CRITICAL": 0,
            "ERROR": 0,
            "WARN": 0,
            "INFO": 0,
            "DEBUG": 0,
        }
        for e in self.entries:
            lvl = e.level.upper()
            if lvl in stats:
                stats[lvl] += 1
            else:
                stats["INFO"] += 1
        return stats

