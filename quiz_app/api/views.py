from rest_framework import status
from rest_framework.generics import RetrieveUpdateDestroyAPIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from quiz_app.models import Quiz
from quiz_app.services import create_quiz_from_url

from .permissions import IsOwner
from .serializers import QuizCreateSerializer, QuizSerializer


class QuizListCreateView(APIView):
    """List the user's quizzes or create a new one from a YouTube URL."""

    permission_classes = [IsAuthenticated]

    def get(self, request):
        """Return all quizzes owned by the authenticated user."""
        quizzes = Quiz.objects.filter(owner=request.user)
        serializer = QuizSerializer(quizzes, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def post(self, request):
        """Create a quiz from a YouTube URL via the generation pipeline."""
        serializer = QuizCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        url = serializer.validated_data["url"]

        try:
            quiz = create_quiz_from_url(url, request.user)
        except ValueError:
            return Response(
                {"detail": "Invalid YouTube URL."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        except Exception:
            return Response(
                {"detail": "Failed to generate quiz from the provided URL."},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

        output = QuizSerializer(quiz)
        return Response(output.data, status=status.HTTP_201_CREATED)


class QuizDetailView(RetrieveUpdateDestroyAPIView):
    """Retrieve, update or delete a single quiz owned by the user."""

    queryset = Quiz.objects.all()
    serializer_class = QuizSerializer
    permission_classes = [IsAuthenticated, IsOwner]
    http_method_names = ["get", "patch", "delete"]
