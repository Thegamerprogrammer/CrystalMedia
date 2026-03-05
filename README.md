# 💎 CrystalMedia

> **A hyper-interactive terminal downloader for YouTube MP4/MP3 with a live Rich UI.**

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](./LICENSE)
[![Python](https://img.shields.io/badge/Python-3.8%2B-brightgreen)](#-requirements)

---

## ⚡ Jump To

- [🚀 30-Second Quick Start](#-30-second-quick-start)
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
git clone https://github.com/Thegamerprogrammer/CrystalMedia.git
cd CrystalMedia
python CrystalMedia.py
```

On first launch, CrystalMedia can prompt to install dependencies (`yt-dlp`, `rich`, `pyfiglet`, etc.) and bootstrap download folders automatically.

---

## 🎮 Interactive Walkthrough

When the app starts, the flow is designed to feel game-like and guided:

1. **Splash appears** (`CrystalMedia` logo + version)
2. **Main menu** opens (YouTube Video / YouTube Music / Spotify / Exit)
3. You choose:
   - Single item or playlist
   - URL
   - MP4 quality or MP3 bitrate
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

### 🎧 Spotify (Status: Limited/Broken)
Spotify mode is currently impacted by upstream API/auth changes in `spotdl` workflows.

Reference issue: https://github.com/spotDL/spotify-downloader/issues/2617

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
downloads/
├── YT VIDEO/
│   ├── Single/
│   └── Playlist/
├── YT MUSIC/
│   ├── Single/
│   └── Playlist/
└── SPOTIFY/
    ├── Single/
    └── Playlist/
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

- If a download looks complete but retries start, restart CrystalMedia to reload the latest logger class definitions.
- If terminal rendering looks off after a resize, return to the main menu and start the download again.

---

## 🤝 Contributing

PRs are welcome for UI polish, reliability improvements, and Spotify-mode recovery when upstream ecosystem changes stabilize.
