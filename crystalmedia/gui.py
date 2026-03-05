"""PyWebView-based glassmorphism control panel for CrystalMedia."""

from __future__ import annotations

import json
import subprocess
import sys
import threading
from datetime import datetime
from pathlib import Path
from typing import List


class GuiBackend:
    def __init__(self) -> None:
        self._logs: List[str] = []
        self._lock = threading.Lock()

    def _log(self, msg: str) -> None:
        line = f"[{datetime.now().strftime('%H:%M:%S')}] {msg}"
        with self._lock:
            self._logs.append(line)
            self._logs = self._logs[-800:]

    def get_logs(self) -> str:
        with self._lock:
            return "\n".join(self._logs)

    def get_status(self) -> str:
        return json.dumps({
            "python": sys.version.split()[0],
            "cwd": str(Path.cwd()),
        })

    def auto_install_dependencies(self) -> str:
        """Install or update core Python dependencies and stream logs."""
        targets = [
            "yt-dlp[default,curl-cffi]",
            "spotdl",
            "rich",
            "pyfiglet",
            "pywebview",
        ]
        self._log("Auto-install requested from GUI.")
        for target in targets:
            self._log(f"Installing/upgrading: {target}")
            cmd = [sys.executable, "-m", "pip", "install", "--upgrade", target]
            try:
                proc = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
                for line in (proc.stdout or "").splitlines():
                    if line.strip():
                        self._log(line.strip())
                if proc.returncode == 0:
                    self._log(f"OK: {target}")
                else:
                    self._log(f"FAILED ({proc.returncode}): {target}")
            except Exception as e:
                self._log(f"ERROR installing {target}: {e}")
        self._log("Auto-install flow finished.")
        return "done"

    def launch_cli_background(self) -> str:
        """Run the existing terminal CLI in the background and stream output."""

        def _runner() -> None:
            self._log("Starting CrystalMedia CLI in background...")
            cmd = [sys.executable, "-m", "crystalmedia"]
            try:
                proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
                assert proc.stdout is not None
                for line in proc.stdout:
                    if line.strip():
                        self._log(line.rstrip())
                code = proc.wait()
                self._log(f"Background CLI exited with code {code}")
            except Exception as e:
                self._log(f"Failed to start background CLI: {e}")

        threading.Thread(target=_runner, daemon=True).start()
        return "started"


def launch_gui() -> None:
    import webview

    html_path = Path(__file__).parent / "webui" / "glass-terminal.html"
    backend = GuiBackend()
    backend._log("CrystalMedia GUI ready.")

    webview.create_window(
        "CrystalMedia v4 · Glass Control Center",
        url=html_path.resolve().as_uri(),
        js_api=backend,
        width=1400,
        height=900,
    )
    webview.start(debug=False)


if __name__ == "__main__":
    launch_gui()
