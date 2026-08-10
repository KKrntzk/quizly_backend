from django.test import TestCase

from unittest.mock import patch, MagicMock
from quiz_app.services import (
    extract_video_id,
    build_youtube_url,
    strip_markdown_fences,
    generate_quiz_data,
)


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


class StripMarkdownFencesTest(TestCase):
    """Tests for the strip_markdown_fences helper."""

    def test_plain_json_unchanged(self):
        """A string without fences is returned unchanged."""
        text = '{"title": "Test"}'
        self.assertEqual(strip_markdown_fences(text), '{"title": "Test"}')

    def test_strips_plain_fence(self):
        """A generic code fence is removed."""
        text = '```\n{"title": "Test"}\n```'
        self.assertEqual(strip_markdown_fences(text), '{"title": "Test"}')

    def test_strips_json_fence(self):
        """A json-labelled code fence is removed."""
        text = '```json\n{"title": "Test"}\n```'
        self.assertEqual(strip_markdown_fences(text), '{"title": "Test"}')

    def test_strips_fence_with_surrounding_whitespace(self):
        """Leading and trailing whitespace around fences is handled."""
        text = '  ```json\n{"title": "Test"}\n```  '
        self.assertEqual(strip_markdown_fences(text), '{"title": "Test"}')


class GenerateQuizDataTest(TestCase):
    """Tests for the generate_quiz_data function."""

    @patch("quiz_app.services.genai.Client")
    def test_returns_parsed_dict(self, mock_client_class):
        """A valid Gemini response is parsed into a Python dict."""
        mock_interaction = MagicMock()
        mock_interaction.output_text = (
            '```json\n{"title": "Quiz", "questions": []}\n```'
        )

        mock_client = MagicMock()
        mock_client.interactions.create.return_value = mock_interaction
        mock_client_class.return_value = mock_client

        result = generate_quiz_data("some transcript")

        self.assertEqual(result["title"], "Quiz")
        self.assertEqual(result["questions"], [])

    @patch("quiz_app.services.genai.Client")
    def test_invalid_json_raises(self, mock_client_class):
        """An unparseable Gemini response raises a JSONDecodeError."""
        import json

        mock_interaction = MagicMock()
        mock_interaction.output_text = "not valid json at all"

        mock_client = MagicMock()
        mock_client.interactions.create.return_value = mock_interaction
        mock_client_class.return_value = mock_client

        with self.assertRaises(json.JSONDecodeError):
            generate_quiz_data("some transcript")
