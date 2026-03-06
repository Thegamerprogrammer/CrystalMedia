#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""CrystalMedia v4 launcher (GUI-first)."""

from __future__ import annotations

import sys

__version__ = "4.0.0"


def _help() -> None:
    print("CrystalMedia launcher flags:")
    print("  --version       Print version and exit")
    print("  --diagnostics   Print runtime diagnostics and exit")
    print("  --terminal      Run legacy terminal placeholder mode")
    print("Default behavior launches GUI mode.")


def main(argv: list[str] | None = None) -> int:
    argv = list(argv or [])
    if any(a in ("-h", "--help") for a in argv):
        _help()
        return 0
    if "--version" in argv:
        print(f"CrystalMedia v{__version__}")
        return 0

    from crystalmedia import cli

    if "--diagnostics" in argv:
        from crystalmedia.gui import GuiBackend
        b = GuiBackend()
        print(b.get_status())
        return 0

    if "--terminal" in argv:
        cli.terminal_main()
        return 0

    cli.main()
    return 0


def main_loop() -> None:
    raise SystemExit(main())


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
