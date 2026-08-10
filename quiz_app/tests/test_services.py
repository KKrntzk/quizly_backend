from django.test import TestCase

from unittest.mock import patch, MagicMock
from django.contrib.auth import get_user_model

from quiz_app.services import (
    extract_video_id,
    build_youtube_url,
    strip_markdown_fences,
    generate_quiz_data,
    create_quiz_from_url,
)
from quiz_app.models import Quiz, Question

User = get_user_model()


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


class CreateQuizFromUrlTest(TestCase):
    """Tests for the create_quiz_from_url orchestration."""

    def setUp(self):
        """Create a user and a fake quiz data payload."""
        self.user = User.objects.create_user(
            username="pipelineuser",
            email="pipelineuser@mail.de",
            password="securepassword123",
        )
        self.fake_quiz_data = {
            "title": "Test Quiz",
            "description": "A short description.",
            "questions": [
                {
                    "question_title": "Question 1?",
                    "question_options": ["A", "B", "C", "D"],
                    "answer": "A",
                },
                {
                    "question_title": "Question 2?",
                    "question_options": ["W", "X", "Y", "Z"],
                    "answer": "Z",
                },
            ],
        }

    @patch("quiz_app.services.generate_quiz_data")
    @patch("quiz_app.services.transcribe_audio")
    @patch("quiz_app.services.download_audio")
    def test_creates_quiz_with_questions(
        self, mock_download, mock_transcribe, mock_generate
    ):
        """The pipeline creates a quiz with all its questions."""
        mock_download.return_value = "/tmp/fake/audio.mp3"
        mock_transcribe.return_value = "a transcript"
        mock_generate.return_value = self.fake_quiz_data

        url = "https://www.youtube.com/watch?v=dQw4w9WgXcQ"
        quiz = create_quiz_from_url(url, self.user)

        self.assertEqual(quiz.title, "Test Quiz")
        self.assertEqual(quiz.owner, self.user)
        self.assertEqual(quiz.questions.count(), 2)

    @patch("quiz_app.services.generate_quiz_data")
    @patch("quiz_app.services.transcribe_audio")
    @patch("quiz_app.services.download_audio")
    def test_normalizes_video_url(self, mock_download, mock_transcribe, mock_generate):
        """The stored video_url is normalized regardless of input format."""
        mock_download.return_value = "/tmp/fake/audio.mp3"
        mock_transcribe.return_value = "a transcript"
        mock_generate.return_value = self.fake_quiz_data

        url = "https://youtu.be/dQw4w9WgXcQ?t=42"
        quiz = create_quiz_from_url(url, self.user)

        self.assertEqual(quiz.video_url, "https://www.youtube.com/watch?v=dQw4w9WgXcQ")

    @patch("quiz_app.services.generate_quiz_data")
    @patch("quiz_app.services.transcribe_audio")
    @patch("quiz_app.services.download_audio")
    def test_question_data_is_stored_correctly(
        self, mock_download, mock_transcribe, mock_generate
    ):
        """Each question is stored with its options and answer."""
        mock_download.return_value = "/tmp/fake/audio.mp3"
        mock_transcribe.return_value = "a transcript"
        mock_generate.return_value = self.fake_quiz_data

        url = "https://www.youtube.com/watch?v=dQw4w9WgXcQ"
        quiz = create_quiz_from_url(url, self.user)

        first = quiz.questions.first()
        self.assertEqual(first.question_title, "Question 1?")
        self.assertEqual(first.question_options, ["A", "B", "C", "D"])
        self.assertEqual(first.answer, "A")
