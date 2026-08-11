from django.contrib import admin

from quiz_app.models import Quiz, Question


class QuestionInline(admin.TabularInline):
    """Displays a quiz's questions inline within the quiz admin page."""

    model = Question
    extra = 0


@admin.register(Quiz)
class QuizAdmin(admin.ModelAdmin):
    """Admin configuration for quizzes with inline questions."""

    list_display = ["title", "owner", "created_at"]
    search_fields = ["title", "description"]
    list_filter = ["created_at"]
    inlines = [QuestionInline]


@admin.register(Question)
class QuestionAdmin(admin.ModelAdmin):
    """Admin configuration for individual quiz questions."""

    list_display = ["question_title", "quiz", "answer"]
    search_fields = ["question_title"]
    list_filter = ["created_at"]
