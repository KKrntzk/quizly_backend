from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated

from quiz_app.services import create_quiz_from_url
from .serializers import QuizCreateSerializer, QuizSerializer
from quiz_app.models import Quiz


class QuizListCreateView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        quizzes = Quiz.objects.filter(owner=request.user)
        serializer = QuizSerializer(quizzes, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def post(self, request):
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
