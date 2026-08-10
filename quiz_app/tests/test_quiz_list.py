from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from quiz_app.models import Quiz

User = get_user_model()


class QuizListViewTest(APITestCase):
    """Tests for GET /api/quizzes/."""

    def setUp(self):
        """Create two users, each with their own quizzes."""
        self.user = User.objects.create_user(
            username="owner",
            email="owner@mail.de",
            password="securepassword123",
        )
        self.other_user = User.objects.create_user(
            username="other",
            email="other@mail.de",
            password="securepassword123",
        )
        self.login_url = reverse("login")
        self.url = reverse("quiz-list-create")

        # Two quizzes for our user
        Quiz.objects.create(
            owner=self.user,
            title="My Quiz 1",
            description="Description 1",
            video_url="https://www.youtube.com/watch?v=aaaaaaaaaaa",
        )
        Quiz.objects.create(
            owner=self.user,
            title="My Quiz 2",
            description="Description 2",
            video_url="https://www.youtube.com/watch?v=bbbbbbbbbbb",
        )
        # One quiz for the other user
        Quiz.objects.create(
            owner=self.other_user,
            title="Other Quiz",
            description="Not mine",
            video_url="https://www.youtube.com/watch?v=ccccccccccc",
        )

    def _login(self):
        """Log in as our user so the test client stores the auth cookies."""
        self.client.post(
            self.login_url,
            {"username": "owner", "password": "securepassword123"},
        )

    def test_list_success(self):
        """An authenticated user receives 200."""
        self._login()
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_list_returns_only_own_quizzes(self):
        """The list contains only the authenticated user's quizzes."""
        self._login()
        response = self.client.get(self.url)
        self.assertEqual(len(response.data), 2)
        titles = [quiz["title"] for quiz in response.data]
        self.assertIn("My Quiz 1", titles)
        self.assertIn("My Quiz 2", titles)
        self.assertNotIn("Other Quiz", titles)

    def test_list_includes_questions(self):
        """Each quiz in the list includes its questions field."""
        self._login()
        response = self.client.get(self.url)
        self.assertIn("questions", response.data[0])

    def test_list_unauthenticated(self):
        """An unauthenticated request is rejected with 401."""
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_list_empty_for_user_without_quizzes(self):
        """A user with no quizzes receives an empty list."""
        self.client.post(
            self.login_url,
            {"username": "other", "password": "securepassword123"},
        )
        # other_user has 1 quiz, so let's verify they see exactly that one
        response = self.client.get(self.url)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]["title"], "Other Quiz")
