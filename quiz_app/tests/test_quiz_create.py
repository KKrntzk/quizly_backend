from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from quiz_app.models import Quiz, Question

User = get_user_model()


class QuizCreateViewTest(APITestCase):
    """Tests for POST /api/quizzes/."""

    def setUp(self):
        """Create a user and provide login url, endpoint url and payload."""
        self.user = User.objects.create_user(
            username="creator",
            email="creator@mail.de",
            password="securepassword123",
        )
        self.login_url = reverse("login")
        self.url = reverse("quiz-list-create")
        self.payload = {"url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ"}
        self.fake_quiz_data = {
            "title": "Test Quiz",
            "description": "A short description.",
            "questions": [
                {
                    "question_title": "Question 1?",
                    "question_options": ["A", "B", "C", "D"],
                    "answer": "A",
                }
            ],
        }

    def _login(self):
        """Log in so the test client stores the auth cookies."""
        self.client.post(
            self.login_url,
            {"username": "creator", "password": "securepassword123"},
        )

    def _create_fake_quiz(self, owner):
        """Helper that builds a real quiz object like the pipeline would."""
        quiz = Quiz.objects.create(
            owner=owner,
            title=self.fake_quiz_data["title"],
            description=self.fake_quiz_data["description"],
            video_url=self.payload["url"],
        )
        for q in self.fake_quiz_data["questions"]:
            Question.objects.create(
                quiz=quiz,
                question_title=q["question_title"],
                question_options=q["question_options"],
                answer=q["answer"],
            )
        return quiz

    @patch("quiz_app.api.views.create_quiz_from_url")
    def test_create_quiz_success(self, mock_create):
        """A valid request returns 201 with the serialized quiz."""
        self._login()
        mock_create.side_effect = lambda url, user: self._create_fake_quiz(user)

        response = self.client.post(self.url, self.payload)

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data["title"], "Test Quiz")
        self.assertEqual(len(response.data["questions"]), 1)

    @patch("quiz_app.api.views.create_quiz_from_url")
    def test_create_quiz_sets_owner(self, mock_create):
        """The created quiz belongs to the authenticated user."""
        self._login()
        mock_create.side_effect = lambda url, user: self._create_fake_quiz(user)

        self.client.post(self.url, self.payload)

        quiz = Quiz.objects.first()
        self.assertEqual(quiz.owner, self.user)

    def test_create_quiz_unauthenticated(self):
        """An unauthenticated request is rejected with 401."""
        response = self.client.post(self.url, self.payload)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_create_quiz_invalid_payload(self):
        """A request without a url is rejected with 400."""
        self._login()
        response = self.client.post(self.url, {})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    @patch("quiz_app.api.views.create_quiz_from_url")
    def test_create_quiz_invalid_youtube_url(self, mock_create):
        """A ValueError from the pipeline results in a 400."""
        self._login()
        mock_create.side_effect = ValueError("bad url")

        response = self.client.post(self.url, self.payload)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    @patch("quiz_app.api.views.create_quiz_from_url")
    def test_create_quiz_pipeline_error(self, mock_create):
        """An unexpected pipeline error results in a 500."""
        self._login()
        mock_create.side_effect = Exception("gemini exploded")

        response = self.client.post(self.url, self.payload)
        self.assertEqual(response.status_code, status.HTTP_500_INTERNAL_SERVER_ERROR)
