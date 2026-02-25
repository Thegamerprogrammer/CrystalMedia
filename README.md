# 💎 CrystalMedia

> A powerful YouTube & Spotify media downloader built in Python.\
> Powered by **yt-dlp** and **spotdl**.

CrystalMedia allows you to download videos, audio tracks, and playlists
--- single items or bulk --- directly to your machine through a clean
terminal interface with an organized folder structure.

------------------------------------------------------------------------

## ⚠️ Important Legal Notice

**This project is provided for educational and personal use only.**

Downloading copyrighted material without permission may violate
copyright laws in your country.

You are solely responsible for any legal consequences resulting from
misuse of this software.\
The author and contributors assume no liability for how this tool is
used.

------------------------------------------------------------------------

## ✨ Features

### 🎬 YouTube Support (Fully Working)

-   Download MP4 videos
-   Extract MP3 audio
-   Single video/track or full playlist support
-   Quality / bitrate selection
-   Automatic retry + user-agent rotation on rate limits

Organized output structure:

    downloads/
    ├── YT VIDEO/
    └── YT MUSIC/

------------------------------------------------------------------------

### 🎵 Spotify Support (Currently Broken -- Feb 2026)

-   MP3 downloads via `spotdl`
-   Single track or playlist support
-   ❌ Broken due to Spotify Developer Mode changes

Reference issue:\
https://github.com/spotDL/spotify-downloader/issues/2617

Potential future fixes:

-   Personal Spotify Developer App credentials (requires Spotify
    Premium)
-   Future `spotdl` authentication patch

------------------------------------------------------------------------

### 🖥️ Interface & System

-   Clean ASCII splash screen
-   Interactive menu system
-   Auto-installs missing dependencies on first run
-   Automatically downloads FFmpeg (via `spotdl`)
-   Persistent folder structure creation

------------------------------------------------------------------------

## 📊 Current Status (February 2026)

  Feature   Status
  --------- ------------------------------
  YouTube   ✅ Fully Functional
  Spotify   ❌ Broken (Dev Mode Changes)

To update `spotdl` when a fix is released:

``` bash
pip install --upgrade spotdl
```

------------------------------------------------------------------------

## 📦 Requirements

-   Python 3.8+
-   Internet connection
-   FFmpeg (auto-downloaded by `spotdl` on first run)

------------------------------------------------------------------------

## 🚀 Installation

``` bash
git clone https://github.com/Thegamerprogrammer/CrystalMedia.git
cd CrystalMedia
```

### (Optional) Create a Virtual Environment

``` bash
python -m venv venv
```

Activate it:

**Windows**

``` bash
venv\Scripts\activate
```

**Linux / macOS**

``` bash
source venv/bin/activate
```

------------------------------------------------------------------------

## ▶️ First Run

``` bash
python CrystalMedia.py
```

On first launch, the application will:

-   Install missing Python packages
-   Prompt to download FFmpeg (type `y` if asked)
-   Create the downloads/ folder structure

------------------------------------------------------------------------

## 🧭 Usage

``` bash
python CrystalMedia.py
```

Main Menu:

    1. YouTube Video (MP4)
    2. YouTube Music (MP3)
    3. Spotify Track/Playlist (Broken as of now)
    0. Exit Application

Follow the prompts --- paste URLs, choose single/playlist mode, and
select quality or bitrate.

------------------------------------------------------------------------

## 🤝 Contributing

Pull requests are welcome --- especially fixes for Spotify mode once
`spotdl` becomes usable again.

------------------------------------------------------------------------

## 📄 License

MIT License

You are solely responsible for any copyright violations or legal issues
that result from using this tool.\
The author and contributors are not liable for how this software is
used.
