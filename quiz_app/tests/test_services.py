from django.test import TestCase

from quiz_app.services import extract_video_id, build_youtube_url


class ExtractVideoIdTest(TestCase):
    """Tests for the extract_video_id helper."""

    def test_standard_watch_url(self):
        """The id is extracted from a standard watch url."""
        url = "https://www.youtube.com/watch?v=dQw4w9WgXcQ"
        self.assertEqual(extract_video_id(url), "dQw4w9WgXcQ")

    def test_watch_url_without_www(self):
        """The id is extracted from a watch url without www."""
        url = "https://youtube.com/watch?v=dQw4w9WgXcQ"
        self.assertEqual(extract_video_id(url), "dQw4w9WgXcQ")

    def test_watch_url_with_timestamp(self):
        """Extra query params like a timestamp are ignored."""
        url = "https://www.youtube.com/watch?v=dQw4w9WgXcQ&t=42s"
        self.assertEqual(extract_video_id(url), "dQw4w9WgXcQ")

    def test_short_url(self):
        """The id is extracted from a youtu.be short url."""
        url = "https://youtu.be/dQw4w9WgXcQ"
        self.assertEqual(extract_video_id(url), "dQw4w9WgXcQ")

    def test_embed_url(self):
        """The id is extracted from an embed url."""
        url = "https://www.youtube.com/embed/dQw4w9WgXcQ"
        self.assertEqual(extract_video_id(url), "dQw4w9WgXcQ")

    def test_mobile_url(self):
        """The id is extracted from a mobile (m.) watch url."""
        url = "https://m.youtube.com/watch?v=dQw4w9WgXcQ"
        self.assertEqual(extract_video_id(url), "dQw4w9WgXcQ")

    def test_invalid_url_raises(self):
        """A non-YouTube url raises a ValueError."""
        url = "https://example.com/watch?v=dQw4w9WgXcQ"
        with self.assertRaises(ValueError):
            extract_video_id(url)

    def test_garbage_url_raises(self):
        """A garbage string raises a ValueError."""
        with self.assertRaises(ValueError):
            extract_video_id("not-a-url-at-all")


class BuildYoutubeUrlTest(TestCase):
    """Tests for the build_youtube_url helper."""

    def test_build_url(self):
        """A video id is turned into a normalized watch url."""
        result = build_youtube_url("dQw4w9WgXcQ")
        self.assertEqual(result, "https://www.youtube.com/watch?v=dQw4w9WgXcQ")
