from django.contrib.auth import get_user_model
from django.test import TestCase

from quiz_app.models import Quiz, Question

User = get_user_model()


class QuizModelTest(TestCase):
    """Tests for the Quiz model."""

    def setUp(self):
        """Create a user and a quiz."""
        self.user = User.objects.create_user(
            username="quizowner",
            email="quizowner@mail.de",
            password="securepassword123",
        )
        self.quiz = Quiz.objects.create(
            owner=self.user,
            title="Python Basics",
            description="A quiz about Python fundamentals.",
            video_url="https://www.youtube.com/watch?v=example",
        )

    def test_quiz_is_created(self):
        """A quiz is created with the correct field values."""
        self.assertEqual(self.quiz.title, "Python Basics")
        self.assertEqual(self.quiz.owner, self.user)
        self.assertEqual(self.quiz.video_url, "https://www.youtube.com/watch?v=example")

    def test_quiz_timestamps_are_set(self):
        """Created and updated timestamps are set automatically."""
        self.assertIsNotNone(self.quiz.created_at)
        self.assertIsNotNone(self.quiz.updated_at)

    def test_quiz_str(self):
        """The string representation is the quiz title."""
        self.assertEqual(str(self.quiz), "Python Basics")

    def test_quiz_owner_related_name(self):
        """A user can access their quizzes via the related name."""
        self.assertIn(self.quiz, self.user.quizzes.all())


class QuestionModelTest(TestCase):
    """Tests for the Question model."""

    def setUp(self):
        """Create a user, a quiz and a question."""
        self.user = User.objects.create_user(
            username="quizowner",
            email="quizowner@mail.de",
            password="securepassword123",
        )
        self.quiz = Quiz.objects.create(
            owner=self.user,
            title="Python Basics",
            description="A quiz about Python fundamentals.",
            video_url="https://www.youtube.com/watch?v=example",
        )
        self.question = Question.objects.create(
            quiz=self.quiz,
            question_title="What is a list?",
            question_options=["A", "B", "C", "D"],
            answer="A",
        )

    def test_question_is_created(self):
        """A question is created with the correct field values."""
        self.assertEqual(self.question.question_title, "What is a list?")
        self.assertEqual(self.question.answer, "A")

    def test_question_options_stored_as_list(self):
        """The question options are stored and returned as a list."""
        self.assertEqual(self.question.question_options, ["A", "B", "C", "D"])
        self.assertEqual(len(self.question.question_options), 4)

    def test_question_quiz_related_name(self):
        """A quiz can access its questions via the related name."""
        self.assertIn(self.question, self.quiz.questions.all())

    def test_question_str(self):
        """The string representation is the question title."""
        self.assertEqual(str(self.question), "What is a list?")

    def test_cascade_delete(self):
        """Deleting a quiz also deletes its questions."""
        quiz_id = self.quiz.id
        self.quiz.delete()
        self.assertFalse(Question.objects.filter(quiz_id=quiz_id).exists())
