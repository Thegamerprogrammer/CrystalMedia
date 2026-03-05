#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
CrystalMedia v4 GUI Launcher
Stable top-level launcher for CrystalMedia.
- Default: launches the PyWebView HTML GUI.
- Optional: `--terminal` invokes legacy terminal entrypoint.
- Safe diagnostics: clear messages for missing package/runtime issues.
"""

from __future__ import annotations

import argparse
import importlib.util
import platform
import shutil
import sys
from dataclasses import dataclass


__version__ = "4.0.0"


@dataclass
class LaunchContext:
    python: str
    platform: str
    executable: str


def _context() -> LaunchContext:
    return LaunchContext(
        python=sys.version.split()[0],
        platform=f"{platform.system()} {platform.release()}",
        executable=sys.executable,
    )


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="CrystalMedia.py",
        description="Launch CrystalMedia glass GUI (default) or legacy terminal mode.",
    )
    parser.add_argument(
        "--terminal",
        action="store_true",
        help="Run legacy terminal mode (same as crystalmedia-terminal).",
    )
    parser.add_argument(
    )
    parser.add_argument(
        "--terminal",
        action="store_true",
        help="Run legacy terminal mode (same as crystalmedia-terminal).",
    )
    parser.add_argument(
        "--version",
        action="store_true",
        help="Print version and exit.",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    args = _build_parser().parse_args(argv)

    if args.version:
        print(f"CrystalMedia v{__version__}")
        return 0

    if args.terminal:
        try:
            from crystalmedia.cli import terminal_main
        except Exception as e:
            print(f"Failed to load legacy terminal mode: {e}")
            return 1
        terminal_main()
        return 0

    launch_gui()
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
