"""
PH-Lending Pro — Persistent Logger
Logs all errors, warnings and events to a rotating file that survives restarts.
Log file location: ~/Library/Application Support/PH-Lending/logs/app.log
"""

import os
import sys
import logging
import traceback
import threading
from logging.handlers import RotatingFileHandler
from datetime import datetime

# ── Paths ──────────────────────────────────────────────────────────────────────
if sys.platform == "win32":
    # Windows: C:\Users\<User>\AppData\Roaming\PH-Lending
    _base = os.environ.get("APPDATA", os.path.expanduser("~"))
    APP_SUPPORT_DIR = os.path.join(_base, "PH-Lending")
elif sys.platform == "darwin":
    # macOS: ~/Library/Application Support/PH-Lending
    APP_SUPPORT_DIR = os.path.expanduser("~/Library/Application Support/PH-Lending")
else:
    # Linux / autres : ~/.local/share/PH-Lending
    APP_SUPPORT_DIR = os.path.expanduser("~/.local/share/PH-Lending")

LOG_DIR = os.path.join(APP_SUPPORT_DIR, "logs")
LOG_FILE = os.path.join(LOG_DIR, "app.log")

# ── Setup ──────────────────────────────────────────────────────────────────────
os.makedirs(LOG_DIR, exist_ok=True)

# Create the main logger
_logger = logging.getLogger("PH-Lending")
_logger.setLevel(logging.DEBUG)

# Formatter with rich context
_formatter = logging.Formatter(
    fmt="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)

# Rotating file handler: 5 MB max, keep 5 old files → ~25 MB max total
_file_handler = RotatingFileHandler(
    LOG_FILE,
    maxBytes=5 * 1024 * 1024,  # 5 MB
    backupCount=5,
    encoding="utf-8"
)
_file_handler.setLevel(logging.DEBUG)
_file_handler.setFormatter(_formatter)
_logger.addHandler(_file_handler)

# Also mirror to console during development
_console_handler = logging.StreamHandler(sys.stdout)
_console_handler.setLevel(logging.INFO)
_console_handler.setFormatter(_formatter)
_logger.addHandler(_console_handler)

# ── Public helpers ──────────────────────────────────────────────────────────────

def info(msg: str, *args, **kwargs):
    _logger.info(msg, *args, **kwargs)

def warning(msg: str, *args, **kwargs):
    _logger.warning(msg, *args, **kwargs)

def error(msg: str, *args, exc_info=False, **kwargs):
    _logger.error(msg, *args, exc_info=exc_info, **kwargs)

def critical(msg: str, *args, **kwargs):
    _logger.critical(msg, *args, **kwargs)

def debug(msg: str, *args, **kwargs):
    _logger.debug(msg, *args, **kwargs)

def log_exception(context: str, exc: Exception):
    """Log a full exception with traceback and context."""
    tb = traceback.format_exc()
    _logger.error(
        "EXCEPTION in [%s]: %s\n%s",
        context, str(exc), tb
    )

def log_api_call(method_name: str, args_summary: str = ""):
    """Log an API method call (debug level — not written unless DEBUG is enabled)."""
    _logger.debug("API call: %s(%s)", method_name, args_summary)

def log_startup():
    """Log application startup."""
    _logger.info("=" * 70)
    _logger.info("PH-Lending Pro STARTED — %s", datetime.now().strftime("%A %d %B %Y à %H:%M:%S"))
    _logger.info("Log file: %s", LOG_FILE)
    _logger.info("Python: %s", sys.version.split()[0])
    _logger.info("=" * 70)

def log_shutdown():
    """Log application shutdown."""
    _logger.info("PH-Lending Pro SHUTDOWN — %s", datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
    _logger.info("-" * 70)

# ── Global exception hook ───────────────────────────────────────────────────────

def _global_exception_handler(exc_type, exc_value, exc_tb):
    """Catch any unhandled exception and write it to the log before crashing."""
    if issubclass(exc_type, KeyboardInterrupt):
        sys.__excepthook__(exc_type, exc_value, exc_tb)
        return
    _logger.critical(
        "UNHANDLED EXCEPTION:\n%s",
        "".join(traceback.format_exception(exc_type, exc_value, exc_tb))
    )

sys.excepthook = _global_exception_handler

# ── Thread exception hook (Python 3.8+) ────────────────────────────────────────

def _thread_exception_handler(args):
    """Catch unhandled exceptions in threads."""
    _logger.critical(
        "UNHANDLED THREAD EXCEPTION (thread=%s):\n%s",
        args.thread.name if args.thread else "unknown",
        "".join(traceback.format_exception(args.exc_type, args.exc_value, args.exc_tb))
    )

threading.excepthook = _thread_exception_handler


# ── Read logs API for the frontend ─────────────────────────────────────────────

def get_log_entries(limit: int = 200, level_filter: str = "ALL") -> list:
    """
    Read the log file and return structured entries for the frontend.
    Returns a list of dicts: {timestamp, level, message, raw}
    """
    entries = []
    allowed_levels = {"DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"}

    try:
        if not os.path.exists(LOG_FILE):
            return []

        with open(LOG_FILE, "r", encoding="utf-8", errors="replace") as f:
            lines = f.readlines()

        # Parse each line
        current_entry = None
        for line in lines:
            line = line.rstrip("\n")
            # Lines starting with a timestamp are new entries
            if len(line) >= 19 and line[4] == "-" and line[7] == "-" and line[10] == " ":
                if current_entry:
                    entries.append(current_entry)
                parts = line.split(" | ", 3)
                if len(parts) >= 3:
                    level = parts[1].strip()
                    current_entry = {
                        "timestamp": parts[0].strip(),
                        "level": level,
                        "source": parts[2].strip() if len(parts) > 2 else "",
                        "message": parts[3].strip() if len(parts) > 3 else "",
                        "raw": line
                    }
                else:
                    current_entry = {
                        "timestamp": "",
                        "level": "INFO",
                        "source": "",
                        "message": line,
                        "raw": line
                    }
            else:
                # Continuation line (e.g. traceback lines)
                if current_entry:
                    current_entry["message"] += "\n" + line
                    current_entry["raw"] += "\n" + line

        if current_entry:
            entries.append(current_entry)

        # Apply level filter
        if level_filter != "ALL" and level_filter in allowed_levels:
            entries = [e for e in entries if e["level"].strip() == level_filter]

        # Return the most recent entries (last N)
        return entries[-limit:][::-1]  # Most recent first

    except Exception as e:
        return [{"timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                 "level": "ERROR",
                 "source": "logger",
                 "message": f"Could not read log file: {e}",
                 "raw": ""}]


def get_log_stats() -> dict:
    """Return statistics about the log file."""
    try:
        if not os.path.exists(LOG_FILE):
            return {"exists": False, "size_kb": 0, "total_lines": 0, "errors": 0, "warnings": 0}

        size = os.path.getsize(LOG_FILE)
        error_count = 0
        warning_count = 0
        total_lines = 0

        with open(LOG_FILE, "r", encoding="utf-8", errors="replace") as f:
            for line in f:
                total_lines += 1
                if " | ERROR    |" in line or " | CRITICAL |" in line:
                    error_count += 1
                elif " | WARNING  |" in line:
                    warning_count += 1

        return {
            "exists": True,
            "path": LOG_FILE,
            "size_kb": round(size / 1024, 1),
            "total_lines": total_lines,
            "errors": error_count,
            "warnings": warning_count,
            "log_dir": LOG_DIR
        }
    except Exception as e:
        return {"exists": False, "error": str(e)}


def clear_logs() -> bool:
    """Clear the current log file (does not clear rotated .log.1 etc.)."""
    try:
        with open(LOG_FILE, "w", encoding="utf-8") as f:
            f.write("")
        _logger.info("Log file cleared by user.")
        return True
    except Exception:
        return False
