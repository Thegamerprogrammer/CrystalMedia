"""Entry points for CrystalMedia commands."""


def main():
    """Default command: launch the PyWebView HTML GUI."""
    from .gui import launch_gui
    launch_gui()


def terminal_main():
    """Legacy terminal mode."""
    from CrystalMedia import main_loop
    main_loop()
