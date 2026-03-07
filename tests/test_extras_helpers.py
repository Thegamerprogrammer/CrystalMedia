import unittest
from pathlib import Path

from crystalmedia import extras


class TestExtrasHelpers(unittest.TestCase):
    def test_strip_vtt_timestamp(self):
        self.assertEqual(extras.strip_vtt_timestamp("00:00:01.000 --> 00:00:02.000"), "")
        self.assertEqual(extras.strip_vtt_timestamp("42"), "")
        self.assertEqual(extras.strip_vtt_timestamp("<c.colorE5E5E5>Hello</c>"), "Hello")

    def test_guess_mime_type(self):
        self.assertEqual(extras.guess_mime_type("https://x/img.png"), "image/png")
        self.assertEqual(extras.guess_mime_type("https://x/img.webp"), "image/webp")
        self.assertEqual(extras.guess_mime_type("https://x/img.jpg"), "image/jpeg")

    def test_fetch_lrclib_lyrics_parses_synced(self):
        original = extras.http_get_json
        try:
            extras.http_get_json = lambda *_args, **_kwargs: {
                "plainLyrics": "line a\nline b",
                "syncedLyrics": "[00:01.00]Hello\n[00:02.500]World",
            }
            result = extras.fetch_lrclib_lyrics("Song", "Artist", ["ua"])
        finally:
            extras.http_get_json = original

        self.assertEqual(result["unsynced"], "line a\nline b")
        self.assertEqual(result["synced"], [(1000, "Hello"), (2500, "World")])

    def test_iter_downloaded_entries_nested(self):
        info = {
            "entries": [
                {"_filename": "a.webm"},
                {"entries": [{"_filename": "b.m4a"}]},
            ]
        }
        entries = list(extras.iter_downloaded_entries(info))
        self.assertEqual(len(entries), 2)

    def test_extract_entry_final_path_prefers_requested_filepath(self):
        entry = {"requested_downloads": [{"filepath": "/tmp/demo.mp3"}], "_filename": "/tmp/demo.webm"}
        self.assertEqual(extras.extract_entry_final_path(entry), Path("/tmp/demo.mp3"))

    def test_extract_entry_final_path_derives_mp3(self):
        entry = {"_filename": "/tmp/demo.webm"}
        self.assertEqual(extras.extract_entry_final_path(entry), Path("/tmp/demo.mp3"))

    def test_starfield_auto_size_and_depth_token(self):
        field = extras.StarfieldBackground(width=40, height=10, star_count=5)
        self.assertEqual(field.width, 40)
        self.assertEqual(field.height, 10)
        self.assertTrue(all(star[3] in (1, 2) for star in field._stars))


if __name__ == "__main__":
    unittest.main()
