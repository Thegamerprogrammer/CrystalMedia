#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
CrystalMedia Downloader – Stable Production Release v3.1.9
==========================================================
Cross-platform media downloader for YouTube & Spotify.
YouTube: works like a beast
Spotify: fallback mode available (metadata + yt-dlp search pipeline)
Author: Thegamerprogrammer
License: MIT
"""
# ──────────────────────────────────────────────
# Built-in modules only — no external imports yet
# ──────────────────────────────────────────────
import sys
import os
import subprocess
import time
import random
import platform
import re
import shutil
from pathlib import Path
import zipfile
import tarfile
import urllib.request
import html
import json
from datetime import datetime
from importlib.metadata import version as pkg_version, PackageNotFoundError


APP_ROOT = Path("CrystalMedia")
LOG_ROOT = APP_ROOT / "logs"
DOWNLOADS_ROOT = APP_ROOT / "downloads"
RUNTIME_LOG = LOG_ROOT / "log.txt"
CRASH_LOG = LOG_ROOT / "crash.txt"
DEPS_LOG = LOG_ROOT / "deps.txt"


def _ensure_app_layout():
    APP_ROOT.mkdir(exist_ok=True)
    LOG_ROOT.mkdir(parents=True, exist_ok=True)
    DOWNLOADS_ROOT.mkdir(parents=True, exist_ok=True)


def _append_file(path: Path, line: str):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as f:
        f.write(line + "\n")


def log_runtime(msg: str):
    _append_file(RUNTIME_LOG, f"[{datetime.now().isoformat(timespec='seconds')}] {msg}")


def log_crash(msg: str):
    _append_file(CRASH_LOG, f"[{datetime.now().isoformat(timespec='seconds')}] {msg}")


def check_log_rotation(max_mb: int = 500):
    if not RUNTIME_LOG.exists():
        return
    size_mb = RUNTIME_LOG.stat().st_size / (1024 * 1024)
    if size_mb <= max_mb:
        return
    print(f"\n[Warning] {RUNTIME_LOG} is {size_mb:.1f} MB (limit {max_mb} MB).")
    ans = input("Keep existing log file? [Y/n]: ").strip().lower()
    if ans in ("n", "no"):
        RUNTIME_LOG.unlink(missing_ok=True)
        log_runtime("Rotated runtime log after user confirmation.")


def print_dependency_notice():
    print("CrystalMedia requires the following dependencies to work:")
    print(" - Deno / Node.js: JavaScript challenge runtime for yt-dlp signature solving.")
    print(" - yt-dlp: media extraction/download engine.")
    print(" - ffmpeg: remuxing and MP3 extraction.")
    print(" - spotdl: legacy Spotify fallback path.")
    print(" - rich + pyfiglet: terminal UI and splash rendering.")
    print("Windows PATH note: Scripts folder like %APPDATA%\Python\PythonXY\Scripts.")
    print("Linux/macOS PATH counterpart: ~/.local/bin and shell profile export PATH updates.")




def _fetch_pypi_version(package_name: str):
    url = f"https://pypi.org/pypi/{package_name}/json"
    try:
        with urllib.request.urlopen(url, timeout=10) as resp:
            payload = json.loads(resp.read().decode("utf-8", errors="ignore"))
        return payload.get("info", {}).get("version")
    except Exception:
        return None


def _installed_python_package_version(package_name: str):
    try:
        return pkg_version(package_name)
    except PackageNotFoundError:
        return None
    except Exception:
        return None


def preflight_sync_python_tools():
    """Check PyPI and proactively upgrade key Python tools before healing starts."""
    package_map = {
        "yt-dlp": "yt-dlp[default,curl-cffi]",
        "spotdl": "spotdl",
        "rich": "rich",
        "pyfiglet": "pyfiglet",
    }
    print("\nCrystalMedia PyPI preflight: checking latest package versions...")
    for pkg_name, pip_target in package_map.items():
        installed = _installed_python_package_version(pkg_name)
        latest = _fetch_pypi_version(pkg_name)
        if latest is None:
            print(f" - {pkg_name}: could not query PyPI; attempting upgrade anyway.")
            subprocess.call([sys.executable, "-m", "pip", "install", "--upgrade", pip_target], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            continue

        if installed != latest:
            print(f" - {pkg_name}: {installed or 'not installed'} -> {latest}; upgrading...")
            subprocess.call([sys.executable, "-m", "pip", "install", "--upgrade", pip_target], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        else:
            print(f" - {pkg_name}: already latest ({latest}).")

_ensure_app_layout()
check_log_rotation()
preflight_sync_python_tools()
print_dependency_notice()
log_runtime("Startup: dependency preflight shown.")

# ──────────────────────────────────────────────
# ANSI stripper for yt-dlp colored progress strings
# ──────────────────────────────────────────────
def strip_ansi(text: str) -> str:
    ansi_escape = re.compile(r'\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])')
    return ansi_escape.sub('', text)

# ──────────────────────────────────────────────
# Self-healing dependency block — runs first
# ──────────────────────────────────────────────
def command_exists(cmd: str) -> bool:
    return shutil.which(cmd) is not None


def ask_add_to_path(path_value: str, reason: str):
    print(f"\nAdd to PATH for {reason}?\n  {path_value}")
    ans = input("Add now? [Y/n]: ").strip().lower()
    if ans in ('', 'y', 'yes'):
        os.environ["PATH"] += os.pathsep + path_value
        log_runtime(f"PATH updated: {path_value}")
        return True
    log_runtime(f"PATH unchanged (user declined): {path_value}")
    return False

def ask_install(what: str) -> bool:
    print(f"\nCrystalMedia needs {what} to not be a broken toy.")
    ans = input("Install now? [Y/n]: ").strip().lower()
    return ans in ('', 'y', 'yes')

def run_quiet(cmd_list):
    try:
        subprocess.check_call(cmd_list, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        return True
    except:
        return False


def run_shell_quiet(cmd: str):
    try:
        subprocess.check_call(cmd, shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        return True
    except:
        return False


def detect_linux_distro() -> str:
    if platform.system() != "Linux":
        return ""
    os_release = Path("/etc/os-release")
    if not os_release.exists():
        return ""
    data = os_release.read_text(encoding="utf-8", errors="ignore").lower()
    for key in ["ubuntu", "debian", "fedora", "rhel", "centos", "arch", "manjaro", "opensuse", "suse", "alpine"]:
        if key in data:
            return key
    return "linux"


def install_node_runtime_os_aware() -> bool:
    """Install Node.js only with platform-appropriate installers."""
    system = platform.system()
    if system == "Windows":
        if command_exists("winget"):
            return run_quiet(["winget", "install", "OpenJS.NodeJS.LTS", "--silent"])
        if command_exists("choco"):
            return run_quiet(["choco", "install", "nodejs-lts", "-y"])
        return False
    if system == "Darwin":
        if command_exists("brew"):
            return run_quiet(["brew", "install", "node"])
        return False

    distro = detect_linux_distro()
    if command_exists("apt-get"):
        return run_shell_quiet("sudo apt-get update && sudo apt-get install -y nodejs npm")
    if command_exists("dnf"):
        return run_shell_quiet("sudo dnf install -y nodejs npm")
    if command_exists("yum"):
        return run_shell_quiet("sudo yum install -y nodejs npm")
    if command_exists("pacman"):
        return run_shell_quiet("sudo pacman -Sy --noconfirm nodejs npm")
    if command_exists("zypper"):
        return run_shell_quiet("sudo zypper --non-interactive install nodejs npm")
    if command_exists("apk"):
        return run_shell_quiet("sudo apk add --no-cache nodejs npm")
    log_runtime(f"No supported package manager for Node.js install on distro={distro}")
    return False

print("CrystalMedia performing dependency health check...")
log_runtime("Dependency health check started.")

# Windows: dynamic user Scripts PATH
if platform.system() == "Windows":
    try:
        import site
        user_base = site.getusersitepackages()
        user_scripts = Path(user_base).parent.parent / "Scripts"
        user_scripts_str = str(user_scripts)
    except Exception:
        py_ver = f"Python{sys.version_info.major}{sys.version_info.minor}"
        user_scripts_str = os.path.expanduser(rf"~\AppData\Roaming\Python\{py_ver}\Scripts")

    if user_scripts_str not in os.environ["PATH"]:
        ask_add_to_path(user_scripts_str, "Windows Python user scripts")

# Unix/macOS/Linux: add ~/.local/bin if missing
elif platform.system() in ("Linux", "Darwin"):
    local_bin = os.path.expanduser("~/.local/bin")
    if local_bin not in os.environ.get("PATH", "").split(os.pathsep):
        ask_add_to_path(local_bin, "Unix/macOS local user binaries")

# Deno
if not command_exists("deno"):
    print("Deno missing — auto-installing...")
    if platform.system() == "Windows":
        run_quiet(["powershell", "-Command", "irm https://deno.land/install.ps1 | iex"])
    else:
        run_shell_quiet("curl -fsSL https://deno.land/install.sh | sh")
    if not command_exists("deno"):
        print("Deno install failed. Go to https://deno.com manually.")

# Always try to upgrade Deno when available
if command_exists("deno"):
    run_quiet(["deno", "upgrade"])

# Node.js (alternate JS runtime for yt-dlp challenge solving)
if not (command_exists("node") or command_exists("nodejs")):
    print("Node.js missing — auto-installing with OS-aware package manager...")
    ok = install_node_runtime_os_aware()
    if not ok:
        print("Node.js install helper could not complete automatically.")
        print("Install manually: https://nodejs.org/en/download")

# Node.js (alternate JS runtime for yt-dlp challenge solving)
if not (command_exists("node") or command_exists("nodejs")):
    if ask_install("Node.js (fallback JavaScript runtime for yt-dlp)"):
        print("Installing Node.js with OS-aware package manager...")
        ok = install_node_runtime_os_aware()
        if not ok:
            print("Node.js install helper could not complete automatically.")
            print("Install manually: https://nodejs.org/en/download")

# yt-dlp
if not command_exists("yt-dlp"):
    if ask_install("yt-dlp"):
        print("Installing yt-dlp...")
        run_quiet([sys.executable, "-m", "pip", "install", "--upgrade", "--force-reinstall", "yt-dlp[default,curl-cffi]"])

# spotdl
if not command_exists("spotdl"):
    if ask_install("spotdl"):
        print("Installing spotdl...")
        run_quiet([sys.executable, "-m", "pip", "install", "--upgrade", "spotdl"])



def available_js_runtimes():
    runtimes = []
    if command_exists("deno"):
        runtimes.append("deno")
    if command_exists("node"):
        runtimes.append("node")
    elif command_exists("nodejs"):
        runtimes.append("nodejs")
    return runtimes


def refresh_js_runtimes():
    """Attempt lightweight runtime update/health checks for yt-dlp JS challenges."""
    if command_exists("deno"):
        run_quiet(["deno", "upgrade"])
    if command_exists("node"):
        run_quiet(["node", "--version"])
    elif command_exists("nodejs"):
        run_quiet(["nodejs", "--version"])

# rich + pyfiglet
for pkg in ["rich", "pyfiglet"]:
    try:
        __import__(pkg.replace("-", "_"))
    except ImportError:
        if ask_install(pkg):
            print(f"Installing {pkg}...")
            run_quiet([sys.executable, "-m", "pip", "install", "--upgrade", pkg])

print("Dependency health check completed. Importing libraries...\n")
_append_file(DEPS_LOG, f"[{datetime.now().isoformat(timespec='seconds')}] deno={command_exists('deno')} node={command_exists('node') or command_exists('nodejs')} yt-dlp={command_exists('yt-dlp')} ffmpeg={command_exists('ffmpeg')} spotdl={command_exists('spotdl')}")
log_runtime("Dependency health check completed.")

# ──────────────────────────────────────────────
# NOW import external libraries
# ──────────────────────────────────────────────
from rich.console import Console
from rich.panel import Panel
from rich.text import Text
from rich.live import Live
from rich.layout import Layout
from rich.progress import Progress, SpinnerColumn, BarColumn, TextColumn
from rich.spinner import Spinner
from pyfiglet import Figlet
import yt_dlp
from yt_dlp import YoutubeDL
from spotdl import Spotdl

console = Console()

# ──────────────────────────────────────────────
# Pastel blue theme constants — defined early
# ──────────────────────────────────────────────
COL_TITLE = "bold #A5D8FF"
COL_ACC = "bold #B3E0FF"
COL_WARN = "bold #FFE066"
COL_ERR = "bold #FF9999"
COL_GOOD = "bold #B2F2BB"
COL_MENU = "bold #D6E4FF"

# ──────────────────────────────────────────────
# List imported libraries with style
# ──────────────────────────────────────────────
console.print("\n[bold cyan]Libraries loaded after healing:[/bold cyan]")
libs = [
    ("rich", "console, panel, text, live, layout, progress"),
    ("pyfiglet", "ascii art"),
    ("yt_dlp", "YouTube downloader"),
    ("spotdl", "Spotify downloader"),
]
for name, desc in libs:
    console.print(f" • [bold green]{name}[/bold green] → {desc}")

console.print("")
refresh_js_runtimes()

# ──────────────────────────────────────────────
# Clean Rich Live countdown INSIDE the yellow panel
# ──────────────────────────────────────────────
def pause_for_reading(message: str = "Continuing in", seconds: int = 15):
    """Live countdown inside the yellow Panel — press any key to skip."""
    with Live(console=console, refresh_per_second=4, transient=True) as live:
        remaining = seconds
        while remaining > 0:
            content = Text.assemble(
                (f"{message} {remaining}...\n", COL_ACC),
                ("Press Enter or any key to continue", "italic dim")
            )
            live.update(
                Panel(
                    content,
                    title="Timeout",
                    border_style=COL_WARN,
                    padding=(0, 1),
                )
            )
            # Cross-platform any-key detection
            if platform.system() == "Windows":
                import msvcrt
                if msvcrt.kbhit():
                    msvcrt.getch()
                    break
            else:
                import select
                try:
                    if select.select([sys.stdin], [], [], 0.1)[0]:
                        sys.stdin.read(1)
                        break
                except Exception:
                    pass
            time.sleep(1)
            remaining -= 1

# 5-second countdown after import list
pause_for_reading("Imports complete", 5)

# ──────────────────────────────────────────────
# Download FFmpeg directly from gyan.dev if missing
# ──────────────────────────────────────────────
def download_ffmpeg():
    ffmpeg_dir = APP_ROOT / "ffmpeg"
    bin_dir = ffmpeg_dir / "bin"
    bin_dir.mkdir(parents=True, exist_ok=True)
    if command_exists("ffmpeg"):
        console.print(Text("FFmpeg already found in PATH — skipping.", style=COL_GOOD))
        return

    console.print(Text("FFmpeg missing — preparing architecture-aware download...", style=COL_WARN))
    system = platform.system()
    machine = platform.machine().lower()
    archive_path = None

    try:
        if system == "Windows":
            if machine not in ("amd64", "x86_64"):
                raise RuntimeError(f"Unsupported Windows architecture for bundled FFmpeg: {machine}")
            url = "https://www.gyan.dev/ffmpeg/builds/ffmpeg-release-essentials.zip"
            archive_path = Path("ffmpeg.zip")
        elif system == "Linux":
            if machine not in ("amd64", "x86_64"):
                raise RuntimeError(f"Unsupported Linux architecture for bundled FFmpeg: {machine}")
            url = "https://www.gyan.dev/ffmpeg/builds/ffmpeg-release-amd64-static.tar.xz"
            archive_path = Path("ffmpeg.tar.xz")
        elif system == "Darwin":
            # gyan.dev is Windows-centric; avoid downloading wrong binaries on macOS/ARM.
            raise RuntimeError("Automatic FFmpeg download is disabled on macOS. Please install via Homebrew: brew install ffmpeg")
        else:
            raise RuntimeError(f"Unsupported OS for auto-download: {system}")

        console.print(f"[cyan]Downloading {url.split('/')[-1]}...[/cyan]")
        urllib.request.urlretrieve(url, archive_path)
        console.print("[cyan]Extracting binaries...[/cyan]")

        if system == "Windows":
            with zipfile.ZipFile(archive_path, 'r') as zip_ref:
                for file in zip_ref.namelist():
                    if file.endswith(("ffmpeg.exe", "ffprobe.exe")):
                        zip_ref.extract(file, bin_dir)
                        extracted = bin_dir / file
                        if extracted.parent != bin_dir:
                            shutil.move(extracted, bin_dir / extracted.name)
        else:
            with tarfile.open(archive_path, "r:xz") as tar:
                for member in tar.getmembers():
                    if member.name.endswith(("ffmpeg", "ffprobe")):
                        tar.extract(member, bin_dir)
                        extracted = bin_dir / member.name
                        if extracted.parent != bin_dir:
                            shutil.move(extracted, bin_dir / extracted.name.split('/')[-1])

        archive_path.unlink(missing_ok=True)
        console.print(Text(f"FFmpeg binaries downloaded to {bin_dir}", style=COL_GOOD))
        ask_add_to_path(str(bin_dir.absolute()), "FFmpeg binaries")
    except Exception as e:
        if archive_path is not None:
            archive_path.unlink(missing_ok=True)
        console.print(Text(f"FFmpeg download failed: {str(e)}", style=COL_ERR))
        console.print(Text("Install manually (Linux/macOS: package manager, Windows: gyan.dev).", style=COL_WARN))

# Check & download FFmpeg if needed
if not command_exists("ffmpeg"):
    if ask_install("FFmpeg (direct from gyan.dev)"):
        download_ffmpeg()
    else:
        console.print(Text("FFmpeg skipped — audio/merging may break.", style=COL_WARN))

# ──────────────────────────────────────────────
# Splash variants
# ──────────────────────────────────────────────
def display_full_splash():
    clear_screen()
    figlet = Figlet(font='slant')
    art = figlet.renderText('CrystalMedia')
    console.print(Text(art, style=COL_TITLE))
    console.print(Text("v3.1.9", style=COL_ACC))
    console.print("-" * 60)

def display_clean_splash():
    clear_screen()
    figlet = Figlet(font='slant')
    art = figlet.renderText('CrystalMedia')
    console.print(Text(art, style=COL_TITLE))
    console.print(Text("v3.1.9", style=COL_ACC))
    console.print("-" * 60)

def clear_screen():
    os.system('cls' if os.name == 'nt' else 'clear')

# ──────────────────────────────────────────────
# Directory structure
# ──────────────────────────────────────────────
def create_folders():
    base = DOWNLOADS_ROOT
    base.mkdir(exist_ok=True)
    for category in ["YT VIDEO", "YT MUSIC", "SPOTIFY"]:
        for subcategory in ["Single", "Playlist"]:
            (base / category / subcategory).mkdir(parents=True, exist_ok=True)
    console.print(Text("Output directories initialised.", style=COL_GOOD))
    pause_for_reading("Directories ready", 2)

create_folders()

# ──────────────────────────────────────────────
# Fixed Progress Logger with Layout
# ──────────────────────────────────────────────

class ContinuePromptTooltip:
    """Animated continue prompt rendered inside a tooltip panel."""
    def __init__(self, message: str = "Download success", border_style: str = COL_WARN):
        self.message = message
        self.border_style = border_style
        self.frames = ["⠋", "⠙", "⠹", "⠸", "⠼", "⠴", "⠦", "⠧", "⠇", "⠏"]

    def render(self, remaining: int, frame_idx: int) -> Panel:
        prompt = Text.assemble(
            (f"{self.frames[frame_idx]} {self.message} {remaining}...\n", COL_ACC),
            ("Press Enter or any key to continue", "italic dim")
        )
        return Panel(prompt, title="Timeout", border_style=self.border_style, title_align="left", padding=(0, 1))

class FixedProgressLogger:
    """Fixed progress bar + scrolling log panel using Rich Layout"""
    def __init__(self, console_obj, header_text: Text):
        self.console = console_obj
        self.logs = []
        self.layout = Layout()
        self.layout.split_column(
            Layout(name="header", size=10),
            Layout(name="progress", size=6),
            Layout(name="logs", size=10)
        )
        self.layout["header"].update(
            Panel(header_text, border_style=COL_MENU, title="CrystalMedia", title_align="left")
        )
        self.progress = Progress(
            SpinnerColumn(style=COL_MENU),
            TextColumn("[progress.description]{task.description}", style=COL_MENU),
            BarColumn(complete_style=COL_MENU, finished_style=COL_MENU, pulse_style=COL_MENU),
            TextColumn("[progress.percentage]{task.percentage:>3.0f}%", style=COL_MENU),
            console=self.console
        )
        self.task = None
        self.live = Live(self.layout, console=self.console, refresh_per_second=4, vertical_overflow="crop", screen=True)
        self.max_logs = 8
        self.max_log_width = 110
        self.layout["progress"].update(self._waiting_panel())
        self.continue_tooltip = ContinuePromptTooltip()

    def _waiting_panel(self):
        """Render spinner placeholder until progress data arrives."""
        waiting_spinner = Spinner("dots", text=Text(" Waiting for download data...", style=COL_MENU), style=COL_MENU)
        return Panel(waiting_spinner, title="Progress", border_style=COL_MENU, title_align="left")

    def add_log(self, msg: str, level: str = "info"):
        """Add message to log panel with color coding"""
        msg = strip_ansi(msg).replace("\n", " ").strip()
        if len(msg) > self.max_log_width:
            msg = msg[:self.max_log_width - 1] + "…"

        if level == "error":
            styled_msg = f"[red]{msg}[/red]"
        elif level == "warning":
            styled_msg = f"[yellow]{msg}[/yellow]"
        elif level == "success":
            styled_msg = f"[green]{msg}[/green]"
        else:
            styled_msg = f"[{COL_MENU}]{msg}[/{COL_MENU}]"

        self.logs.append(Text.from_markup(styled_msg))
        log_runtime(f"[{level.upper()}] {msg}")
        if level in ("error", "warning"):
            log_crash(msg)
        if len(self.logs) > self.max_logs:
            self.logs = self.logs[-self.max_logs:]

        log_text = Text()
        for log_entry in self.logs:
            log_text.append(log_entry)
            log_text.append("\n")

        log_panel = Panel(
            log_text if self.logs else Text("Waiting for output...", style="dim"),
            title="Download Log",
            border_style=COL_MENU,
            title_align="left"
        )
        self.layout["logs"].update(log_panel)

    def update_progress(self, percent: float, description: str = "Downloading"):
        if self.task is None:
            self.task = self.progress.add_task(description, total=100)
        self.progress.update(self.task, completed=percent, description=description)
        self.layout["progress"].update(
            Panel(self.progress, title="Progress", border_style=COL_MENU, title_align="left")
        )

    def mark_complete(self, description: str = "Download complete!"):
        complete_text = Text(f"✓ {description}", style=COL_GOOD)
        self.layout["progress"].update(
            Panel(complete_text, title="Progress", border_style=COL_GOOD, title_align="left")
        )

    def wait_for_continue(self, message: str = "Download success", seconds: int = 30):
        return self._wait_for_continue_impl(message, seconds)

    def _wait_for_continue_impl(self, message: str = "Download success", seconds: int = 30):
        """Show timeout prompt inside progress panel to avoid layout gaps."""
        remaining = seconds
        frames = ["⠋", "⠙", "⠹", "⠸", "⠼", "⠴", "⠦", "⠧", "⠇", "⠏"]
        frame_idx = 0
        while remaining > 0:
            self.continue_tooltip.message = message
            self.layout["progress"].update(self.continue_tooltip.render(remaining, frame_idx))
            if platform.system() == "Windows":
                import msvcrt
                if msvcrt.kbhit():
                    msvcrt.getch()
                    break
            else:
                import select
                try:
                    if select.select([sys.stdin], [], [], 0.1)[0]:
                        sys.stdin.read(1)
                        break
                except Exception:
                    # Non-interactive stdin in some environments; just continue countdown
                    pass
            time.sleep(1)
            remaining -= 1
            frame_idx = (frame_idx + 1) % len(frames)

    def start(self):
        self.live.start()

    def stop(self):
        self.live.stop()


def show_inline_continue_prompt(progress_logger, message: str = "Download success", seconds: int = 30):
    """Compatibility wrapper so post-download prompt never crashes on missing method."""
    wait_fn = getattr(progress_logger, "wait_for_continue", None)
    if callable(wait_fn):
        wait_fn(message, seconds)
        return

    # Fallback path for stale runtime objects/classes.
    with Live(console=console, refresh_per_second=4, transient=True) as live:
        remaining = seconds
        frames = ["⠋", "⠙", "⠹", "⠸", "⠼", "⠴", "⠦", "⠧", "⠇", "⠏"]
        frame_idx = 0
        while remaining > 0:
            content = Text.assemble(
                (f"{frames[frame_idx]} {message} {remaining}...\n", COL_ACC),
                ("Press Enter or any key to continue", "italic dim")
            )
            live.update(Panel(content, title="Timeout", border_style=COL_WARN, padding=(0, 1)))
            if platform.system() == "Windows":
                import msvcrt
                if msvcrt.kbhit():
                    msvcrt.getch()
                    break
            else:
                import select
                try:
                    if select.select([sys.stdin], [], [], 0.1)[0]:
                        sys.stdin.read(1)
                        break
                except Exception:
                    pass
            time.sleep(1)
            remaining -= 1
            frame_idx = (frame_idx + 1) % len(frames)


def build_download_header(title: str, mode: str, content_type: str, target_dir: Path) -> Text:
    figlet = Figlet(font='slant')
    art = figlet.renderText('CrystalMedia')
    return Text.assemble(
        (art, COL_TITLE),
        ("v3.1.9\n", COL_ACC),
        (("-" * 60) + "\n", COL_MENU),
        (f"Downloading: {title}\n", COL_ACC),
        (f"Initiating {mode} {content_type.upper()} download → {target_dir}", COL_MENU),
    )

# ──────────────────────────────────────────────
# YouTube download logic (native API + title display + improved logger)
# ──────────────────────────────────────────────
USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Edg/131.0.0.0",
]

def get_ydl_options(is_playlist: bool, content_type: str) -> dict:
    subfolder = "Playlist" if is_playlist else "Single"
    base_path = (
        str(DOWNLOADS_ROOT / ("YT VIDEO" if content_type == "video" else "YT MUSIC") / subfolder / "%(playlist_title)s" / "%(title)s.%(ext)s")
        if is_playlist else
        str(DOWNLOADS_ROOT / ("YT VIDEO" if content_type == "video" else "YT MUSIC") / subfolder / "%(title)s.%(ext)s")
    )
    options = {
        "outtmpl": base_path,
        "quiet": True,
        "no_warnings": False,
        "noprogress": True,
        "retries": 20,
        "fragment_retries": 10,
        "keep_fragments": True,
        "no_clean_infojson": True,
        "concurrent_fragments": 1,
        "http_headers": {"User-Agent": random.choice(USER_AGENTS)},
        "remux_video": "mp4",
        "format_sort": ["ext:mp4:m4a"],
        "js_runtimes": available_js_runtimes(),
    }
    if is_playlist:
        options.update({"sleep_requests": 2, "sleep_interval": 5, "max_sleep_interval": 15})
    else:
        options.update({"sleep_requests": 1, "sleep_interval": 3, "max_sleep_interval": 10})
    if content_type == "video":
        options["format"] = select_mp4_quality()
        options["postprocessors"] = [{"key": "FFmpegVideoConvertor", "preferedformat": "mp4"}]
    else:
        options["format"] = "bestaudio/best"
        bitrate = select_mp3_bitrate()
        options["postprocessors"] = [{"key": "FFmpegExtractAudio", "preferredcodec": "mp3", "preferredquality": bitrate}]
    return options

def select_mp3_bitrate() -> str:
    console.print(Text("MP3 Bitrate Selection", style=COL_TITLE))
    console.print(Text(" 1. Low (96 kbps)", style=COL_MENU))
    console.print(Text(" 2. Medium (128 kbps)", style=COL_MENU))
    console.print(Text(" 3. Standard (192 kbps) [default]", style=COL_MENU))
    console.print(Text(" 4. High (256 kbps)", style=COL_MENU))
    console.print(Text(" 5. Insane (320 kbps)", style=COL_MENU))
    choice = console.input(Text("→ ", style=COL_ACC)).strip() or "3"
    return {"1": "96", "2": "128", "3": "192", "4": "256", "5": "320"}.get(choice, "192")

def select_mp4_quality() -> str:
    console.print(Text("MP4 Quality Selection", style=COL_TITLE))
    console.print(Text(" 1. Low (~360p)", style=COL_MENU))
    console.print(Text(" 2. Medium (~480p–720p)", style=COL_MENU))
    console.print(Text(" 3. High (~720p–1080p)", style=COL_MENU))
    console.print(Text(" 4. Best (highest available) [default]", style=COL_MENU))
    choice = console.input(Text("→ ", style=COL_ACC)).strip() or "4"
    if choice == "1": return "bestvideo[height<=?360][ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]"
    if choice == "2": return "bestvideo[height<=?720][ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]"
    if choice == "3": return "bestvideo[height<=?1080][ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]"
    return "bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best"



def select_js_runtime_preference() -> str:
    console.print(Text("JavaScript Runtime Preference", style=COL_TITLE))
    console.print(Text(" 1. Auto fallback (recommended)", style=COL_MENU))
    console.print(Text(" 2. Prefer Deno first", style=COL_MENU))
    console.print(Text(" 3. Prefer Node first", style=COL_MENU))
    choice = console.input(Text("→ ", style=COL_ACC)).strip() or "1"
    return {"1": "auto", "2": "deno", "3": "node"}.get(choice, "auto")


def build_js_runtime_profiles(preference: str):
    installed = available_js_runtimes()
    if not installed:
        return [[]]
    deno_first = [["deno"], ["node"], ["nodejs"], ["deno", "node"], ["node", "deno"]]
    node_first = [["node"], ["nodejs"], ["deno"], ["node", "deno"], ["deno", "node"]]
    auto_order = [["node"], ["nodejs"], ["deno"], ["node", "deno"], ["deno", "node"]]
    source = auto_order if preference == "auto" else (deno_first if preference == "deno" else node_first)

    profiles = []
    for profile in source:
        filtered = [r for r in profile if r in installed]
        if filtered and filtered not in profiles:
            profiles.append(filtered)
    return profiles or [installed]

def download_youtube(url: str, content_type: str, is_playlist: bool) -> None:
    try:
        with YoutubeDL({"quiet": True}) as ydl:
            info = ydl.extract_info(url, download=False)
            title = info.get('title', 'Unknown')
            if is_playlist:
                title = info.get('playlist_title', title) or title
        console.print(Text("Downloading: ", style=COL_ACC), end="")
        console.print(Text(title, style="bold yellow"))
    except:
        console.print(Text("Could not extract title — downloading anyway...", style=COL_WARN))

    subfolder = "Playlist" if is_playlist else "Single"
    target_dir = DOWNLOADS_ROOT / ("YT VIDEO" if content_type == "video" else "YT MUSIC") / subfolder
    target_dir.mkdir(parents=True, exist_ok=True)

    mode = "Playlist" if is_playlist else "Single Item"

    options = get_ydl_options(is_playlist, content_type)

    # Initialize fixed progress logger
    progress_header = build_download_header(title if "title" in locals() else "Unknown", mode, content_type, target_dir)
    progress_logger = FixedProgressLogger(console, progress_header)
    progress_logger.start()
    progress_logger.add_log(f"Starting {mode} {content_type.upper()} download", "info")

    class FixedYellowLogger:
        def __init__(self, logger):
            self.logger = logger

        def _handle_message(self, msg: str, level: str = "info"):
            clean_msg = strip_ansi(msg)
            lower_msg = clean_msg.lower()

            if 'already been downloaded' in lower_msg:
                self.logger.add_log(clean_msg, "success")
                self.logger.mark_complete("Download complete (already exists)!")
                return

            if '[merger]' in lower_msg or 'merging formats into' in lower_msg:
                self.logger.update_progress(100, "Merging")

            if 'download complete' in lower_msg and 'processing' in lower_msg:
                self.logger.update_progress(100, "Processing")

            if 'ETA' in clean_msg or '%' in clean_msg:
                return

            if any(x in clean_msg for x in ['[youtube]', '[download]', '[info]', '[Merger]']) or '[merger]' in lower_msg:
                self.logger.add_log(clean_msg, level)

        def debug(self, msg):
            self._handle_message(msg, "info")

        def info(self, msg):
            self._handle_message(msg, "info")

        def warning(self, msg):
            self._handle_message(msg, "warning")

        def error(self, msg):
            self._handle_message(msg, "error")

    options["logger"] = FixedYellowLogger(progress_logger)

    def progress_hook(d):
        if d['status'] == 'downloading':
            raw_percent = d.get('_percent_str', '0%')
            clean_percent = strip_ansi(raw_percent).strip('%')
            try:
                percent = float(clean_percent)
                progress_logger.update_progress(percent, "Downloading")
            except ValueError:
                pass
        elif d['status'] == 'finished':
            progress_logger.add_log("Download complete. Processing...", "success")
            progress_logger.update_progress(100, "Processing")

    options["progress_hooks"] = [progress_hook]

    retry_count = 0
    max_retries = 30
    final_path = None
    download_completed = False

    runtime_preference = select_js_runtime_preference()
    runtime_profiles = build_js_runtime_profiles(runtime_preference)

    for runtime_try, runtime_list in enumerate(runtime_profiles, start=1):
        runtime_value = ",".join(runtime_list)
        options["js_runtimes"] = runtime_list
        progress_logger.add_log(f"JS runtime try {runtime_try}/{len(runtime_profiles)} → {runtime_value}", "info")
        console.print(Text(f"Trying JS runtime profile: {runtime_value}", style=COL_ACC))

        while retry_count < max_retries:
            try:
                with YoutubeDL(options) as downloader:
                    final_info = downloader.extract_info(url, download=True)

                if isinstance(final_info, dict):
                    requested = final_info.get("requested_downloads") or []
                    if requested and isinstance(requested[0], dict):
                        final_path = requested[0].get("filepath")
                    if not final_path:
                        final_path = final_info.get("_filename")
                download_completed = True
                break
            except KeyboardInterrupt:
                progress_logger.stop()
                raise
            except Exception as e:
                err_text = str(e)
                retry_count += 1
                progress_logger.add_log(f"Attempt {retry_count}/{max_retries} failed: {err_text[:80]}", "warning")
                if any(keyword in err_text.lower() for keyword in ["rate limit", "throttl", "429", "443"]):
                    options["http_headers"]["User-Agent"] = random.choice(USER_AGENTS)
                    progress_logger.add_log("Rate limit detected. Rotating user-agent...", "warning")
                if any(k in err_text.lower() for k in ["jsc", "challenge", "signature", "deno", "node"]):
                    progress_logger.add_log(f"Runtime {runtime_value} failed; falling back to next runtime profile.", "warning")
                    console.print(Text(f"Runtime {runtime_value} failed; falling back to next runtime profile.", style=COL_WARN))
                    break
                time.sleep(random.uniform(4, 10))

        if download_completed:
            break

    if not download_completed:
        progress_logger.stop()
        console.print(Text("All selected JS runtimes failed. Switching to fallback Z (noisy yt-dlp output)...", style=COL_WARN))
        noisy_options = dict(options)
        noisy_options["quiet"] = False
        noisy_options["noprogress"] = False
        noisy_options["no_warnings"] = False
        noisy_options.pop("logger", None)
        noisy_options.pop("progress_hooks", None)
        try:
            with YoutubeDL(noisy_options) as noisy_downloader:
                final_info = noisy_downloader.extract_info(url, download=True)
            if isinstance(final_info, dict):
                requested = final_info.get("requested_downloads") or []
                if requested and isinstance(requested[0], dict):
                    final_path = requested[0].get("filepath")
                if not final_path:
                    final_path = final_info.get("_filename")
            download_completed = True
        except Exception as e:
            console.print(Text(f"Noisy fallback failed: {str(e)}", style=COL_ERR))

    if download_completed:
        progress_logger.mark_complete("Download complete!")
        if final_path:
            progress_logger.add_log(f"✓ Final file: {final_path}", "success")
        progress_logger.add_log(f"✓ Download complete → {target_dir}", "success")
        progress_logger.wait_for_continue("Download success", 30)
        progress_logger.stop()
        if final_path:
            console.print(Text(f"Final file saved at: {final_path}", style=COL_GOOD))
        else:
            console.print(Text(f"Download complete → {target_dir}", style=COL_GOOD))
        return

    progress_logger.add_log("Maximum retries reached", "error")
    progress_logger.stop()
    console.print(Text("Maximum retries reached. Check connection or try again later.", style=COL_ERR))
    pause_for_reading("Max retries — review above", 15)

def _spotify_oembed_query(url: str) -> str:
    req = urllib.request.Request(f"https://open.spotify.com/oembed?url={url}", headers={"User-Agent": random.choice(USER_AGENTS)})
    with urllib.request.urlopen(req, timeout=20) as resp:
        payload = json.loads(resp.read().decode("utf-8", errors="ignore"))
    title = payload.get("title", "")
    author = payload.get("author_name", "")
    query = f"{title} {author}".strip()
    return query


def _spotify_page_queries(url: str, max_tracks: int = 30):
    req = urllib.request.Request(url, headers={"User-Agent": random.choice(USER_AGENTS)})
    with urllib.request.urlopen(req, timeout=25) as resp:
        page = resp.read().decode("utf-8", errors="ignore")

    queries = []

    # Strategy 1 (more stable): parse /track/<id> links and resolve via oEmbed.
    track_ids = []
    for tid in re.findall(r'/track/([A-Za-z0-9]{22})', page):
        if tid not in track_ids:
            track_ids.append(tid)
        if len(track_ids) >= max_tracks:
            break

    for tid in track_ids:
        try:
            q = _spotify_oembed_query(f"https://open.spotify.com/track/{tid}")
            if q:
                queries.append(q)
        except Exception:
            continue
        if len(queries) >= max_tracks:
            break

    if queries:
        return queries

    # Strategy 2 (fallback): row/label HTML parsing (brittle, but sometimes useful).
    rows = re.findall(r'data-testid="track-row".*?(?=data-testid="track-row"|</body>)', page, flags=re.S)
    for row in rows:
        title_match = re.search(r'data-encore-id="listRowTitle"[^>]*>\s*<span[^>]*>(.*?)</span>', row, flags=re.S)
        artist_match = re.search(r'data-encore-id="text">(.*?)</span>', row, flags=re.S)
        if not title_match:
            continue
        title = html.unescape(re.sub(r'<[^>]+>', '', title_match.group(1))).strip()
        artist = html.unescape(re.sub(r'<[^>]+>', '', artist_match.group(1))).strip() if artist_match else ""
        if not title:
            continue
        queries.append(f"{title} {artist}".strip())
        if len(queries) >= max_tracks:
            break
    return queries


def _download_spotify_queries_with_ytdlp(queries, target_dir: Path, progress_logger: FixedProgressLogger):
    target_dir.mkdir(parents=True, exist_ok=True)

    class SpotifyYTDLPLogger:
        def __init__(self, logger):
            self.logger = logger
        def debug(self, msg):
            clean = strip_ansi(str(msg))
            if '[youtube]' in clean and 'WARNING:' not in clean:
                self.logger.add_log(clean, 'info')
        def info(self, msg):
            clean = strip_ansi(str(msg))
            if clean:
                self.logger.add_log(clean, 'info')
        def warning(self, msg):
            self.logger.add_log(strip_ansi(str(msg)), 'warning')
        def error(self, msg):
            self.logger.add_log(strip_ansi(str(msg)), 'error')

    ydl_opts = {
        "quiet": True,
        "no_warnings": True,
        "noprogress": True,
        "format": "bestaudio/best",
        "outtmpl": str(target_dir / "%(title)s.%(ext)s"),
        "postprocessors": [{"key": "FFmpegExtractAudio", "preferredcodec": "mp3", "preferredquality": "192"}],
        "http_headers": {"User-Agent": random.choice(USER_AGENTS)},
        "logger": SpotifyYTDLPLogger(progress_logger),
    }

    count = 0
    total = max(len(queries), 1)
    with YoutubeDL(ydl_opts) as ydl:
        for idx, query in enumerate(queries, start=1):
            progress_logger.add_log(f"[{idx}/{len(queries)}] Spotify fallback search: {query}", "info")
            progress_logger.update_progress(((idx - 1) / total) * 100, "Searching & downloading")
            ydl.download([f"ytsearch1:{query}"])
            count += 1
            progress_logger.update_progress((idx / total) * 100, "Searching & downloading")

    return count


def download_spotify(url: str, is_playlist: bool) -> None:
    subfolder = "Playlist" if is_playlist else "Single"
    target_dir = DOWNLOADS_ROOT / "SPOTIFY" / subfolder
    target_dir.mkdir(parents=True, exist_ok=True)

    mode = "Playlist" if is_playlist else "Single Item"
    progress_header = build_download_header("Spotify fallback", mode, "audio", target_dir)
    progress_logger = FixedProgressLogger(console, progress_header)
    progress_logger.start()
    progress_logger.add_log("Spotify downloader (no-premium fallback mode)", "info")

    queries = []
    try:
        if is_playlist or "/playlist/" in url or "/album/" in url:
            queries = _spotify_page_queries(url)
        else:
            q = _spotify_oembed_query(url)
            if q:
                queries = [q]
    except Exception as e:
        progress_logger.add_log(f"Metadata parsing fallback triggered: {str(e)[:120]}", "warning")

    if queries:
        try:
            downloaded = _download_spotify_queries_with_ytdlp(queries, target_dir, progress_logger)
            progress_logger.mark_complete(f"Downloaded {downloaded} track(s)!")
            progress_logger.add_log(f"✓ Downloaded {downloaded} track(s) → {target_dir}", "success")
            progress_logger.wait_for_continue("Spotify download success", 30)
            progress_logger.stop()
            console.print(Text(f"Downloaded {downloaded} track(s) → {target_dir}", style=COL_GOOD))
            return
        except Exception as e:
            progress_logger.add_log(f"yt-dlp Spotify fallback failed: {str(e)}", "error")

    progress_logger.add_log("Trying spotdl legacy mode as last fallback...", "warning")
    try:
        spotdl_client = Spotdl()
        songs = spotdl_client.search([url])
        results = spotdl_client.download_songs(songs)
        progress_logger.mark_complete(f"Downloaded {len(results)} track(s)!")
        progress_logger.add_log(f"✓ Downloaded {len(results)} track(s) → {target_dir}", "success")
        progress_logger.wait_for_continue("Spotify download success", 30)
        progress_logger.stop()
        console.print(Text(f"Downloaded {len(results)} track(s) → {target_dir}", style=COL_GOOD))
    except Exception as e:
        progress_logger.stop()
        console.print(Text(f"Spotify download failed: {str(e)}", style=COL_ERR))
        log_crash(f"Spotify download failed: {str(e)}")
        pause_for_reading("Error — copy the message above", 15)


# ──────────────────────────────────────────────
# Cross-platform arrow-key menu navigation
# ──────────────────────────────────────────────
def read_key():
    """Cross-platform arrow key / Enter detection."""
    if platform.system() == "Windows":
        import msvcrt
        k = msvcrt.getch()
        if k == b'\xe0':
            k2 = msvcrt.getch()
            if k2 == b'H': return "UP"
            if k2 == b'P': return "DOWN"
        elif k == b'\r':
            return "ENTER"
        elif k == b'\x03':
            raise KeyboardInterrupt
        return None
    else:
        import tty, termios, select
        if not sys.stdin.isatty():
            return None
        fd = sys.stdin.fileno()
        old = termios.tcgetattr(fd)
        try:
            tty.setraw(fd)
            rlist, _, _ = select.select([sys.stdin], [], [], 0.1)
            if rlist:
                ch = sys.stdin.read(1)
                if ch == "\x1b":
                    ch2 = sys.stdin.read(1)
                    ch3 = sys.stdin.read(1)
                    seq = ch + ch2 + ch3
                    if seq == "\x1b[A": return "UP"
                    if seq == "\x1b[B": return "DOWN"
                if ch in ("\r", "\n"): return "ENTER"
                if ch == "\x03": raise KeyboardInterrupt
            return None
        finally:
            termios.tcsetattr(fd, termios.TCSADRAIN, old)

# ──────────────────────────────────────────────
# Primary application loop
# ──────────────────────────────────────────────
def main_loop():
    categories = ["YouTube Video (MP4)", "YouTube Music (MP3)", "Spotify", "Exit"]
    selected_index = 0

    # FIX: Clear any leftover keypresses from the library countdown
    # so they don't accidentally skip the Spotify warning pause
    if platform.system() == "Windows":
        import msvcrt
        while msvcrt.kbhit():
            msvcrt.getch()  # drain any pending keys
    else:
        import select
        if sys.stdin.isatty():
            while select.select([sys.stdin], [], [], 0)[0]:
                sys.stdin.read(1)

    # Now safe to show the splash (Spotify warning won't be skipped)
    display_full_splash()

    while True:
        display_clean_splash()

        console.print(Text("Main Category Selection", style=COL_TITLE))
        for i, category in enumerate(categories):
            prefix = "→ " if i == selected_index else " "
            style = COL_ACC if i == selected_index else "white"
            console.print(Text(prefix + category, style=style))
        console.print(Text("\n↑ ↓ to navigate • Enter to select • Ctrl+C to quit", style=COL_ACC))

        try:
            key = read_key()
            if key == "UP":
                selected_index = (selected_index - 1) % len(categories)
            elif key == "DOWN":
                selected_index = (selected_index + 1) % len(categories)
            elif key == "ENTER":
                if selected_index == 3:
                    console.print(Text("Thank you for using CrystalMedia. Exiting.", style=COL_GOOD))
                    pause_for_reading("Shutting down", 15)
                    sys.exit(0)
                category_choice = str(selected_index + 1)

                display_clean_splash()
                console.print(Text("Mode Selection", style=COL_TITLE))
                console.print(Text(" 1. Single Item", style=COL_MENU))
                console.print(Text(" 2. Playlist", style=COL_MENU))
                mode_input = console.input(Text("→ ", style=COL_ACC)).strip()
                is_playlist = mode_input == "2"

                display_clean_splash()
                url_input = console.input(Text("Resource URL → ", style=COL_ACC)).strip()

                display_clean_splash()

                if category_choice == "1":
                    download_youtube(url_input, "video", is_playlist)
                elif category_choice == "2":
                    download_youtube(url_input, "audio", is_playlist)
                elif category_choice == "3":
                    download_spotify(url_input, is_playlist)

                console.input(Text("\nPress Enter to continue...", style=COL_ACC))

        except KeyboardInterrupt:
            console.print()
            console.print(Text("Keyboard interrupt detected. Returning to main menu.", style=COL_WARN))
            pause_for_reading("Interrupt acknowledged", 15)
        except Exception as e:
            console.print(Panel(
                Text(f"Unexpected error: {str(e)}", style="bold red"),
                title="Error",
                border_style="red"
            ))
            log_crash(f"Unexpected error: {str(e)}")
            pause_for_reading("Error — copy the message above", 15)
            console.print(Text("Recovery in progress — returning to main menu.", style=COL_WARN))
            pause_for_reading("Resuming", 15)

if __name__ == "__main__":
    main_loop()
