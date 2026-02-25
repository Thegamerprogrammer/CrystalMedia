#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
CrystalMedia Downloader v3.1.9
==================================================

Spotify mode warning:
As of February 2026, spotdl in shared/default mode fails with 403 or 86400-second rate-limit errors due to Spotify's API policy changes.
Personal developer application credentials (requiring a Premium account) may restore functionality, but this is not implemented here.
Monitor the referenced issue for updates and upgrade spotdl when resolved: pip install --upgrade spotdl

Author: Thegamerprogram
License: MIT
"""

import sys
import subprocess
import os
import time
import random
from pathlib import Path
import shutil

import colorama
from colorama import Fore, Style
from pyfiglet import Figlet
import yt_dlp

colorama.init(autoreset=True)

# ──────────────────────────────────────────────
# Terminal styling
# ──────────────────────────────────────────────
BLUE_LOGO   = Fore.CYAN + Style.BRIGHT
BLUE_MEDIUM = Fore.CYAN
RESET       = Style.RESET_ALL

def print_colored(text: str, tone: str = 'medium') -> None:
    """Print styled text to terminal."""
    colour = BLUE_LOGO if tone == 'logo' else BLUE_MEDIUM
    print(colour + text + RESET)

def clear_screen() -> None:
    """Clear the terminal screen."""
    os.system('cls' if os.name == 'nt' else 'clear')

def display_splash() -> None:
    """Display application header."""
    figlet = Figlet(font='slant')
    print(BLUE_LOGO + figlet.renderText('CrystalMedia') + RESET)
    print_colored("v3.1.9", 'medium')
    print_colored("══════════════════════════════════════════════════════", 'medium')
    print_colored("Spotify mode: NON-FUNCTIONAL (February 2026 Developer Mode update)", 'medium')
    print_colored("Shared credentials rate-limited or rejected (403 / 86400s errors)", 'medium')
    print_colored("Refer: https://github.com/spotDL/spotify-downloader/issues/2617", 'medium')
    print()

# ──────────────────────────────────────────────
# Self-healing dependency management
# ──────────────────────────────────────────────
def ask_permission(component: str) -> bool:
    """Prompt user for permission to install a component."""
    print_colored(f"CrystalMedia requires {component} to function properly.", 'medium')
    response = input(BLUE_MEDIUM + f"Allow installation of {component}? [Y/n]: " + RESET).strip().lower()
    return response in ('', 'y', 'yes')

def run_command(cmd: list, silent: bool = False) -> bool:
    """Run shell command and return success status."""
    kwargs = {"stdout": subprocess.DEVNULL, "stderr": subprocess.DEVNULL} if silent else {}
    try:
        subprocess.check_call(cmd, **kwargs)
        return True
    except subprocess.CalledProcessError:
        return False

def heal_dependencies() -> None:
    """Detect and install missing dependencies with user consent."""
    print_colored("Performing dependency health check...", 'medium')

    # yt-dlp
    if not shutil.which("yt-dlp"):
        if ask_permission("yt-dlp"):
            print_colored("Installing yt-dlp...", 'medium')
            run_command([sys.executable, "-m", "pip", "install", "--upgrade", "yt-dlp[default,curl-cffi]"])
        else:
            print_colored("yt-dlp missing — YouTube mode will not function.", 'medium')

    # spotdl (includes Deno)
    if not shutil.which("spotdl"):
        if ask_permission("spotdl (includes Deno)"):
            print_colored("Installing spotdl...", 'medium')
            run_command([sys.executable, "-m", "pip", "install", "--upgrade", "spotdl"])
        else:
            print_colored("spotdl missing — Spotify mode will not function.", 'medium')

    # FFmpeg via spotdl
    if not shutil.which("ffmpeg"):
        if ask_permission("FFmpeg via spotdl"):
            print_colored("Running spotdl --download-ffmpeg...", 'medium')
            subprocess.run(["spotdl", "--download-ffmpeg"], check=False)
        else:
            print_colored("FFmpeg missing — audio conversion may fail.", 'medium')

    print_colored("Dependency health check completed.", 'medium')

heal_dependencies()

# ──────────────────────────────────────────────
# Directory structure
# ──────────────────────────────────────────────
def create_folders() -> None:
    """Initialise standardised download directory structure."""
    base = Path("downloads")
    base.mkdir(exist_ok=True)
    for category in ["YT VIDEO", "YT MUSIC", "SPOTIFY"]:
        for subcategory in ["Single", "Playlist"]:
            (base / category / subcategory).mkdir(parents=True, exist_ok=True)
    print_colored("Output directories initialised.", 'medium')

create_folders()

# ──────────────────────────────────────────────
# YouTube download logic
# ──────────────────────────────────────────────
USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Edg/131.0.0.0",
]

def get_ydl_options(is_playlist: bool, content_type: str) -> dict:
    """Generate configuration for yt-dlp."""
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
    """Prompt user to select desired MP3 bitrate."""
    print_colored("MP3 Bitrate Selection", 'medium')
    print_colored("  1. Low (96 kbps)", 'medium')
    print_colored("  2. Medium (128 kbps)", 'medium')
    print_colored("  3. Standard (192 kbps) [default]", 'medium')
    print_colored("  4. High (256 kbps)", 'medium')
    print_colored("  5. Insane (320 kbps)", 'medium')
    choice = input(BLUE_MEDIUM + "→ " + Style.RESET_ALL).strip() or "3"
    return {"1": "96", "2": "128", "3": "192", "4": "256", "5": "320"}.get(choice, "192")

def select_mp4_quality() -> str:
    """Prompt user to select desired MP4 video quality."""
    print_colored("MP4 Quality Selection", 'medium')
    print_colored("  1. Low (~360p)", 'medium')
    print_colored("  2. Medium (~480p–720p)", 'medium')
    print_colored("  3. High (~720p–1080p)", 'medium')
    print_colored("  4. Best (highest available) [default]", 'medium')
    choice = input(BLUE_MEDIUM + "→ " + Style.RESET_ALL).strip() or "4"
    if choice == "1": return "bestvideo[height<=?360][ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]"
    if choice == "2": return "bestvideo[height<=?720][ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]"
    if choice == "3": return "bestvideo[height<=?1080][ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]"
    return "bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best"

def download_youtube(url: str, content_type: str, is_playlist: bool) -> None:
    """Download content from YouTube using yt-dlp."""
    subfolder = "Playlist" if is_playlist else "Single"
    target_dir = Path("downloads") / ("YT VIDEO" if content_type == "video" else "YT MUSIC") / subfolder
    target_dir.mkdir(parents=True, exist_ok=True)

    mode = "Playlist" if is_playlist else "Single Item"
    print_colored(f"Initiating {mode} {content_type.upper()} download → {target_dir}", 'medium')

    options = get_ydl_options(is_playlist, content_type)

    retry_count = 0
    max_retries = 30
    while retry_count < max_retries:
        try:
            with yt_dlp.YoutubeDL(options) as downloader:
                downloader.extract_info(url, download=True)
            print_colored(f"Download complete → {target_dir}", 'medium')
            return
        except Exception as e:
            retry_count += 1
            print_colored(f"Attempt {retry_count}/{max_retries} failed: {str(e)}", tone='medium')
            if any(keyword in str(e).lower() for keyword in ["rate limit", "throttl", "429", "443", "connect"]):
                options["http_headers"]["User-Agent"] = random.choice(USER_AGENTS)
                print_colored("YouTube rate limit detected. Rotating user-agent...", tone='medium')
            time.sleep(random.uniform(4, 10))

    print_colored("Maximum retries reached. Check connection or try again later.", tone='medium')

def download_spotify(url: str, is_playlist: bool) -> None:
    """Attempt to download Spotify content using spotdl (currently non-functional)."""
    subfolder = "Playlist" if is_playlist else "Single"
    target_dir = Path("downloads/SPOTIFY") / subfolder
    target_dir.mkdir(parents=True, exist_ok=True)

    print_colored(f"Attempting to download {'playlist' if is_playlist else 'track'} → {target_dir}", 'medium')
    print_colored("WARNING: Spotify mode is BROKEN as of February 2026 Developer Mode update", tone='medium')
    print_colored("Shared application credentials are rate-limited or rejected (403 / 86400s errors)", tone='medium')
    print_colored("Refer: https://github.com/spotDL/spotify-downloader/issues/2617", tone='medium')
    print_colored("Update spotdl when a resolution is released: pip install --upgrade spotdl", tone='medium')

    cmd = [
        "spotdl", url,
        "--output", str(target_dir / "{playlist}/{artist} - {title}.{ext}" if is_playlist else "{artist} - {title}.{ext}"),
        "--threads", "1",
        "--max-retries", "10",
        "--no-cache",
    ]

    retry_count = 0
    max_retries = 5
    backoff = 5

    while retry_count < max_retries:
        try:
            time.sleep(backoff)
            subprocess.run(cmd, check=True)
            print_colored(f"Download complete → {target_dir}", 'medium')
            return
        except subprocess.CalledProcessError as e:
            err_msg = e.stdout.decode(errors='ignore') + e.stderr.decode(errors='ignore') if e.stdout or e.stderr else str(e)
            print_colored(f"Spotdl failed:\n{err_msg.strip()}", tone='medium')
            if any(keyword in err_msg for keyword in ["86400", "rate", "limit", "403"]):
                retry_count += 1
                backoff *= 2
                print_colored(f"Rate-limit or authentication issue detected (likely 86400s ban). Retrying in {backoff}s... ({retry_count}/{max_retries})", tone='medium')
            else:
                print_colored("Non-rate-limit error. Spotify mode is currently non-functional in shared mode.", tone='medium')
                return
        except Exception as e:
            print_colored(f"Unexpected error: {str(e)}", tone='medium')
            return

    print_colored("Maximum retries reached. Wait 24 hours or update spotdl when resolved.", tone='medium')

def main_loop() -> None:
    """Primary application loop."""
    while True:
        clear_screen()
        display_splash()
        try:
            print_colored("Main Category Selection", 'medium')
            print_colored("  1. YouTube Video (MP4)", 'medium')
            print_colored("  2. YouTube Music (MP3)", 'medium')
            print_colored("  3. Spotify Track/Playlist (Broken as of now)", 'medium')
            print_colored("  0. Exit Application", 'medium')
            category = input(BLUE_MEDIUM + "→ " + Style.RESET_ALL).strip()

            if category == "0":
                clear_screen()
                display_splash()
                print_colored("Thank you for using CrystalMedia. Exiting.", 'light')
                time.sleep(2)
                sys.exit(0)

            if category not in ["1", "2", "3"]:
                print_colored("Invalid category selected.", tone='medium')
                time.sleep(2)
                continue

            clear_screen()
            display_splash()
            print_colored("Mode Selection", 'medium')
            print_colored("  1. Single Item", 'medium')
            print_colored("  2. Playlist", 'medium')
            mode_choice = input(BLUE_MEDIUM + "→ " + Style.RESET_ALL).strip()
            is_playlist = mode_choice == "2"

            clear_screen()
            display_splash()
            url_input = input(BLUE_MEDIUM + "Resource URL → " + Style.RESET_ALL).strip()

            clear_screen()
            display_splash()

            if category == "1":
                download_youtube(url_input, "video", is_playlist)
            elif category == "2":
                download_youtube(url_input, "audio", is_playlist)
            elif category == "3":
                download_spotify(url_input, is_playlist)

            input("\nPress Enter to continue...")

        except KeyboardInterrupt:
            print_colored("Keyboard interrupt detected. Returning to main menu.", tone='medium')
            time.sleep(1)
        except Exception as e:
            print_colored(f"Unexpected error: {str(e)}", tone='medium')
            print_colored("Recovery in progress, returning to main menu.", tone='medium')
            time.sleep(2)

if __name__ == "__main__":
    main_loop()
