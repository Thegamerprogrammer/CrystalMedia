
"""
CrystalMedia Downloader v3.1.9
==============================

Spotify mode note:
Spotdl shared mode is frequently rate-limited (86400s) after Spotify's 2025 update.
Personal credentials or --musicbrainz workaround may help, but not implemented here.
Update spotdl when fixed: pip install --upgrade spotdl

Author: Thegamerprogram
License: MIT
"""

import sys
import subprocess
import os
import time
import random
from pathlib import Path

import colorama
from colorama import Fore, Style
from pyfiglet import Figlet
import yt_dlp

colorama.init(autoreset=True)

# ──────────────────────────────────────────────
# Colors & UI
# ──────────────────────────────────────────────
BLUE_LOGO   = Fore.CYAN + Style.BRIGHT
BLUE_MEDIUM = Fore.CYAN
CREAMY_RESET = Style.RESET_ALL

def print_colored(text: str, tone: str = 'medium') -> None:
    color = BLUE_LOGO if tone == 'logo' else BLUE_MEDIUM
    print(color + text + CREAMY_RESET)

def clear_screen():
    os.system('cls' if os.name == 'nt' else 'clear')

def display_splash():
    figlet = Figlet(font='slant')
    print(BLUE_LOGO + figlet.renderText('CrystalMedia') + CREAMY_RESET)
    print_colored("v3.1.9", 'medium')
    print_colored("══════════════════════════════════════════════════════", 'medium')
    print()

# ──────────────────────────────────────────────
# Folders
# ──────────────────────────────────────────────
def create_folders():
    base = Path("downloads")
    base.mkdir(exist_ok=True)
    for cat in ["YT VIDEO", "YT MUSIC", "SPOTIFY"]:
        for sub in ["Single", "Playlist"]:
            (base / cat / sub).mkdir(parents=True, exist_ok=True)
    print_colored("Output folders initialized.", 'medium')

create_folders()

# ──────────────────────────────────────────────
# YouTube logic
# ──────────────────────────────────────────────
USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Edg/131.0.0.0",
]

def get_ydl_options(is_playlist: bool, content_type: str) -> dict:
    subfolder = "Playlist" if is_playlist else "Single"
    base_path = f"downloads/{'YT VIDEO' if content_type == 'video' else 'YT MUSIC'}/{subfolder}/%(playlist_title)s/%(title)s.%(ext)s" if is_playlist else f"downloads/{'YT VIDEO' if content_type == 'video' else 'YT MUSIC'}/{subfolder}/%(title)s.%(ext)s"

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
    print_colored("MP3 Bitrate Selection", 'medium')
    print_colored("  1. Low (96 kbps)", 'medium')
    print_colored("  2. Medium (128 kbps)", 'medium')
    print_colored("  3. Standard (192 kbps) [default]", 'medium')
    print_colored("  4. High (256 kbps)", 'medium')
    print_colored("  5. Insane (320 kbps)", 'medium')
    ch = input(BLUE_MEDIUM + "→ " + CREAMY_RESET).strip() or "3"
    return {"1": "96", "2": "128", "3": "192", "4": "256", "5": "320"}.get(ch, "192")

def select_mp4_quality() -> str:
    print_colored("MP4 Quality Selection", 'medium')
    print_colored("  1. Low (~360p)", 'medium')
    print_colored("  2. Medium (~480p–720p)", 'medium')
    print_colored("  3. High (~720p–1080p)", 'medium')
    print_colored("  4. Best (highest available) [default]", 'medium')
    ch = input(BLUE_MEDIUM + "→ " + CREAMY_RESET).strip() or "4"
    if ch == "1": return "bestvideo[height<=?360][ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]"
    if ch == "2": return "bestvideo[height<=?720][ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]"
    if ch == "3": return "bestvideo[height<=?1080][ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]"
    return "bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best"

def download_youtube(url: str, content_type: str, is_playlist: bool):
    subfolder = "Playlist" if is_playlist else "Single"
    target_dir = Path("downloads") / ("YT VIDEO" if content_type == "video" else "YT MUSIC") / subfolder
    target_dir.mkdir(parents=True, exist_ok=True)

    mode = "Playlist" if is_playlist else "Single Item"
    print_colored(f"Initiating {mode} {content_type.upper()} Acquisition → {target_dir}", 'medium')

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
            if any(kw in str(e).lower() for kw in ["rate limit", "throttl", "429", "443", "connect"]):
                options["http_headers"]["User-Agent"] = random.choice(USER_AGENTS)
                print_colored("YouTube rate limit detected. Rotating user-agent...", tone='medium')
            time.sleep(random.uniform(4, 10))

    print_colored("Max retries reached. Check connection or try again later.", tone='medium')

def download_spotify(url: str, is_playlist: bool):
    subfolder = "Playlist" if is_playlist else "Single"
    target_dir = Path("downloads/SPOTIFY") / subfolder
    target_dir.mkdir(parents=True, exist_ok=True)

    print_colored(f"Ripping {'playlist' if is_playlist else 'track'} → {target_dir}", 'medium')
    print_colored("WARNING: Spotify mode is BROKEN as of now (shared key rate-limited).", tone='medium')
    print_colored("Trying anyway — update spotdl when fixed: pip install --upgrade spotdl", tone='medium')

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
            print_colored(f"Rip complete → {target_dir}", 'medium')
            return
        except subprocess.CalledProcessError as e:
            err_msg = e.stdout.decode(errors='ignore') + e.stderr.decode(errors='ignore') if e.stdout or e.stderr else str(e)
            print_colored(f"Spotdl failed:\n{err_msg.strip()}", tone='medium')
            if "86400" in err_msg or "rate" in err_msg.lower() or "limit" in err_msg.lower() or "403" in err_msg:
                retry_count += 1
                backoff *= 2
                print_colored(f"Rate/auth ban (likely 86400s). Backing off {backoff}s... ({retry_count}/{max_retries})", tone='medium')
            else:
                print_colored("Non-rate/auth error. Spotdl is probably bricked harder than we thought.", tone='medium')
                return
        except Exception as e:
            print_colored(f"Unexpected crash: {str(e)}", tone='medium')
            return

    print_colored("Max retries reached. Wait 24h or update spotdl when fixed.", tone='medium')

def main_loop():
    while True:
        clear_screen()
        display_splash()
        try:
            print_colored("Main Category Selection", 'medium')
            print_colored("  1. YouTube Video (MP4)", 'medium')
            print_colored("  2. YouTube Music (MP3)", 'medium')
            print_colored("  3. Spotify Track/Playlist (Broken as of now)", 'medium')
            print_colored("  0. Exit Application", 'medium')
            category = input(BLUE_MEDIUM + "→ " + CREAMY_RESET).strip()

            if category == "0":
                clear_screen()
                display_splash()
                print_colored("Thank you for using CrystalMedia. Exiting.", 'light')
                time.sleep(2)
                sys.exit(0)

            if category not in ["1", "2", "3"]:
                print_colored("Invalid category.", tone='medium')
                time.sleep(2)
                continue

            clear_screen()
            display_splash()
            print_colored("Mode Selection", 'medium')
            print_colored("  1. Single Item", 'medium')
            print_colored("  2. Playlist", 'medium')
            mode_choice = input(BLUE_MEDIUM + "→ " + CREAMY_RESET).strip()
            is_playlist = mode_choice == "2"

            clear_screen()
            display_splash()
            url_input = input(BLUE_MEDIUM + "Resource URL → " + CREAMY_RESET).strip()

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
            print_colored("Recovery in progress — returning to main menu.", tone='medium')
            time.sleep(2)

if __name__ == "__main__":

    main_loop()
