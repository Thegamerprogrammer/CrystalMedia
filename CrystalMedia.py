
"""
CrystalMedia Downloader – Stable Production Release v4
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
import urllib.request
import urllib.parse
import html
import json
import csv
import webbrowser
import traceback
from datetime import datetime


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


def install_exportify_vendor_requirements():
    """Deprecated no-op for backwards compatibility (runtime installs removed)."""
    return


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
    print(r"Windows PATH note: Scripts folder like %APPDATA%\Python\PythonXY\Scripts.")
    print("Linux/macOS PATH counterpart: ~/.local/bin and shell profile export PATH updates.")




def _runtime_dependency_snapshot():
    """Print a simple dependency snapshot without network calls or runtime installs."""
    print("\nCrystalMedia dependency snapshot:")
    bins = {
        "deno": command_exists("deno"),
        "node/nodejs": command_exists("node") or command_exists("nodejs"),
        "yt-dlp": command_exists("yt-dlp"),
        "ffmpeg": command_exists("ffmpeg"),
        "spotdl": command_exists("spotdl"),
    }
    for name, ok in bins.items():
        status = "found" if ok else "missing"
        print(f" - {name}: {status}")


_ensure_app_layout()
check_log_rotation()
install_exportify_vendor_requirements()
print_dependency_notice()
log_runtime("Startup: dependency notice shown.")

# ──────────────────────────────────────────────
# ANSI stripper for yt-dlp colored progress strings
# ──────────────────────────────────────────────
def strip_ansi(text: str) -> str:
    ansi_escape = re.compile(r'\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])')
    return ansi_escape.sub('', text)


def should_suppress_ytdlp_log(msg: str) -> bool:
    """Hide repetitive yt-dlp authentication/cookie hints from the compact log panel."""
    clean = strip_ansi(str(msg)).lower()
    noisy_fragments = (
        "age-restricted; some formats may be missing without authentication",
        "--cookies-from-browser or --cookies",
        "wiki/faq#how-do-i-pass-cookies-to-yt-dlp",
        "wiki/extractors#exporting-youtube-cookies",
    )
    return any(fragment in clean for fragment in noisy_fragments)


def command_exists(cmd: str) -> bool:
    return shutil.which(cmd) is not None


print("CrystalMedia performing dependency health check...")
log_runtime("Dependency health check started.")
_runtime_dependency_snapshot()

if not command_exists("deno"):
    print("Deno missing. Install manually if yt-dlp JS challenges fail: https://deno.com")

if not (command_exists("node") or command_exists("nodejs")):
    print("Node.js missing. Install manually for best yt-dlp runtime fallback: https://nodejs.org/en/download")

if not command_exists("yt-dlp"):
    print("yt-dlp missing. Install it with: pip install yt-dlp[default,curl-cffi]")

if not command_exists("spotdl"):
    print("spotdl missing (legacy fallback). Install with: pip install spotdl")

if not command_exists("ffmpeg"):
    print("ffmpeg missing. Install via your OS package manager (or use Docker).")




def run_quiet(cmd_list):
    try:
        subprocess.check_call(cmd_list, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        return True
    except (subprocess.CalledProcessError, FileNotFoundError, OSError):
        return False


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
        print(f"Missing Python dependency: {pkg}. Install with: pip install {pkg}")

print("Dependency health check completed. Importing libraries...\n")
_append_file(DEPS_LOG, f"[{datetime.now().isoformat(timespec='seconds')}] deno={command_exists('deno')} node={command_exists('node') or command_exists('nodejs')} yt-dlp={command_exists('yt-dlp')} ffmpeg={command_exists('ffmpeg')} spotdl={command_exists('spotdl')} exportify_req={(Path('vendor') / 'exportify' / 'requirements.txt').exists()}")
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
from crystalmedia.extras import (
    StarfieldBackground,
    write_mp3_tags,
    iter_downloaded_entries,
    extract_entry_final_path,
)

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


STARFIELD = StarfieldBackground()  # auto-sizes from terminal when available
FIGLET = Figlet(font='slant')
FIGLET_ART_LINES = FIGLET.renderText('CrystalMedia').rstrip('\n').splitlines()


def _compose_splash_frame(body_lines: list[str] | None = None) -> Text:
    """Overlay splash title and optional body content onto the animated starfield canvas."""
    star_lines = STARFIELD.render().splitlines()
    width = max((len(line) for line in star_lines), default=80)
    if not star_lines:
        star_lines = [" " * width for _ in range(10)]

    canvas = [list(line.ljust(width)) for line in star_lines]

    start_row = max(0, min(2, len(canvas) - len(FIGLET_ART_LINES) - 3))
    for idx, line in enumerate(FIGLET_ART_LINES):
        row = start_row + idx
        if row >= len(canvas):
            break
        left = max(0, (width - len(line)) // 2)
        for col, ch in enumerate(line):
            c = left + col
            if c < width and ch != " ":
                canvas[row][c] = ch

    info_row = min(len(canvas) - 2, start_row + len(FIGLET_ART_LINES))
    for text in ("v4", "-" * min(width, 60)):
        left = max(0, (width - len(text)) // 2)
        if 0 <= info_row < len(canvas):
            for col, ch in enumerate(text):
                c = left + col
                if c < width:
                    canvas[info_row][c] = ch
        info_row += 1

    if body_lines:
        body_start = min(len(canvas) - 1, info_row)
        for idx, line in enumerate(body_lines):
            row = body_start + idx
            if row >= len(canvas):
                break
            text = line[: max(1, width - 4)]
            left = 2
            for col, ch in enumerate(text):
                c = left + col
                if c < width:
                    canvas[row][c] = ch

    return Text('\n'.join(''.join(row) for row in canvas), style='#A5D8FF')

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
                    title=Text("Continue", style=COL_MENU),
                    border_style=COL_MENU,
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

# Check FFmpeg availability (no runtime install/download)
if not command_exists("ffmpeg"):
    console.print(Text("FFmpeg missing — install it to enable audio extraction/remuxing.", style=COL_WARN))

# ──────────────────────────────────────────────
# Splash variants
# ──────────────────────────────────────────────
def display_full_splash():
    clear_screen()
    console.print(_compose_splash_frame())


def display_clean_splash():
    clear_screen()
    console.print(_compose_splash_frame())


def build_main_menu_frame(categories, selected_index) -> Text:
    """Build animated starfield + menu as a single frame renderable."""
    divider = "-" * 60
    menu_lines = [
        "Main Category Selection",
        *[("→ " if i == selected_index else "  ") + cat for i, cat in enumerate(categories)],
        "",
        "↑ ↓ to navigate • Enter to select • Ctrl+C to quit",
    ]
    return _compose_splash_frame([divider, *menu_lines])

def clear_screen():
    """Cross-platform screen clear for animated frames."""
    try:
        console.clear()
    except Exception:
        # ANSI fallback for environments where Rich clear is unavailable.
        sys.stdout.write("\033[2J\033[H")
        sys.stdout.flush()

# ──────────────────────────────────────────────
# Directory structure
# ──────────────────────────────────────────────
def create_folders():
    base = DOWNLOADS_ROOT
    base.mkdir(exist_ok=True)
    created_paths = []
    for category in ["YT VIDEO", "YT MUSIC", "SPOTIFY"]:
        for subcategory in ["Single", "Playlist"]:
            path = (base / category / subcategory)
            path.mkdir(parents=True, exist_ok=True)
            created_paths.append(path)
    console.print(Text("Output directories initialised.", style=COL_GOOD))
    console.print(Text(f"Base folder: {base.resolve()}", style=COL_MENU))
    for path in created_paths:
        console.print(Text(f" • {path.resolve()}", style=COL_MENU))
    pause_for_reading("Directories ready", 2)

create_folders()

# ──────────────────────────────────────────────
# Fixed Progress Logger with Layout
# ──────────────────────────────────────────────

class FixedProgressLogger:
    """Fixed progress bar + scrolling log panel using Rich Layout"""
    def __init__(self, console_obj, header_text: Text = None):
        self.console = console_obj
        self.logs = []
        self.layout = Layout()
        self.layout.split_column(
            Layout(name="progress", size=8),
            Layout(name="logs", size=16)
        )
        self.progress = Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
            console=self.console
        )
        self.task = None
        self.live = Live(self.layout, console=self.console, refresh_per_second=4)
        self.max_logs = 12
        self.max_log_width = 110
        self.layout["progress"].update(self._waiting_panel())
        self.started = False

    def _waiting_panel(self):
        """Render spinner placeholder until progress data arrives."""
        waiting_spinner = Spinner("dots", text=Text(" Waiting for download data...", style=COL_MENU), style=COL_MENU)
        return Panel(waiting_spinner, title=Text("Progress", style=COL_MENU), border_style=COL_MENU, title_align="left")

    def add_log(self, msg: str, level: str = "info"):
        """Add message to log panel with color coding"""
        msg = strip_ansi(msg).replace("\n", " ").strip()

        if level == "error":
            style = "red"
        elif level == "warning":
            style = "yellow"
        elif level == "success":
            style = "green"
        else:
            style = COL_MENU

        self.logs.append(Text(msg, style=style))
        log_runtime(f"[{level.upper()}] {msg}")
        if level in ("error", "warning"):
            log_crash(msg)
        if len(self.logs) > 15:
            self.logs = self.logs[-15:]

        log_text = Text()
        for log_entry in self.logs:
            log_text.append_text(log_entry)
            log_text.append("\n")

        log_panel = Panel(
            log_text if self.logs else Text("Waiting for output...", style="dim"),
            title=Text("Download Log", style=COL_MENU),
            border_style=COL_MENU,
            title_align="left"
        )
        self.layout["logs"].update(log_panel)

    def update_progress(self, percent: float, description: str = "Downloading"):
        """Update progress bar"""
        if self.task is None:
            self.task = self.progress.add_task(description, total=100)
        self.progress.update(self.task, completed=percent, description=description)

        self.layout["progress"].update(
            Panel(self.progress, title=Text("Progress", style=COL_MENU), border_style=COL_MENU, title_align="left")
        )

    def mark_complete(self, description: str = "Download complete!"):
        """Show a completed progress state even when file already exists."""
        if self.task is None:
            self.task = self.progress.add_task(description, total=100, completed=100)
        else:
            self.progress.update(self.task, completed=100, description=description)
        self.layout["progress"].update(
            Panel(self.progress, title=Text("Progress", style=COL_MENU), border_style=COL_MENU, title_align="left")
        )

    def start(self):
        if not self.started:
            self.live.start()
            self.started = True

    def stop(self):
        if self.started:
            self.live.stop()
            self.started = False

    def wait_for_continue(self, message: str = "Download success", seconds: int = 30):
        self.stop()
        pause_for_reading(message, seconds)


def build_download_header(title: str, mode: str, content_type: str, target_dir: Path) -> Text:
    figlet = Figlet(font='slant')
    art = figlet.renderText('CrystalMedia')
    return Text.assemble(
        (art, COL_TITLE),
        ("v4\n", COL_ACC),
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


def select_embed_extras() -> bool:
    console.print(Text("Embed extras (lyrics + art + subtitle fallback + metadata)", style=COL_TITLE))
    console.print(Text(" 1. Yes (recommended for MP3)", style=COL_MENU))
    console.print(Text(" 2. No", style=COL_MENU))
    choice = console.input(Text("→ ", style=COL_ACC)).strip() or "1"
    return choice == "1"



def is_age_restricted_error(msg: str) -> bool:
    clean = strip_ansi(str(msg)).lower()
    keys = (
        "age-restricted",
        "confirm your age",
        "sign in to confirm",
        "this video may be inappropriate",
        "login required",
    )
    return any(k in clean for k in keys)


def _cookie_browser_sources():
    """Generate yt-dlp cookiesfrombrowser tuples with likely browser/profile combos."""
    browsers = []
    try:
        controller = webbrowser.get()
        hint = f"{getattr(controller, 'name', '')} {controller}".lower()
        for b in ("chrome", "chromium", "edge", "firefox", "opera", "brave", "safari", "vivaldi"):
            if b in hint and b not in browsers:
                browsers.append(b)
    except Exception:
        pass

    system = platform.system()
    if system == "Windows":
        ordered = ["edge", "chrome", "firefox", "brave", "opera"]
        profiles = [None, "Default", "Profile 1", "Profile 2"]
    elif system == "Darwin":
        ordered = ["safari", "chrome", "firefox", "edge", "brave"]
        profiles = [None, "Default", "Profile 1"]
    else:
        ordered = ["chrome", "chromium", "firefox", "edge", "brave", "opera"]
        profiles = [None, "Default", "default"]

    for b in ordered:
        if b not in browsers:
            browsers.append(b)

    seen = set()
    for browser_name in browsers:
        for profile in profiles:
            source = (browser_name, None, profile, None)
            if source not in seen:
                seen.add(source)
                yield source


def _cookie_source_label(source):
    browser_name, _, profile, _ = source
    return f"{browser_name}{f':{profile}' if profile else ''}"


def try_ytdlp_with_browser_cookies(url_or_query: str, options: dict, progress_logger, extract_info_mode: bool = False):
    last_error = "No browser cookie source succeeded."
    for source in _cookie_browser_sources():
        cookie_opts = dict(options)
        cookie_opts["cookiesfrombrowser"] = source
        label = _cookie_source_label(source)
        progress_logger.add_log(f"Trying browser cookies fallback via: {label}", "warning")
        try:
            with YoutubeDL(cookie_opts) as browser_ydl:
                if extract_info_mode:
                    info = browser_ydl.extract_info(url_or_query, download=True)
                    return True, info, label
                browser_ydl.download([url_or_query])
                return True, None, label
        except Exception as e:
            last_error = str(e)

    # CLI fallback can work in environments where python-embedded cookie loading fails.
    for source in _cookie_browser_sources():
        label = _cookie_source_label(source)
        browser_name, _, profile, _ = source
        browser_arg = f"{browser_name}:{profile}" if profile else browser_name
        progress_logger.add_log(f"Trying yt-dlp CLI cookie fallback via: {label}", "warning")
        cmd = ["yt-dlp", "--cookies-from-browser", browser_arg, "--skip-download", "--simulate", url_or_query]
        try:
            subprocess.check_call(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            cookie_opts = dict(options)
            cookie_opts["cookiesfrombrowser"] = source
            with YoutubeDL(cookie_opts) as browser_ydl:
                if extract_info_mode:
                    info = browser_ydl.extract_info(url_or_query, download=True)
                    return True, info, label
                browser_ydl.download([url_or_query])
                return True, None, label
        except Exception as e:
            last_error = str(e)

    return False, None, last_error


def extract_final_path_from_info(final_info):
    final_path = None
    if isinstance(final_info, dict):
        requested = final_info.get("requested_downloads") or []
        if requested and isinstance(requested[0], dict):
            final_path = requested[0].get("filepath")
        if not final_path:
            final_path = final_info.get("_filename")
    return final_path



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
        return [None]
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


def to_js_runtime_option(runtime_list):
    """yt-dlp expects a dict mapping runtime->config for js_runtimes."""
    if not runtime_list:
        return None
    return {runtime: {} for runtime in runtime_list}

def download_youtube(url: str, content_type: str, is_playlist: bool, embed_extras: bool = False) -> None:
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
    console.print(Text(f"Initiating {mode} {content_type.upper()} download → {target_dir}", style=COL_ACC))

    options = get_ydl_options(is_playlist, content_type)

    runtime_preference = select_js_runtime_preference()

    # Initialize fixed progress logger
    progress_logger = FixedProgressLogger(console)
    progress_logger.start()
    progress_logger.add_log(f"Starting {mode} {content_type.upper()} download", "info")

    class FixedYellowLogger:
        def __init__(self, logger):
            self.logger = logger

        def _handle_message(self, msg: str, level: str = "info"):
            clean_msg = strip_ansi(msg)
            lower_msg = clean_msg.lower()

            if should_suppress_ytdlp_log(clean_msg):
                return

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
            if should_suppress_ytdlp_log(msg):
                return
            if any(x in msg for x in ['[youtube]', '[download]', '[info]', '[Merger]']):
                if 'ETA' in msg or '%' in msg:
                    return
                self.logger.add_log(strip_ansi(msg), "info")

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
    final_info = None
    final_path = None
    download_completed = False

    runtime_profiles = build_js_runtime_profiles(runtime_preference)

    for runtime_try, runtime_list in enumerate(runtime_profiles, start=1):
        runtime_value = ",".join(runtime_list) if runtime_list else "default"
        js_runtime_option = to_js_runtime_option(runtime_list)
        if js_runtime_option is None:
            options.pop("js_runtimes", None)
        else:
            options["js_runtimes"] = js_runtime_option
        progress_logger.add_log(f"JS runtime try {runtime_try}/{len(runtime_profiles)} → {runtime_value}", "info")
        console.print(Text(f"Trying JS runtime profile: {runtime_value}", style=COL_ACC))

        while retry_count < max_retries:
            try:
                with YoutubeDL(options) as downloader:
                    final_info = downloader.extract_info(url, download=True)

                final_path = extract_final_path_from_info(final_info)
                download_completed = True
                break
            except KeyboardInterrupt:
                progress_logger.stop()
                raise
            except Exception as e:
                err_text = str(e)
                retry_count += 1
                progress_logger.add_log(f"Attempt {retry_count}/{max_retries} failed: {err_text[:80]}", "warning")

                if is_age_restricted_error(err_text):
                    progress_logger.add_log("Age-restricted content detected. Attempting browser-cookies fallback.", "warning")
                    ok, info_with_cookies, browser_or_err = try_ytdlp_with_browser_cookies(url, options, progress_logger, extract_info_mode=True)
                    if ok:
                        final_info = info_with_cookies
                        final_path = extract_final_path_from_info(info_with_cookies)
                        progress_logger.add_log(f"Cookie fallback succeeded with browser: {browser_or_err}", "success")
                        download_completed = True
                        break
                    progress_logger.add_log(f"Cookie fallback failed: {browser_or_err[:120]}", "warning")

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
            final_path = extract_final_path_from_info(final_info)
            download_completed = True
        except Exception as e:
            console.print(Text(f"Noisy fallback failed: {str(e)}", style=COL_ERR))

    if download_completed:
        if content_type == "audio" and isinstance(final_info, dict):
            for entry in iter_downloaded_entries(final_info):
                mp3_path = extract_entry_final_path(entry)
                if not mp3_path:
                    continue
                try:
                    write_mp3_tags(mp3_path, entry, embed_extras=embed_extras, user_agents=USER_AGENTS, log=progress_logger.add_log)
                except Exception as e:
                    progress_logger.add_log(f"Metadata/lyrics embed failed for {mp3_path.name}: {str(e)[:120]}", "warning")
        progress_logger.mark_complete("Download complete!")
        if final_path:
            progress_logger.add_log(f"✓ Final file: {final_path}", "success")
        progress_logger.add_log(f"✓ Download complete → {target_dir}", "success")
        progress_logger.wait_for_continue("Download success", 30)
        if final_path:
            console.print(Text(f"Final file saved at: {final_path}", style=COL_GOOD))
        else:
            console.print(Text(f"Download complete → {target_dir}", style=COL_GOOD))
        pause_for_reading("Download success — review above", 30)
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


def _playlist_name_from_url(url: str) -> str:
    m = re.search(r"/playlist/([A-Za-z0-9]+)", url)
    return m.group(1) if m else "playlist"


def _playlist_display_name_from_url(url: str) -> str:
    """Prefer human playlist title from Spotify oEmbed; fallback to id slug."""
    try:
        req = urllib.request.Request(
            f"https://open.spotify.com/oembed?url={url}",
            headers={"User-Agent": random.choice(USER_AGENTS)},
        )
        with urllib.request.urlopen(req, timeout=20) as resp:
            payload = json.loads(resp.read().decode("utf-8", errors="ignore"))
        title = (payload.get("title") or "").strip()
        if title:
            return title
    except Exception:
        pass
    return _playlist_name_from_url(url)


def _normalize_playlist_name(value: str) -> str:
    lowered = value.lower().strip()
    cleaned = re.sub(r"[^a-z0-9]+", "", lowered)
    return cleaned


def _looks_like_spotify_id(value: str) -> bool:
    value = (value or "").strip()
    return bool(re.fullmatch(r"[A-Za-z0-9]{22}", value))


def _open_exportify_helper_page(playlist_name: str, playlist_url: str):
    helper_candidates = [
        Path(__file__).parent / "vendor" / "exportify" / "index.html",
        Path(__file__).parent / "crystalmedia" / "vendor" / "exportify" / "index.html",
    ]
    helper_page = next((p for p in helper_candidates if p.exists()), None)
    csv_dir = (Path.cwd() / "csv").resolve()
    if helper_page is not None:
        params = urllib.parse.urlencode({
            "playlist": playlist_name,
            "csv_dir": str(csv_dir),
            "playlist_url": playlist_url,
        })
        webbrowser.open(helper_page.resolve().as_uri() + "?" + params)
    else:
        webbrowser.open("https://watsonbox.github.io/exportify/")


def _csv_matches_playlist_name(csv_path: Path, playlist_name: str) -> bool:
    # If Spotify title lookup fails we may only have the 22-char playlist id.
    # In that case, don't enforce filename matching because Exportify filenames
    # typically use playlist titles, not raw ids.
    if _looks_like_spotify_id(playlist_name):
        return True
    needle = _normalize_playlist_name(playlist_name)
    if not needle:
        return True
    return needle in _normalize_playlist_name(csv_path.stem)


def _find_exportify_csv(playlist_name: str):
    csv_root = Path.cwd() / "csv"
    if not csv_root.exists():
        return None

    files = [p for p in csv_root.glob("*.csv") if p.is_file()]
    if not files:
        return None

    files.sort(key=lambda p: p.stat().st_mtime, reverse=True)

    needle = _normalize_playlist_name(playlist_name)
    if needle:
        for path in files:
            if needle in _normalize_playlist_name(path.stem):
                return path

    # If no name match, return newest so caller can explicitly validate and report.
    return files[0]


def _queries_from_exportify_csv(csv_path: Path, max_tracks: int = 300):
    queries = []
    with csv_path.open("r", encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f)
        for row in reader:
            title = (row.get("Track Name") or row.get("track_name") or "").strip()
            artists = (row.get("Artist Name(s)") or row.get("artist_names") or row.get("Artist Name") or "").strip()
            if title:
                query = f"{title} {artists}".strip()
                if query and query not in queries:
                    queries.append(query)
            if len(queries) >= max_tracks:
                break
    return queries


def _spotify_exportify_queries_interactive(url: str, wait_seconds: int = 180):
    console.print(Text("Spotify playlist helper (Exportify CSV)", style=COL_TITLE))
    console.print(Text("Exportify is the primary metadata source for Spotify playlists.", style=COL_MENU))
    console.print(Text("1) Login/auth at Exportify in your browser", style=COL_MENU))
    console.print(Text("2) Export your playlist to CSV", style=COL_MENU))
    console.print(Text("3) Save CSV into ./csv, then continue", style=COL_MENU))

    csv_dir = Path.cwd() / "csv"
    csv_dir.mkdir(parents=True, exist_ok=True)

    default_name = _playlist_display_name_from_url(url)
    console.print(Text(f"Playlist from link: {default_name}", style=COL_ACC))
    console.print(Text(f"CSV directory: {csv_dir.resolve()}", style=COL_MENU))

    try:
        _open_exportify_helper_page(default_name, url)
    except Exception:
        console.print(Text("Could not auto-open helper page. Open vendor/exportify/index.html manually.", style=COL_WARN))

    csv_input = console.input(Text("CSV filename in ./csv (Enter = auto-detect latest) → ", style=COL_ACC)).strip()
    if csv_input:
        csv_path = (csv_dir / csv_input).resolve()
        if not str(csv_path).startswith(str(csv_dir.resolve())):
            console.print(Text(f"CSV must be inside: {csv_dir.resolve()}", style=COL_ERR))
            return []
        if not csv_path.exists():
            console.print(Text(f"CSV not found: {csv_path}", style=COL_ERR))
            return []
        if not _csv_matches_playlist_name(csv_path, default_name):
            console.print(Text(f"CSV filename doesn't look like playlist '{default_name}', continuing anyway.", style=COL_WARN))
        return _queries_from_exportify_csv(csv_path)

    # No explicit filename: keep checking newest file until timeout.
    remaining = max(wait_seconds, 10)
    while remaining > 0:
        guessed_csv = _find_exportify_csv(default_name)
        if guessed_csv and guessed_csv.exists():
            if not _csv_matches_playlist_name(guessed_csv, default_name):
                console.print(Text(f"Using newest CSV despite name mismatch: {guessed_csv.name}", style=COL_WARN))
            else:
                console.print(Text(f"Detected Exportify CSV: {guessed_csv}", style=COL_GOOD))
            try:
                return _queries_from_exportify_csv(guessed_csv)
            except Exception as e:
                console.print(Text(f"Failed to parse CSV: {str(e)}", style=COL_ERR))
                return []
        if remaining % 10 == 0:
            console.print(Text(f"Waiting for CSV in ./csv ... {remaining}s", style=COL_MENU))
        time.sleep(1)
        remaining -= 1

    console.print(Text("Timed out waiting for CSV in ./csv.", style=COL_WARN))
    return []


def _resolve_spotify_url(url: str) -> str:
    """Follow Spotify share redirects and return canonical open.spotify URL when possible."""
    try:
        req = urllib.request.Request(url, headers={"User-Agent": random.choice(USER_AGENTS)})
        with urllib.request.urlopen(req, timeout=20) as resp:
            final_url = resp.geturl()
        return final_url or url
    except Exception:
        return url


def _extract_track_ids_from_page(page: str, max_tracks: int = 30):
    track_ids = []

    patterns = [
        r'/track/([A-Za-z0-9]{22})',
        r'\/track\/([A-Za-z0-9]{22})',
        r'open\.spotify\.com/track/([A-Za-z0-9]{22})',
        r'spotify:track:([A-Za-z0-9]{22})',
        r'spotify%3Atrack%3A([A-Za-z0-9]{22})',
        r'spotify%253Atrack%253A([A-Za-z0-9]{22})',
        r'"uri"\s*:\s*"spotify:track:([A-Za-z0-9]{22})"',
        r'"entityUri"\s*:\s*"spotify:track:([A-Za-z0-9]{22})"',
    ]
    for pattern in patterns:
        for tid in re.findall(pattern, page):
            if tid not in track_ids:
                track_ids.append(tid)
            if len(track_ids) >= max_tracks:
                return track_ids

    next_data_match = re.search(r'<script[^>]*id="__NEXT_DATA__"[^>]*>(.*?)</script>', page, flags=re.S)
    if next_data_match:
        payload_text = next_data_match.group(1)
        for tid in re.findall(r'"spotify:track:([A-Za-z0-9]{22})"', payload_text):
            if tid not in track_ids:
                track_ids.append(tid)
            if len(track_ids) >= max_tracks:
                return track_ids

    return track_ids


def _spotify_page_queries(url: str, max_tracks: int = 30):
    url = _resolve_spotify_url(url)
    req = urllib.request.Request(
        url,
        headers={
            "User-Agent": random.choice(USER_AGENTS),
            "Accept-Language": "en-US,en;q=0.9",
            "Referer": "https://open.spotify.com/",
        },
    )
    with urllib.request.urlopen(req, timeout=25) as resp:
        page = resp.read().decode("utf-8", errors="ignore")

    queries = []
    track_ids = _extract_track_ids_from_page(page, max_tracks=max_tracks)

    unresolved_track_ids = []
    for tid in track_ids:
        try:
            q = _spotify_oembed_query(f"https://open.spotify.com/track/{tid}")
            if q and q not in queries:
                queries.append(q)
            else:
                unresolved_track_ids.append(tid)
        except Exception:
            unresolved_track_ids.append(tid)
            continue
        if len(queries) >= max_tracks:
            break

    if queries:
        return queries

    # Last-resort fallback when IDs were found but oEmbed lookup is blocked/throttled.
    for tid in unresolved_track_ids[:max_tracks]:
        queries.append(f"https://open.spotify.com/track/{tid}")

    if queries:
        return queries

    # Fallback: row/label HTML parsing.
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
        query = f"{title} {artist}".strip()
        if query and query not in queries:
            queries.append(query)
        if len(queries) >= max_tracks:
            break
    return queries


def _download_spotify_queries_with_ytdlp(queries, target_dir: Path, progress_logger: FixedProgressLogger, embed_extras: bool = False):
    target_dir.mkdir(parents=True, exist_ok=True)

    class SpotifyYTDLPLogger:
        def __init__(self, logger):
            self.logger = logger
        def debug(self, msg):
            clean = strip_ansi(str(msg))
            if should_suppress_ytdlp_log(clean):
                return
            if '[youtube]' in clean and 'WARNING:' not in clean:
                self.logger.add_log(clean, 'info')
        def info(self, msg):
            clean = strip_ansi(str(msg))
            if clean and not should_suppress_ytdlp_log(clean):
                self.logger.add_log(clean, 'info')
        def warning(self, msg):
            clean = strip_ansi(str(msg))
            if should_suppress_ytdlp_log(clean):
                return
            self.logger.add_log(clean, 'warning')
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
    failed = 0
    total = max(len(queries), 1)
    for idx, query in enumerate(queries, start=1):
        progress_logger.add_log(f"[{idx}/{len(queries)}] Spotify fallback search: {query}", "info")
        progress_logger.update_progress(((idx - 1) / total) * 100, "Searching & downloading")
        query_ok = False
        try:
            with YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(f"ytsearch1:{query}", download=True)
            if embed_extras and isinstance(info, dict):
                for entry in iter_downloaded_entries(info):
                    mp3_path = extract_entry_final_path(entry)
                    if mp3_path:
                        write_mp3_tags(mp3_path, entry, embed_extras=True, user_agents=USER_AGENTS, log=progress_logger.add_log)
            query_ok = True
        except Exception as e:
            err_text = str(e)
            if is_age_restricted_error(err_text):
                progress_logger.add_log("Age-restricted result detected. Attempting browser-cookies fallback.", "warning")
                ok, _, browser_or_err = try_ytdlp_with_browser_cookies(f"ytsearch1:{query}", ydl_opts, progress_logger, extract_info_mode=False)
                if ok:
                    progress_logger.add_log(f"Cookie fallback succeeded with browser: {browser_or_err}", "success")
                    query_ok = True
                else:
                    progress_logger.add_log(f"Cookie fallback failed for query: {query}", "warning")
                    progress_logger.add_log(f"Last cookie error: {browser_or_err[:120]}", "warning")
            else:
                progress_logger.add_log(f"Failed query skipped: {query}", "warning")
                progress_logger.add_log(err_text[:120], "warning")

        if query_ok:
            count += 1
        else:
            failed += 1
        progress_logger.update_progress((idx / total) * 100, "Searching & downloading")

    return count, failed


def download_spotify(url: str, is_playlist: bool, embed_extras: bool = False) -> None:
    subfolder = "Playlist" if is_playlist else "Single"
    target_dir = DOWNLOADS_ROOT / "SPOTIFY" / subfolder
    target_dir.mkdir(parents=True, exist_ok=True)

    resolved_url = _resolve_spotify_url(url)
    queries = []

    try:
        if is_playlist or "/playlist/" in resolved_url or "/album/" in resolved_url:
            # Exportify is the primary path for playlist metadata.
            queries = _spotify_exportify_queries_interactive(resolved_url)
            if not queries:
                console.print(Text("Exportify produced no tracks; trying direct Spotify scrape fallback...", style=COL_WARN))
                queries = _spotify_page_queries(resolved_url)
        else:
            q = _spotify_oembed_query(resolved_url)
            if q:
                queries = [q]
    except Exception as e:
        console.print(Text(f"Metadata parsing fallback triggered: {str(e)[:120]}", style=COL_WARN))

    mode = "Playlist" if is_playlist else "Single Item"
    progress_header = build_download_header("Spotify fallback", mode, "audio", target_dir)
    progress_logger = FixedProgressLogger(console, progress_header)
    progress_logger.start()
    progress_logger.add_log("Spotify downloader (no-premium fallback mode)", "info")

    if queries:
        try:
            progress_logger.add_log(f"Loaded {len(queries)} metadata query item(s)", "info")
            downloaded, failed = _download_spotify_queries_with_ytdlp(queries, target_dir, progress_logger, embed_extras=embed_extras)
            progress_logger.mark_complete(f"Downloaded {downloaded} track(s); skipped {failed}.")
            progress_logger.add_log(f"✓ Downloaded {downloaded} track(s) → {target_dir}", "success")
            if failed:
                progress_logger.add_log(f"⚠ Skipped {failed} track(s) that failed extraction.", "warning")
            progress_logger.wait_for_continue("Spotify download success", 30)
            console.print(Text(f"Downloaded {downloaded} track(s) (skipped {failed}) → {target_dir}", style=COL_GOOD))
            return
        except Exception as e:
            progress_logger.add_log(f"yt-dlp Spotify fallback failed: {str(e)}", "error")

    progress_logger.add_log("Spotify fallback download did not complete.", "error")
    progress_logger.add_log("If age-restricted tracks fail, log into YouTube in your browser profile and retry.", "warning")
    progress_logger.add_log("Export playlist from https://watsonbox.github.io/exportify/ and retry with CSV.", "warning")
    progress_logger.stop()
    console.print(Text("Spotify metadata parsing failed for this URL. Export CSV via Exportify and retry.", style=COL_ERR))
    pause_for_reading("Spotify metadata parse failed — review above", 15)


# ──────────────────────────────────────────────
# Cross-platform arrow-key menu navigation
# ──────────────────────────────────────────────
def drain_pending_input():
    if platform.system() == "Windows":
        import msvcrt
        while msvcrt.kbhit():
            msvcrt.getch()
    else:
        import select
        try:
            while select.select([sys.stdin], [], [], 0)[0]:
                sys.stdin.read(1)
        except Exception:
            pass


def read_key(timeout: float = 0.05):
    """Cross-platform non-blocking arrow key / Enter detection."""
    if platform.system() == "Windows":
        import msvcrt
        if not msvcrt.kbhit():
            time.sleep(timeout)
            return None
        k = msvcrt.getch()
        if k in (b'\xe0', b'\x00') and msvcrt.kbhit():
            k2 = msvcrt.getch()
            if k2 == b'H':
                return "UP"
            if k2 == b'P':
                return "DOWN"
        elif k == b'\r':
            return "ENTER"
        elif k == b'\x03':
            raise KeyboardInterrupt
        return None

    import tty, termios, select
    if not sys.stdin.isatty():
        time.sleep(timeout)
        return None
    fd = sys.stdin.fileno()
    old = termios.tcgetattr(fd)
    try:
        tty.setraw(fd)
        rlist, _, _ = select.select([sys.stdin], [], [], timeout)
        if rlist:
            ch = sys.stdin.read(1)
            if ch == "\x1b":
                ch2 = sys.stdin.read(1)
                ch3 = sys.stdin.read(1)
                seq = ch + ch2 + ch3
                if seq == "\x1b[A":
                    return "UP"
                if seq == "\x1b[B":
                    return "DOWN"
            if ch in ("\r", "\n"):
                return "ENTER"
            if ch == "\x03":
                raise KeyboardInterrupt
        return None
    finally:
        termios.tcsetattr(fd, termios.TCSADRAIN, old)


# ──────────────────────────────────────────────
# Primary application loop
# ──────────────────────────────────────────────
def main_loop():
    categories = ["YouTube Video (MP4)", "YouTube Music (MP3)", "Spotify", "Exit"]
    selected_index = 0
    STARFIELD.start()

    drain_pending_input()
    display_full_splash()

    while True:
        try:
            with Live(console=console, refresh_per_second=60, screen=True) as live:
                while True:
                    live.update(build_main_menu_frame(categories, selected_index), refresh=True)
                    key = read_key(timeout=1 / 60)
                    if key == "UP":
                        selected_index = (selected_index - 1) % len(categories)
                    elif key == "DOWN":
                        selected_index = (selected_index + 1) % len(categories)
                    elif key == "ENTER":
                        break

            if selected_index == 3:
                STARFIELD.stop()
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
            embed_extras = select_embed_extras()

            display_clean_splash()

            if category_choice == "1":
                download_youtube(url_input, "video", is_playlist, embed_extras=embed_extras)
            elif category_choice == "2":
                download_youtube(url_input, "audio", is_playlist, embed_extras=embed_extras)
            elif category_choice == "3":
                download_spotify(url_input, is_playlist, embed_extras=embed_extras)

            console.input(Text("\nPress Enter to continue...", style=COL_ACC))

        except KeyboardInterrupt:
            console.print()
            console.print(Text("Keyboard interrupt detected. Returning to main menu.", style=COL_WARN))
            pause_for_reading("Interrupt acknowledged", 15)
            drain_pending_input()
            display_full_splash()
        except Exception as e:
            STARFIELD.stop()
            trace = traceback.format_exc()
            log_crash(f"Unexpected fatal error: {str(e)}")
            log_crash(trace)
            console.print(Panel(
                Text(
                    f"Unexpected fatal error: {str(e)}\n\nDetails were written to: {CRASH_LOG}",
                    style="bold red"
                ),
                title="Fatal Error",
                border_style="red"
            ))
            pause_for_reading("Fatal error — application will exit", 20)
            sys.exit(1)

if __name__ == "__main__":
    main_loop()
