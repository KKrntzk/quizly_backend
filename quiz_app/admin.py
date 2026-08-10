from django.contrib import admin

from quiz_app.models import Quiz, Question


class QuestionInline(admin.TabularInline):
    model = Question
    extra = 0


@admin.register(Quiz)
class QuizAdmin(admin.ModelAdmin):
    list_display = ["title", "owner", "created_at"]
    search_fields = ["title", "description"]
    list_filter = ["created_at"]
    inlines = [QuestionInline]


@admin.register(Question)
class QuestionAdmin(admin.ModelAdmin):
    list_display = ["question_title", "quiz", "answer"]
    search_fields = ["question_title"]
    list_filter = ["created_at"]
