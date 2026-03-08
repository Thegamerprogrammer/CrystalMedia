"""CrystalMedia package."""

from __future__ import annotations

import traceback
from datetime import datetime
from pathlib import Path

__all__ = ["run"]


def _write_bootstrap_crash_log(message: str):
    log_dir = Path("CrystalMedia") / "logs"
    log_dir.mkdir(parents=True, exist_ok=True)
    crash_log = log_dir / "crash.txt"
    with crash_log.open("a", encoding="utf-8") as fh:
        fh.write(f"[{datetime.now().isoformat(timespec='seconds')}] {message}\n")


def run():
    try:
        from CrystalMedia import main_loop
        main_loop()
    except Exception as exc:
        _write_bootstrap_crash_log(f"Bootstrap fatal error: {exc}")
        _write_bootstrap_crash_log(traceback.format_exc())
        raise
