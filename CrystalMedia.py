#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
CrystalMedia v4 GUI Launcher
============================
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
        "--version",
        action="store_true",
        help="Print version and exit.",
    )
    parser.add_argument(
        "--diagnostics",
        action="store_true",
        help="Print runtime diagnostics and exit.",
    )
    return parser


def _print_diagnostics() -> None:
    ctx = _context()
    pywebview_installed = importlib.util.find_spec("webview") is not None
    scripts_on_path = shutil.which("crystalmedia") is not None

    print("CrystalMedia diagnostics")
    print("-----------------------")
    print(f"Version:   v{__version__}")
    print(f"Python:    {ctx.python}")
    print(f"Platform:  {ctx.platform}")
    print(f"Executable:{ctx.executable}")
    print(f"pywebview: {'yes' if pywebview_installed else 'no'}")
    print(f"CLI path:  {'yes' if scripts_on_path else 'no'}")


def _launch_gui() -> int:
    try:
        from crystalmedia.gui import launch_gui
    except Exception as exc:  # noqa: BLE001 - launcher boundary
        print("Failed to import GUI runtime (crystalmedia.gui).")
        print(f"Reason: {exc}")
        print("Try: pip install --upgrade crystalmedia pywebview")
        return 1

    try:
        launch_gui()
        return 0
    except Exception as exc:  # noqa: BLE001 - launcher boundary
        print("Failed to launch CrystalMedia GUI.")
        print(f"Reason: {exc}")
        print("If running headless/remotely, try legacy terminal placeholder:")
        print("  python CrystalMedia.py --terminal")
        return 1


def _launch_terminal() -> int:
    try:
        from crystalmedia.cli import terminal_main
    except Exception as exc:  # noqa: BLE001
        print("Failed to import legacy terminal entrypoint.")
        print(f"Reason: {exc}")
        return 1

    try:
        terminal_main()
        return 0
    except Exception as exc:  # noqa: BLE001
        print("Legacy terminal entrypoint failed.")
        print(f"Reason: {exc}")
        return 1


def main_loop() -> None:
    """Backwards-compat alias expected by older imports."""
    raise SystemExit(_launch_gui())


def main(argv: list[str] | None = None) -> int:
    args = _build_parser().parse_args(argv)

    if args.version:
        print(f"CrystalMedia v{__version__}")
        return 0

    if args.diagnostics:
        _print_diagnostics()
        return 0

    if args.terminal:
        return _launch_terminal()

    return _launch_gui()


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
