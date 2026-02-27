#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
CrystalMedia Downloader – Stable Production Release v3.1.9
==========================================================
Cross-platform media downloader for YouTube & Spotify.
YouTube: works like a beast
Spotify: currently non-functional (Feb 2026 dev mode killed shared creds)
Refer: https://github.com/spotDL/spotify-downloader/issues/2617
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

print("CrystalMedia performing dependency health check...")

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
        os.environ["PATH"] += os.pathsep + user_scripts_str
        print(f"Added real Windows user Scripts to PATH: {user_scripts_str}")

# Unix/macOS/Linux: add ~/.local/bin if missing
elif platform.system() in ("Linux", "Darwin"):
    local_bin = os.path.expanduser("~/.local/bin")
    if local_bin not in os.environ.get("PATH", "").split(os.pathsep):
        os.environ["PATH"] += os.pathsep + local_bin
        print(f"Added ~/.local/bin to PATH for Unix/macOS compatibility")

# Deno
if not command_exists("deno"):
    if ask_install("Deno (yt-dlp needs it for YouTube JS challenges)"):
        print("Installing Deno...")
        if platform.system() == "Windows":
            run_quiet(["powershell", "-Command", "irm https://deno.land/install.ps1 | iex"])
        else:
            run_quiet(["curl", "-fsSL", "https://deno.land/install.sh", "|", "sh"])
        if not command_exists("deno"):
            print("Deno install failed. Go to https://deno.com manually.")
    else:
        print("Deno skipped — YouTube may choke on protected videos.")

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

# rich + pyfiglet
for pkg in ["rich", "pyfiglet"]:
    try:
        __import__(pkg.replace("-", "_"))
    except ImportError:
        if ask_install(pkg):
            print(f"Installing {pkg}...")
            run_quiet([sys.executable, "-m", "pip", "install", "--upgrade", pkg])

print("Dependency health check completed. Importing libraries...\n")

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
                ("Press any key or Enter to continue", "italic dim")
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
                if select.select([sys.stdin], [], [], 0.1)[0]:
                    sys.stdin.read(1)
                    break
            time.sleep(1)
            remaining -= 1

# 5-second countdown after import list
pause_for_reading("Imports complete", 5)

# ──────────────────────────────────────────────
# Download FFmpeg directly from gyan.dev if missing
# ──────────────────────────────────────────────
def download_ffmpeg():
    ffmpeg_dir = Path("ffmpeg")
    bin_dir = ffmpeg_dir / "bin"
    bin_dir.mkdir(parents=True, exist_ok=True)
    if command_exists("ffmpeg"):
        console.print(Text("FFmpeg already found in PATH — skipping.", style=COL_GOOD))
        return
    console.print(Text("FFmpeg missing — downloading from gyan.dev...", style=COL_WARN))
    base_url = "https://www.gyan.dev/ffmpeg/builds/"
    if platform.system() == "Windows":
        url = base_url + "ffmpeg-release-essentials.zip"
        archive = "ffmpeg.zip"
    else:
        url = base_url + "ffmpeg-release-amd64-static.tar.xz"
        archive = "ffmpeg.tar.xz"
    archive_path = Path(archive)
    try:
        console.print(f"[cyan]Downloading {url.split('/')[-1]}...[/cyan]")
        urllib.request.urlretrieve(url, archive_path)
        console.print("[cyan]Extracting binaries...[/cyan]")
        if platform.system() == "Windows":
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
        console.print(Text("FFmpeg binaries downloaded to ./ffmpeg/bin", style=COL_GOOD))
        os.environ["PATH"] += os.pathsep + str(bin_dir.absolute())
        console.print(f"[dim]Added {bin_dir} to session PATH[/dim]")
    except Exception as e:
        console.print(Text(f"FFmpeg download failed: {str(e)}", style=COL_ERR))
        console.print(Text("Manually grab it from https://www.gyan.dev/ffmpeg/builds/", style=COL_WARN))

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
    console.print(Panel(
        Text(
            "Spotify mode: NON-FUNCTIONAL (February 2026 Developer Mode update)\n"
            "Shared credentials are rate-limited or rejected (403 / 86400s errors)\n"
            "Refer: https://github.com/spotDL/spotify-downloader/issues/2617\n"
            "Upgrade spotdl when resolved: pip install --upgrade spotdl",
            justify="center",
            style="bold red"
        ),
        title="Important Notice",
        border_style="red"
    ))
    pause_for_reading("Reading warning", 15)

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
    base = Path("downloads")
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
class FixedProgressLogger:
    """Fixed progress bar + scrolling log panel using Rich Layout"""
    def __init__(self, console_obj, header_text: Text):
        self.console = console_obj
        self.logs = []
        self.layout = Layout()
        self.layout.split_column(
            Layout(name="progress", size=8),
            Layout(name="logs", size=16)
        )
        self.progress = Progress(
            SpinnerColumn(style=COL_MENU),
            TextColumn("[progress.description]{task.description}", style=COL_MENU),
            BarColumn(complete_style=COL_MENU, finished_style=COL_MENU, pulse_style=COL_MENU),
            TextColumn("[progress.percentage]{task.percentage:>3.0f}%", style=COL_MENU),
            console=self.console
        )
        self.task = None
        self.live = Live(self.layout, console=self.console, refresh_per_second=4)
        self.max_logs = 12
        self.max_log_width = 110
        self.layout["progress"].update(self._waiting_panel())
        
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
        # Keep last 15 logs visible
        if len(self.logs) > 15:
            self.logs = self.logs[-15:]
        
        # Update log panel
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
        """Update progress bar"""
        if self.task is None:
            self.task = self.progress.add_task(description, total=100)
        self.progress.update(self.task, completed=percent, description=description)
        self.layout["progress"].update(
            Panel(self.progress, title="Progress", border_style=COL_MENU, title_align="left")
        )
    
    def mark_complete(self, description: str = "Download complete!"):
        """Show a completed progress state even when file already exists."""
        if self.task is None:
            self.task = self.progress.add_task(description, total=100, completed=100)
        else:
            self.progress.update(self.task, completed=100, description=description)
        self.layout["progress"].update(
            Panel(self.progress, title="Progress", border_style=COL_MENU, title_align="left")
        )

    def start(self):
        self.live.start()

    def stop(self):
        self.live.stop()


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
        f"downloads/{'YT VIDEO' if content_type == 'video' else 'YT MUSIC'}/{subfolder}/%(playlist_title)s/%(title)s.%(ext)s"
        if is_playlist else
        f"downloads/{'YT VIDEO' if content_type == 'video' else 'YT MUSIC'}/{subfolder}/%(title)s.%(ext)s"
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
    target_dir = Path("downloads") / ("YT VIDEO" if content_type == "video" else "YT MUSIC") / subfolder
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
                self.logger.mark_complete("Download complete!")
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
    final_path = None
    download_completed = False
    while retry_count < max_retries:
        try:
            with YoutubeDL(options) as downloader:
                downloader.extract_info(url, download=True)
            progress_logger.mark_complete("Download complete!")
            progress_logger.add_log(f"✓ Download complete → {target_dir}", "success")
            progress_logger.wait_for_continue("Download success", 30)
            progress_logger.stop()
            pause_for_reading("Download success — review above", 30)
            return
        except KeyboardInterrupt:
            progress_logger.stop()
            raise
        except Exception as e:
            retry_count += 1
            progress_logger.add_log(f"Attempt {retry_count}/{max_retries} failed: {str(e)[:80]}", "warning")
            if any(keyword in str(e).lower() for keyword in ["rate limit", "throttl", "429", "443"]):
                options["http_headers"]["User-Agent"] = random.choice(USER_AGENTS)
                progress_logger.add_log("Rate limit detected. Rotating user-agent...", "warning")
            time.sleep(random.uniform(4, 10))

    if download_completed:
        progress_logger.mark_complete("Download complete!")
        if final_path:
            progress_logger.add_log(f"✓ Final file: {final_path}", "success")
        progress_logger.add_log(f"✓ Download complete → {target_dir}", "success")
        if hasattr(progress_logger, "wait_for_continue"):
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

def download_spotify(url: str, is_playlist: bool) -> None:
    subfolder = "Playlist" if is_playlist else "Single"
    target_dir = Path("downloads/SPOTIFY") / subfolder
    target_dir.mkdir(parents=True, exist_ok=True)

    try:
        spotdl_client = Spotdl()
        songs = spotdl_client.search([url])
        title = songs[0].name if songs else "Unknown track"
        if is_playlist:
            title = "Playlist"
        console.print(Text("Downloading: ", style=COL_ACC), end="")
        console.print(Text(title, style="bold yellow"))
    except:
        console.print(Text("Could not extract title — downloading anyway...", style=COL_WARN))

    console.print(Text(f"Attempting to download {'playlist' if is_playlist else 'track'} → {target_dir}", style=COL_ACC))

    console.print(Panel(
        Text(
            "Spotify mode is non-functional due to February 2026 Developer Mode update.\n"
            "Shared credentials are rate-limited or rejected (403 / 86400s errors).\n"
            "Refer: https://github.com/spotDL/spotify-downloader/issues/2617\n"
            "Upgrade spotdl when resolved: pip install --upgrade spotdl",
            justify="center",
            style="bold red"
        ),
        title="Spotify Status",
        border_style="red"
    ))

    pause_for_reading("Spotify warning — review above", 15)

    try:
        spotdl_client = Spotdl()
        songs = spotdl_client.search([url])
        results = spotdl_client.download_songs(songs)
        console.print(Text(f"Downloaded {len(results)} track(s) → {target_dir}", style=COL_GOOD))
        pause_for_reading("Spotify download finished — review above", 15)
    except Exception as e:
        console.print(Text(f"Spotify download failed: {str(e)}", style=COL_ERR))
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
    categories = ["YouTube Video (MP4)", "YouTube Music (MP3)", "Spotify (Broken)", "Exit"]
    selected_index = 0

    # FIX: Clear any leftover keypresses from the library countdown
    # so they don't accidentally skip the Spotify warning pause
    if platform.system() == "Windows":
        import msvcrt
        while msvcrt.kbhit():
            msvcrt.getch()  # drain any pending keys
    else:
        import select
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
                    display_clean_splash()
                    console.print(Panel(
                        Text(
                            "Spotify mode is non-functional due to February 2026 Developer Mode update.\n"
                            "Shared credentials are rate-limited or rejected (403 / 86400s errors).\n"
                            "Refer: https://github.com/spotDL/spotify-downloader/issues/2617\n"
                            "Upgrade spotdl when resolved: pip install --upgrade spotdl",
                            justify="center",
                            style="bold red"
                        ),
                        title="Spotify Status",
                        border_style="red"
                    ))
                    pause_for_reading("Spotify warning — review above", 15)
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
            pause_for_reading("Error — copy the message above", 15)
            console.print(Text("Recovery in progress — returning to main menu.", style=COL_WARN))
            pause_for_reading("Resuming", 15)

if __name__ == "__main__":
    main_loop()
