"""Entry points for CrystalMedia commands."""


def main():
    """Default command: launch the PyWebView HTML GUI."""
    from .gui import launch_gui
    launch_gui()


def terminal_main():
    """Legacy terminal mode placeholder (GUI is now primary)."""
    print("Legacy terminal mode has been retired in v4 GUI-first build.")
    print("Use the HTML GUI: crystalmedia  (or crystalmedia-gui)")
