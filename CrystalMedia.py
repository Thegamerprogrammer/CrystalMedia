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
    print(f"\nCrystalMedia needs {what} to not be a broken tool.")
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
from rich.progress import Progress, SpinnerColumn, BarColumn, TextColumn
from pyfiglet import Figlet
import yt_dlp
from yt_dlp import YoutubeDL
from spotdl import Spotdl

console = Console()

# ──────────────────────────────────────────────
# Pastel blue theme constants — defined early
# ──────────────────────────────────────────────
COL_TITLE = "bold #A5D8FF"
COL_ACC   = "bold #B3E0FF"
COL_WARN  = "bold #FFE066"
COL_ERR   = "bold #FF9999"
COL_GOOD  = "bold #B2F2BB"
COL_MENU  = "bold #D6E4FF"

# ──────────────────────────────────────────────
# List imported libraries with style
# ──────────────────────────────────────────────
console.print("\n[bold cyan]Libraries loaded after healing:[/bold cyan]")
libs = [
    ("rich", "console, panel, text, live, progress"),
    ("pyfiglet", "ascii art"),
    ("yt_dlp", "YouTube downloader"),
    ("spotdl", "Spotify downloader"),
]
for name, desc in libs:
    console.print(f"  • [bold green]{name}[/bold green] → {desc}")

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
                (f"{message} {remaining}...\n\n", COL_ACC),
                ("Press any key or Enter to continue", "italic dim")
            )
            live.update(
                Panel(
                    content,
                    title="Timeout",
                    border_style=COL_WARN,
                    padding=(1, 2),
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

    console.print(Text("Resuming...", style=COL_ACC))
    time.sleep(0.5)

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
    console.print(Text("v3.1.9 – Stable Production Release • 2026", style=COL_ACC))
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
# YouTube download logic (native API + title display + yellow logs)
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
        "quiet": False,
        "no_warnings": False,
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
    console.print(Text("  1. Low (96 kbps)", style=COL_MENU))
    console.print(Text("  2. Medium (128 kbps)", style=COL_MENU))
    console.print(Text("  3. Standard (192 kbps) [default]", style=COL_MENU))
    console.print(Text("  4. High (256 kbps)", style=COL_MENU))
    console.print(Text("  5. Insane (320 kbps)", style=COL_MENU))
    choice = console.input(Text("→ ", style=COL_ACC)).strip() or "3"
    return {"1": "96", "2": "128", "3": "192", "4": "256", "5": "320"}.get(choice, "192")

def select_mp4_quality() -> str:
    console.print(Text("MP4 Quality Selection", style=COL_TITLE))
    console.print(Text("  1. Low (~360p)", style=COL_MENU))
    console.print(Text("  2. Medium (~480p–720p)", style=COL_MENU))
    console.print(Text("  3. High (~720p–1080p)", style=COL_MENU))
    console.print(Text("  4. Best (highest available) [default]", style=COL_MENU))
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
        console.print(Text(f"Downloading: [bold yellow]{title}[/bold yellow]", style=COL_ACC))
    except:
        title = "Unknown title"
        console.print(Text("Could not extract title — downloading anyway...", style=COL_WARN))

    subfolder = "Playlist" if is_playlist else "Single"
    target_dir = Path("downloads") / ("YT VIDEO" if content_type == "video" else "YT MUSIC") / subfolder
    target_dir.mkdir(parents=True, exist_ok=True)

    mode = "Playlist" if is_playlist else "Single Item"
    console.print(Text(f"Initiating {mode} {content_type.upper()} download → {target_dir}", style=COL_ACC))

    options = get_ydl_options(is_playlist, content_type)

    class ColorisedProgress:
        def __init__(self):
            self.progress = Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                BarColumn(),
                TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
                console=console
            )
            self.task = None

        def progress_hook(self, d):
            if d['status'] == 'downloading':
                if not self.task:
                    self.task = self.progress.add_task("[cyan]Downloading...", total=100)
                raw_percent = d.get('_percent_str', '0%')
                clean_percent = strip_ansi(raw_percent).strip('%')
                try:
                    percent = float(clean_percent)
                    self.progress.update(self.task, completed=percent)
                except ValueError:
                    pass
            elif d['status'] == 'finished':
                console.print(Text("Download complete. Processing...", style=COL_GOOD))

    progress = ColorisedProgress()
    options["progress_hooks"] = [progress.progress_hook]

    # Custom logger to color yt-dlp output yellow
    class YellowLogger:
        def debug(self, msg):
            if msg.startswith('[youtube]') or msg.startswith('[download]') or msg.startswith('[info]') or msg.startswith('[Merger]'):
                console.print(f"[yellow]{msg}[/yellow]")
        def info(self, msg):
            console.print(f"[yellow]{msg}[/yellow]")
        def warning(self, msg):
            console.print(f"[yellow]{msg}[/yellow]")
        def error(self, msg):
            console.print(f"[red]{msg}[/red]")

    options["logger"] = YellowLogger()

    retry_count = 0
    max_retries = 30
    while retry_count < max_retries:
        try:
            with YoutubeDL(options) as downloader:
                downloader.extract_info(url, download=True)
            console.print(Text(f"Download complete → {target_dir}", style=COL_GOOD))
            pause_for_reading("Download success — review above", 15)
            return
        except Exception as e:
            retry_count += 1
            console.print(Text(f"Attempt {retry_count}/{max_retries} failed: {str(e)}", style=COL_WARN))
            pause_for_reading("Error — copy the message above", 15)
            if any(keyword in str(e).lower() for keyword in ["rate limit", "throttl", "429", "443", "connect"]):
                options["http_headers"]["User-Agent"] = random.choice(USER_AGENTS)
                console.print(Text("YouTube rate limit detected. Rotating user-agent...", style=COL_WARN))
            time.sleep(random.uniform(4, 10))

    console.print(Text("Maximum retries reached. Check connection or try again later.", style=COL_ERR))
    pause_for_reading("Max retries — review above", 15)

def download_spotify(url: str, is_playlist: bool) -> None:
    subfolder = "Playlist" if is_playlist else "Single"
    target_dir = Path("downloads/SPOTIFY") / subfolder
    target_dir.mkdir(parents=True, exist_ok=True)

    # Try to get title from spotdl
    try:
        spotdl_client = Spotdl()
        songs = spotdl_client.search([url])
        title = songs[0].name if songs else "Unknown track"
        if is_playlist:
            title = "Playlist"
        console.print(Text(f"Downloading: [bold yellow]{title}[/bold yellow]", style=COL_ACC))
    except:
        console.print(Text("Could not extract title — downloading anyway...", style=COL_WARN))

    console.print(Text(f"Attempting to download {'playlist' if is_playlist else 'track'} → {target_dir}", style=COL_ACC))

    console.print(Panel(
        Text(
            "Spotify mode is non-functional due to February 2025 Developer Mode update.\n"
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

    # Initial splash with Spotify warning
    display_full_splash()

    while True:
        display_clean_splash()

        console.print(Text("Main Category Selection", style=COL_TITLE))
        for i, category in enumerate(categories):
            prefix = "→ " if i == selected_index else "  "
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
                console.print(Text("  1. Single Item", style=COL_MENU))
                console.print(Text("  2. Playlist", style=COL_MENU))
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
                            "Spotify mode is non-functional due to February 2025 Developer Mode update.\n"
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
