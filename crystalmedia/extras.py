"""Extras helpers: starfield animation and MP3 metadata enrichment."""

from __future__ import annotations

import json
import random
import re
import shutil
import threading
import time
import urllib.parse
import urllib.request
from pathlib import Path
from typing import Callable, Optional
from urllib.error import HTTPError, URLError

from mutagen.id3 import APIC, ID3, SYLT, TALB, TDRC, TIT2, TPE1, USLT, ID3NoHeaderError


class StarfieldBackground:
    """Projection-style ASCII starfield for full-terminal background rendering."""

    def __init__(self, width: Optional[int] = None, height: Optional[int] = None, star_count: int = 220):
        term = shutil.get_terminal_size(fallback=(120, 36))
        self.width = max(30, width or term.columns)
        self.height = max(12, height or term.lines)
        self.star_count = star_count
        self._lock = threading.Lock()
        self._running = False
        self._thread: Optional[threading.Thread] = None
        self._depth = max(self.width, self.height)
        self._bounds_x = max(10, self.width // 2)
        self._bounds_y = max(6, self.height // 2)
        self._stars = [self._new_star() for _ in range(self.star_count)]

    def _new_star(self):
        z = random.randint(1, self._depth)
        return {
            "x": random.randint(-self._bounds_x, self._bounds_x),
            "y": random.randint(-self._bounds_y, self._bounds_y),
            "z": z,
            "pz": z,
            "speed": random.choice([1, 1, 1, 2]),
        }

    def _refresh_terminal_size(self):
        term = shutil.get_terminal_size(fallback=(self.width, self.height))
        new_width = max(30, term.columns)
        new_height = max(12, term.lines)
        if new_width == self.width and new_height == self.height:
            return
        self.width = new_width
        self.height = new_height
        self._depth = max(self.width, self.height)
        self._bounds_x = max(10, self.width // 2)
        self._bounds_y = max(6, self.height // 2)
        self._stars = [self._new_star() for _ in range(self.star_count)]

    def start(self):
        if self._running:
            return
        self._running = True
        self._thread = threading.Thread(target=self._run, daemon=True)
        self._thread.start()

    def stop(self):
        self._running = False

    def _project(self, x: int, y: int, z: int):
        z = max(1, z)
        sx = int((x / z) * self._bounds_x + self._bounds_x)
        sy = int((y / z) * self._bounds_y + self._bounds_y)
        return sx, sy

    def _run(self):
        while self._running:
            with self._lock:
                self._refresh_terminal_size()
                for star in self._stars:
                    star["pz"] = star["z"]
                    star["z"] -= star["speed"]
                    if star["z"] <= 1:
                        star["x"] = random.randint(-self._bounds_x, self._bounds_x)
                        star["y"] = random.randint(-self._bounds_y, self._bounds_y)
                        star["z"] = self._depth
                        star["pz"] = self._depth
                        star["speed"] = random.choice([1, 1, 1, 2])
            time.sleep(1 / 60)

    def render(self) -> str:
        with self._lock:
            self._refresh_terminal_size()
            canvas = [[" " for _ in range(self.width)] for _ in range(self.height)]
            for star in self._stars:
                x, y = self._project(star["x"], star["y"], star["z"])
                px, py = self._project(star["x"], star["y"], star["pz"])
                if 0 <= px < self.width and 0 <= py < self.height:
                    canvas[py][px] = "."
                if 0 <= x < self.width and 0 <= y < self.height:
                    token = "+" if star["z"] < self._depth // 3 else "*" if star["z"] < self._depth // 2 else "."
                    canvas[y][x] = token
        return "\n".join("".join(row) for row in canvas)


def http_get_json(url: str, user_agents: list[str]):
    req = urllib.request.Request(url, headers={"User-Agent": random.choice(user_agents)})
    with urllib.request.urlopen(req, timeout=15) as resp:
        return json.loads(resp.read().decode("utf-8", errors="ignore"))


def http_get_bytes(url: str, user_agents: list[str]):
    req = urllib.request.Request(url, headers={"User-Agent": random.choice(user_agents)})
    with urllib.request.urlopen(req, timeout=20) as resp:
        return resp.read()


def fetch_lrclib_lyrics(title: str, artist: str, user_agents: list[str]):
    if not title:
        return None
    q_title = urllib.parse.quote(title)
    q_artist = urllib.parse.quote(artist or "")
    try:
        payload = http_get_json(f"https://lrclib.net/api/get?track_name={q_title}&artist_name={q_artist}", user_agents)
    except (HTTPError, URLError, TimeoutError, json.JSONDecodeError):
        return None

    unsynced = (payload.get("plainLyrics") or "").strip()
    synced_raw = (payload.get("syncedLyrics") or "").strip()
    synced_entries = []
    for line in synced_raw.splitlines():
        m = re.match(r"\[(\d{2}):(\d{2})(?:\.(\d{1,3}))?\]\s*(.*)", line.strip())
        if not m:
            continue
        mm, ss, frac, text = m.groups()
        millis = int(mm) * 60000 + int(ss) * 1000 + int((frac or "0").ljust(3, "0"))
        if text.strip():
            synced_entries.append((millis, text.strip()))

    return {"unsynced": unsynced, "synced": synced_entries}


def strip_vtt_timestamp(line: str) -> str:
    if "-->" in line:
        return ""
    if re.match(r"^\d+$", line.strip()):
        return ""
    return re.sub(r"<[^>]+>", "", line).strip()


def subtitle_lines_from_info(info: dict, user_agents: list[str]):
    subtitle_pool = {}
    subtitle_pool.update(info.get("subtitles") or {})
    subtitle_pool.update(info.get("automatic_captions") or {})
    for lang in ("en", "en-US", "en-GB"):
        tracks = subtitle_pool.get(lang) or []
        for track in tracks:
            sub_url = track.get("url")
            ext = (track.get("ext") or "").lower()
            if not sub_url:
                continue
            try:
                payload = http_get_bytes(sub_url, user_agents).decode("utf-8", errors="ignore")
            except (HTTPError, URLError, TimeoutError):
                continue
            if ext == "json3":
                try:
                    obj = json.loads(payload)
                except json.JSONDecodeError:
                    continue
                lines = []
                for event in obj.get("events", []):
                    text = "".join(seg.get("utf8", "") for seg in event.get("segs", []))
                    text = text.strip()
                    if text:
                        lines.append(text)
                if lines:
                    return "\n".join(lines)
            lines = [strip_vtt_timestamp(line) for line in payload.splitlines()]
            lines = [line for line in lines if line]
            if lines:
                return "\n".join(lines)
    return ""


def guess_mime_type(img_url: str) -> str:
    lowered = (img_url or "").lower()
    if ".png" in lowered:
        return "image/png"
    if ".webp" in lowered:
        return "image/webp"
    return "image/jpeg"


def write_mp3_tags(
    mp3_path: Path,
    info: dict,
    embed_extras: bool,
    user_agents: list[str],
    log: Optional[Callable[[str, str], None]] = None,
):
    if not mp3_path.exists() or mp3_path.suffix.lower() != ".mp3":
        return

    try:
        tags = ID3(mp3_path)
    except ID3NoHeaderError:
        tags = ID3()

    title = (info.get("track") or info.get("title") or "").strip()
    artist = (info.get("artist") or info.get("uploader") or info.get("channel") or "Unknown Artist").strip()
    album = (info.get("album") or info.get("playlist_title") or "Single").strip()
    date = (info.get("upload_date") or "")[:4]

    tags.delall("TIT2")
    tags.delall("TPE1")
    tags.delall("TALB")
    tags.delall("TDRC")
    tags.add(TIT2(encoding=3, text=title or mp3_path.stem))
    tags.add(TPE1(encoding=3, text=artist))
    tags.add(TALB(encoding=3, text=album))
    if date:
        tags.add(TDRC(encoding=3, text=date))

    if embed_extras:
        lyrics = fetch_lrclib_lyrics(title, artist, user_agents) or {"unsynced": "", "synced": []}
        unsynced = lyrics.get("unsynced", "").strip()
        synced = lyrics.get("synced", [])
        if not unsynced:
            unsynced = subtitle_lines_from_info(info, user_agents).strip()
            if unsynced and log:
                log("Using subtitles as lyrics fallback.", "warning")

        if unsynced:
            tags.delall("USLT")
            tags.add(USLT(encoding=3, lang="eng", desc="Lyrics", text=unsynced))
        if synced:
            sylt_payload = [(line, millis) for millis, line in synced]
            tags.delall("SYLT")
            tags.add(SYLT(encoding=3, lang="eng", format=2, type=1, desc="Synced Lyrics", text=sylt_payload))

        thumbnail = info.get("thumbnail")
        if thumbnail:
            try:
                image_data = http_get_bytes(thumbnail, user_agents)
                tags.delall("APIC")
                tags.add(APIC(encoding=3, mime=guess_mime_type(thumbnail), type=3, desc="Cover", data=image_data))
            except (HTTPError, URLError, TimeoutError):
                if log:
                    log("Cover art download failed; keeping audio without APIC.", "warning")

    tags.save(mp3_path)


def iter_downloaded_entries(info):
    if not isinstance(info, dict):
        return
    entries = info.get("entries")
    if isinstance(entries, list):
        for entry in entries:
            if isinstance(entry, dict):
                yield from iter_downloaded_entries(entry)
    else:
        yield info


def extract_entry_final_path(entry: dict):
    requested = entry.get("requested_downloads") or []
    if requested and isinstance(requested[0], dict):
        filepath = requested[0].get("filepath")
        if filepath:
            return Path(filepath)
    filename = entry.get("_filename")
    if filename:
        path = Path(filename)
        if path.suffix.lower() != ".mp3":
            path = path.with_suffix(".mp3")
        return path
    return None
