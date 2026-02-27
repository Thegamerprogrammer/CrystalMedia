# 💎 CrystalMedia

CrystalMedia is an interactive terminal downloader for **YouTube video (MP4)** and **YouTube audio (MP3)**, with a Rich-powered live UI and organized output folders.

---

## 🚀 Quick Start

```bash
git clone https://github.com/Thegamerprogrammer/CrystalMedia.git
cd CrystalMedia
python CrystalMedia.py
```

On first run, CrystalMedia can prompt to install missing tools (`yt-dlp`, `rich`, `pyfiglet`, etc.) and create folders automatically.

---

## 🧭 Interactive Flow

When you run the app, you’ll see:

1. **CrystalMedia splash**
2. **Main menu** (YouTube MP4 / YouTube MP3 / Spotify / Exit)
3. **Mode prompts** (single vs playlist, quality/bitrate)
4. **Live download UI** with:
   - `Progress` panel (single progress bar + status)
   - `Download Log` panel (recent yt-dlp events)

### Keyboard / input behavior

- Use the prompts shown in terminal.
- During timeout prompts, press **any key** or **Enter** to continue immediately.
- If no input is provided, CrystalMedia auto-continues after timeout.

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

## ✅ Features

- YouTube MP4 download with selectable quality
- YouTube MP3 extraction with selectable bitrate
- Playlist + single-item support
- Retry logic + rotating user-agent strategy
- Fixed Rich live layout (progress + bounded logs)
- Auto folder bootstrap for clean output organization

---

## ⚠️ Spotify Status

Spotify mode is currently not reliable due to upstream authentication/developer-mode issues in the `spotdl` ecosystem.

Reference: https://github.com/spotDL/spotify-downloader/issues/2617

---

## 🛠 Requirements

- Python 3.8+
- Internet access
- FFmpeg (the app can help bootstrap it when missing)

---

## 📜 Legal Notice

Use this tool only for content you have permission to download.
You are responsible for complying with local copyright and platform terms.

---

## 📄 License

MIT
