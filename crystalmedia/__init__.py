"""CrystalMedia package."""

__all__ = ["run", "run_gui"]


def run():
    from CrystalMedia import main_loop
    main_loop()


def run_gui():
    from .gui import launch_gui
    launch_gui()
