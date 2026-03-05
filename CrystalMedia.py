#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
CrystalMedia v4 GUI Launcher
============================
Primary entrypoint for CrystalMedia now targets the PyWebView glass GUI.
Legacy terminal mode is exposed via `crystalmedia-terminal`.
"""

from __future__ import annotations

import argparse
import sys

from crystalmedia.gui import launch_gui


__version__ = "4.0.0"


def main_loop() -> None:
    """Backwards-compatible alias for old callers expecting main_loop."""
    launch_gui()


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="CrystalMedia.py",
        description="Launch CrystalMedia glass GUI (default).",
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
