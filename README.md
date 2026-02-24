# CrystalMedia
A YouTube & Spotify media downloader built in Python, powered by yt-dlp and spotdl.
Downloads videos, audio tracks, and playlists, single items or bulk, directly to your machine with a clean terminal interface.
Important legal notice
This tool is provided for educational and personal use only.
Downloading copyrighted material without permission may violate copyright laws in your country.
You are solely responsible for any legal consequences arising from misuse of this software.
The author and contributors assume no liability for how this tool is used.
Features

YouTube support (fully working)
MP4 video or MP3 audio
Single video/track or full playlist
Quality / bitrate selection
Automatic retry + user-agent rotation on rate limits
Organized folders: downloads/YT VIDEO / YT MUSIC

Spotify support (currently broken)
MP3 downloads via spotdl
Single track or playlist
BROKEN AS OF FEB 2026 DUE TO SPOTIFY'S DEV MODE CHANGES REFER: https://github.com/spotDL/spotify-downloader/issues/2617
Personal developer app credentials(with spotify premium) or a future spotdl patch may revive it

Clean ASCII splash & menu
Auto-installs missing dependencies on first run
Downloads FFmpeg automatically via spotdl
Persistent folder structure

Current Status (February 2026)

YouTube downloading → 100% functional
Spotify downloading → broken due to Spotify Dev Mode chanegs.
Update spotdl (pip install --upgrade spotdl) whenever the devs push a fix or workaround


Requirements

Python 3.8+
FFmpeg (automatically downloaded by spotdl on first run)
Internet connection

Installation
Bashgit clone https://github.com/Thegamerprogrammer/CrystalMedia.git
cd CrystalMedia
(Optional) virtual environment:
Bashpython -m venv venv
# Windows
venv\Scripts\activate
# Linux/Mac
source venv/bin/activate
Run once — it will auto-install yt-dlp & spotdl:
Bashpython CrystalMedia.py
First launch will:

Install missing packages
Download FFmpeg (answer 'y' to the prompt if asked)
Create the downloads/ folder structure

Usage
Bashpython crystalmedia.py
Menu:
Main Category Selection
  1. YouTube Video (MP4)
  2. YouTube Music (MP3)
  3. Spotify Track/Playlist (Broken as of now)
  0. Exit Application
Follow the prompts — paste URLs, choose single/playlist, pick quality/bitrate.
Spotify Note
Spotify mode uses spotdl in shared/default mode (no personal credentials required).
Due to Spotify's recent changes refer: https://github.com/spotDL/spotify-downloader/issues/2617, spotdl is unusable, which most certainly breaks spotify mode
Workarounds(Requires Spotify Premium):

Create your own Spotify developer app & add credentials (not implemented yet)
Wait for spotdl to add MusicBrainz fallback or new auth method

Until then, expect Spotify mode to be unreliable or completely broken.
YouTube mode works flawlessly.
Contributing
Pull requests welcome, especially fixes for Spotify mode once spotdl becomes usable again.
License
MIT License
You are solely responsible for any copyright violations or legal issues that result from using this tool.
The author and contributors are not liable for how this software is used.
