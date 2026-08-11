from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from quiz_app.models import Quiz, Question

User = get_user_model()


class QuizRetrieveViewTest(APITestCase):
    """Tests for GET /api/quizzes/{id}/."""

    def setUp(self):
        """Create two users, a quiz for each, and a question."""
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

        self.quiz = Quiz.objects.create(
            owner=self.user,
            title="My Quiz",
            description="My description",
            video_url="https://www.youtube.com/watch?v=aaaaaaaaaaa",
        )
        Question.objects.create(
            quiz=self.quiz,
            question_title="Question 1?",
            question_options=["A", "B", "C", "D"],
            answer="A",
        )
        self.other_quiz = Quiz.objects.create(
            owner=self.other_user,
            title="Other Quiz",
            description="Not mine",
            video_url="https://www.youtube.com/watch?v=bbbbbbbbbbb",
        )

        self.url = reverse("quiz-detail", kwargs={"pk": self.quiz.pk})
        self.other_url = reverse("quiz-detail", kwargs={"pk": self.other_quiz.pk})

    def _login(self):
        """Log in as our user so the test client stores the auth cookies."""
        self.client.post(
            self.login_url,
            {"username": "owner", "password": "securepassword123"},
        )

    def test_retrieve_own_quiz_success(self):
        """The owner can retrieve their own quiz with 200."""
        self._login()
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["id"], self.quiz.id)
        self.assertEqual(response.data["title"], "My Quiz")

    def test_retrieve_includes_questions(self):
        """The retrieved quiz includes its questions."""
        self._login()
        response = self.client.get(self.url)
        self.assertEqual(len(response.data["questions"]), 1)
        self.assertEqual(response.data["questions"][0]["question_title"], "Question 1?")

    def test_retrieve_other_users_quiz_forbidden(self):
        """Retrieving another user's quiz is forbidden with 403."""
        self._login()
        response = self.client.get(self.other_url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_retrieve_nonexistent_quiz_not_found(self):
        """Retrieving a non-existent quiz returns 404."""
        self._login()
        url = reverse("quiz-detail", kwargs={"pk": 9999})
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_retrieve_unauthenticated(self):
        """An unauthenticated request is rejected with 401."""
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


class QuizUpdateViewTest(APITestCase):
    """Tests for PATCH /api/quizzes/{id}/."""

    def setUp(self):
        """Create two users and a quiz for each."""
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

        self.quiz = Quiz.objects.create(
            owner=self.user,
            title="Original Title",
            description="Original description",
            video_url="https://www.youtube.com/watch?v=aaaaaaaaaaa",
        )
        self.other_quiz = Quiz.objects.create(
            owner=self.other_user,
            title="Other Quiz",
            description="Not mine",
            video_url="https://www.youtube.com/watch?v=bbbbbbbbbbb",
        )

        self.url = reverse("quiz-detail", kwargs={"pk": self.quiz.pk})
        self.other_url = reverse("quiz-detail", kwargs={"pk": self.other_quiz.pk})

    def _login(self):
        """Log in as our user so the test client stores the auth cookies."""
        self.client.post(
            self.login_url,
            {"username": "owner", "password": "securepassword123"},
        )

    def test_update_title_success(self):
        """The owner can update the title with 200."""
        self._login()
        response = self.client.patch(self.url, {"title": "New Title"})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["title"], "New Title")
        self.quiz.refresh_from_db()
        self.assertEqual(self.quiz.title, "New Title")

    def test_update_description_success(self):
        """The owner can update the description."""
        self._login()
        response = self.client.patch(self.url, {"description": "New description"})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["description"], "New description")

    def test_update_both_fields(self):
        """The owner can update title and description together."""
        self._login()
        response = self.client.patch(
            self.url,
            {"title": "Both New", "description": "Both changed"},
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["title"], "Both New")
        self.assertEqual(response.data["description"], "Both changed")

    def test_update_video_url_ignored(self):
        """The video_url is read-only and cannot be changed via PATCH."""
        self._login()
        original_url = self.quiz.video_url
        response = self.client.patch(
            self.url,
            {"video_url": "https://www.youtube.com/watch?v=hacked12345"},
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.quiz.refresh_from_db()
        self.assertEqual(self.quiz.video_url, original_url)

    def test_update_other_users_quiz_forbidden(self):
        """Updating another user's quiz is forbidden with 403."""
        self._login()
        response = self.client.patch(self.other_url, {"title": "Hacked"})
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_update_nonexistent_quiz_not_found(self):
        """Updating a non-existent quiz returns 404."""
        self._login()
        url = reverse("quiz-detail", kwargs={"pk": 9999})
        response = self.client.patch(url, {"title": "Nope"})
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_update_unauthenticated(self):
        """An unauthenticated update is rejected with 401."""
        response = self.client.patch(self.url, {"title": "Nope"})
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


class QuizDeleteViewTest(APITestCase):
    """Tests for DELETE /api/quizzes/{id}/."""

    def setUp(self):
        """Create two users and a quiz with a question for each scenario."""
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

        self.quiz = Quiz.objects.create(
            owner=self.user,
            title="My Quiz",
            description="My description",
            video_url="https://www.youtube.com/watch?v=aaaaaaaaaaa",
        )
        Question.objects.create(
            quiz=self.quiz,
            question_title="Question 1?",
            question_options=["A", "B", "C", "D"],
            answer="A",
        )
        self.other_quiz = Quiz.objects.create(
            owner=self.other_user,
            title="Other Quiz",
            description="Not mine",
            video_url="https://www.youtube.com/watch?v=bbbbbbbbbbb",
        )

        self.url = reverse("quiz-detail", kwargs={"pk": self.quiz.pk})
        self.other_url = reverse("quiz-detail", kwargs={"pk": self.other_quiz.pk})

    def _login(self):
        """Log in as our user so the test client stores the auth cookies."""
        self.client.post(
            self.login_url,
            {"username": "owner", "password": "securepassword123"},
        )

    def test_delete_own_quiz_success(self):
        """The owner can delete their quiz and receives 204."""
        self._login()
        response = self.client.delete(self.url)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(Quiz.objects.filter(pk=self.quiz.pk).exists())

    def test_delete_cascades_to_questions(self):
        """Deleting a quiz also deletes its questions."""
        self._login()
        quiz_pk = self.quiz.pk
        self.client.delete(self.url)
        self.assertFalse(Question.objects.filter(quiz_id=quiz_pk).exists())

    def test_delete_other_users_quiz_forbidden(self):
        """Deleting another user's quiz is forbidden with 403."""
        self._login()
        response = self.client.delete(self.other_url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertTrue(Quiz.objects.filter(pk=self.other_quiz.pk).exists())

    def test_delete_nonexistent_quiz_not_found(self):
        """Deleting a non-existent quiz returns 404."""
        self._login()
        url = reverse("quiz-detail", kwargs={"pk": 9999})
        response = self.client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_delete_unauthenticated(self):
        """An unauthenticated delete is rejected with 401."""
        response = self.client.delete(self.url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertTrue(Quiz.objects.filter(pk=self.quiz.pk).exists())
