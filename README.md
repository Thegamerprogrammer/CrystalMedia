# 💎 CrystalMedia

> **A glassmorphism HTML GUI downloader backed by Python for YouTube MP4/MP3 + Spotify workflows.**

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](./LICENSE)
[![Python](https://img.shields.io/badge/Python-3.8%2B-brightgreen)](#-requirements)

---

## ⚡ Jump To

- [🚀 30-Second Quick Start](#-30-second-quick-start)
- [🧪 Interactive README + Full Visual Walkthrough](#-interactive-readme--full-visual-walkthrough)
- [🎮 Interactive Walkthrough](#-interactive-walkthrough)
- [⌨️ Controls Cheatsheet](#️-controls-cheatsheet)
- [🧠 Download Modes](#-download-modes)
- [🖥️ Live UI Preview](#️-live-ui-preview)
- [📁 Output Structure](#-output-structure)
- [🛠 Requirements](#-requirements)
- [❗ MIT License + Legal Warning](#-mit-license--legal-warning)

---

## 🚀 30-Second Quick Start

```bash
# From PyPI (recommended)
pip install crystalmedia

# Default = HTML GUI (pywebview)
crystalmedia
# Optional explicit GUI command
crystalmedia-gui
# Optional legacy terminal mode
crystalmedia-terminal

# From source
git clone https://github.com/Thegamerprogrammer/CrystalMedia.git
cd CrystalMedia
pip install .
crystalmedia
# Direct file launcher (now GUI-first)
python CrystalMedia.py
```

On first launch, CrystalMedia runs a dependency preflight/status check and self-healing diagnostics. Runtime auto-install of dependencies is disabled for packaging safety; install/update dependencies through pip.

---



## 🧊 Glass GUI (PyWebView)

> `CrystalMedia.py` in repo root is now a GUI-first launcher/backbone.
> Use `python CrystalMedia.py --terminal` only for legacy placeholder behavior.


CrystalMedia now runs as a **glassmorphism HTML GUI** powered by `pywebview` (default mode):

- Launch with: `crystalmedia` (or `crystalmedia-gui`)
- Uses a 3-column layout (actions / status / dotted logs column)
- Can ask for dependency auto-install from the GUI and stream install logs live
- Can run the classic CLI flow in a background process while logs stream to the GUI panel

## 🧪 Interactive README + Full Visual Walkthrough

Before install, you can explore a modern clickable mini site + complete visual docs:

- **Interactive README (glass UI):** `docs/interactive-readme.html`
- **Pre-install demo:** `docs/interactive-demo.html`
- **PyPI page:** https://pypi.org/project/crystalmedia/

> On Windows, open `docs\interactive-readme.html` directly in your browser.

### Full Screenshot Gallery (Setup + Functions + Troubleshooting)

#### Setup
![Setup Python](docs/media/07-setup-python.svg)
![Setup PyPI Install](docs/media/08-setup-pip-install.svg)
![Setup Source Install](docs/media/09-setup-source.svg)

#### Core UI
![Splash](docs/media/01-splash.svg)
![Main Menu](docs/media/02-main-menu.svg)
![Success](docs/media/06-success.svg)

#### YouTube Functions
![YouTube Flow](docs/media/03-youtube-flow.svg)
![YouTube MP4 Quality](docs/media/10-youtube-mp4-quality.svg)
![YouTube MP3 Bitrate](docs/media/11-youtube-mp3-bitrate.svg)

#### Spotify Functions
![Spotify Exportify](docs/media/04-spotify-exportify.svg)
![Spotify Single](docs/media/12-spotify-single.svg)
![Spotify Playlist CSV](docs/media/13-spotify-playlist-csv.svg)

#### When You Get Stuck
![Stuck Help](docs/media/05-stuck-help.svg)
![Age Restricted Troubleshooting](docs/media/14-stuck-age-restricted.svg)
![Missing Dependencies Troubleshooting](docs/media/15-stuck-missing-deps.svg)
![Output and Logs](docs/media/16-output-structure.svg)

### Video / GIF recommendation for release docs

To publish real full-session recordings (menu navigation, mode selection, progress logs, and recovery flows), record with:

- **OBS Studio** (long-form videos)
- **ScreenToGif** (quick GIF walkthroughs)
- **ShareX** (clip + GIF export)

Then attach them to GitHub Releases and embed links in this README.

---

## 🎮 Interactive Walkthrough

When the app starts, the flow is designed to feel game-like and guided:

1. **Splash appears** (`CrystalMedia` logo + version)
2. **Main menu** opens (YouTube Video / YouTube Music / Spotify / Exit)
3. You choose:
   - Single item or playlist
   - URL
   - MP4 quality or MP3 bitrate
   - JavaScript runtime preference (Auto / Deno-first / Node-first)
4. **Live UI kicks in**:
   - Header panel with current context
   - `Progress` panel (single progress bar)
   - `Download Log` panel (bounded recent yt-dlp events)
5. On completion, timeout prompt waits for input (or auto-returns)

---

## ⌨️ Controls Cheatsheet

| Action | Key |
|---|---|
| Move up/down in menu | `↑ / ↓` |
| Select menu item | `Enter` |
| Skip wait timer / continue now | `Any key` or `Enter` |
| Interrupt current flow | `Ctrl + C` |

---

## 🧠 Download Modes

### 🎬 YouTube Video (MP4)
- Quality presets: low → best available
- Single or playlist
- Remux/postprocess handling with ffmpeg

### 🎵 YouTube Music (MP3)
- Bitrate presets: 96 → 320 kbps
- Single or playlist
- Audio extraction postprocessing

### 🎧 Spotify (Exportify-first Playlist Mode)
- **Single track**: reads Spotify metadata and downloads via `yt-dlp` search (with automatic browser-cookie fallback for age-restricted YouTube matches).
- **Playlist/album**: **Exportify CSV is the primary path**.
  1. Open your playlist URL in CrystalMedia.
  2. CrystalMedia opens `vendor/exportify/index.html` helper + Exportify in browser.
  3. Export the **same playlist** and save CSV in `./csv` (next to `CrystalMedia.py`).
  4. Filename matching is used as a hint; CrystalMedia will still try the newest CSV if names do not match.
  5. CrystalMedia reads that CSV and downloads each song via `yt-dlp` search.

If no CSV is found, CrystalMedia attempts direct Spotify page scraping fallback.


### 🍪 Age-restricted YouTube matches (Spotify fallback)
- CrystalMedia now auto-tries `yt-dlp --cookies-from-browser` profiles when YouTube returns age/sign-in restrictions.
- For best results, sign in to YouTube in your normal (non-incognito) browser profile first.
- If browser-cookie extraction still fails, export a Netscape cookies file and pass it manually in yt-dlp workflows.

---

## 🖥️ Live UI Preview

CrystalMedia uses a fixed Rich layout to keep output readable:

- **Header panel:** logo + current download context
- **Progress panel:** one progress bar (download/processing/merging)
- **Download Log panel:** compact rolling logs with truncation + color tags

This minimizes noisy terminal spam and keeps the interface focused.

---

## 📁 Output Structure

```text
CrystalMedia/
├── downloads/
│   ├── YT VIDEO/
│   │   ├── Single/
│   │   └── Playlist/
│   ├── YT MUSIC/
│   │   ├── Single/
│   │   └── Playlist/
│   └── SPOTIFY/
│       ├── Single/
│       └── Playlist/
└── logs/
    ├── log.txt
    ├── crash.txt
    └── deps.txt
```

---

## 🛠 Requirements

- Python **3.8+**
- Internet connection
- FFmpeg (app can help bootstrap if missing)

---

## ❗ MIT License + Legal Warning

CrystalMedia is released under the **MIT License** (see [`LICENSE`](./LICENSE)).

### Important warning

- The MIT License allows broad use/modification/distribution of this software.
- **It does not grant rights to download copyrighted media without permission.**
- You are solely responsible for how you use this tool and for compliance with local laws/platform terms.

Use responsibly and only with content you are authorized to download.

---

## 🧯 Troubleshooting

- If terminal rendering looks off after a resize, return to the main menu and start the download again.
- Check `CrystalMedia/logs/crash.txt` for error traces and `CrystalMedia/logs/deps.txt` for dependency snapshots after startup.

---

---

PRs are welcome for UI polish, reliability improvements, and Spotify-mode recovery when upstream ecosystem changes stabilize.


## 🧾 Exportify CSV (Playlist) Quick Notes

- CSV files **must be in** `./csv` (relative to where you run `CrystalMedia.py`).
- Leave filename blank in prompt to auto-detect latest CSV in `./csv` that matches playlist name.
- Playlist title is auto-derived from the Spotify playlist link and used for fuzzy CSV matching.
