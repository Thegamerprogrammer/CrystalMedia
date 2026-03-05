"""CrystalMedia package."""

__all__ = ["run", "run_gui", "run_terminal"]


def run():
    """Default package run: GUI mode."""
    from .gui import launch_gui
    launch_gui()


def run_gui():
    from .gui import launch_gui
    launch_gui()


def run_terminal():
    from .cli import terminal_main
    terminal_main()
