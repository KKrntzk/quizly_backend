import os
import tempfile
import json
import shutil

import whisper
import yt_dlp
from django.conf import settings
from google import genai

from quiz_app.utils import (
    extract_video_id,
    build_youtube_url,
    strip_markdown_fences,
)


def download_audio(url):
    """Download the audio track of a YouTube video and return the file path."""
    tmp_dir = tempfile.mkdtemp()
    tmp_filename = os.path.join(tmp_dir, "audio.%(ext)s")

    ydl_opts = {
        "format": "bestaudio/best",
        "outtmpl": tmp_filename,
        "quiet": True,
        "noplaylist": True,
    }

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=True)
        audio_path = ydl.prepare_filename(info)

    return audio_path


def transcribe_audio(audio_path):
    """Transcribe an audio file to text using Whisper."""
    model = whisper.load_model("turbo")
    result = model.transcribe(audio_path)
    return result["text"]


QUIZ_PROMPT_TEMPLATE = """Based on the following transcript, generate a quiz in valid JSON format.
The quiz must follow this exact structure:
{{
  "title": "Create a concise quiz title based on the topic of the transcript.",
  "description": "Summarize the transcript in no more than 150 characters. Do not include any quiz questions or answers.",
  "questions": [
    {{
      "question_title": "The question goes here.",
      "question_options": ["Option A", "Option B", "Option C", "Option D"],
      "answer": "The correct answer from the above options"
    }},
    ...
    (exactly 10 questions)
  ]
}}
Requirements:
- Each question must have exactly 4 distinct answer options.
- Only one correct answer is allowed per question, and it must be present in 'question_options'.
- The output must be valid JSON and parsable as-is (e.g., using Python's json.loads).
- Do not include explanations, comments, or any text outside the JSON.

Transcript:
{transcript}"""


def generate_quiz_data(transcript):
    """Generate quiz data as a Python dict from a transcript using Gemini."""
    client = genai.Client(api_key=settings.GEMINI_API_KEY)
    prompt = QUIZ_PROMPT_TEMPLATE.format(transcript=transcript)

    interaction = client.interactions.create(
        model="gemini-3.6-flash",
        input=prompt,
    )

    cleaned = strip_markdown_fences(interaction.output_text)
    return json.loads(cleaned)


def create_quiz_from_url(url, owner):
    """Run the full pipeline and persist a quiz for the given owner."""
    from quiz_app.models import Quiz, Question

    video_id = extract_video_id(url)
    normalized_url = build_youtube_url(video_id)

    audio_path = download_audio(normalized_url)

    try:
        transcript = transcribe_audio(audio_path)
        quiz_data = generate_quiz_data(transcript)
    finally:
        shutil.rmtree(os.path.dirname(audio_path), ignore_errors=True)

    quiz = Quiz.objects.create(
        owner=owner,
        title=quiz_data["title"],
        description=quiz_data.get("description", ""),
        video_url=normalized_url,
    )

    for question in quiz_data["questions"]:
        Question.objects.create(
            quiz=quiz,
            question_title=question["question_title"],
            question_options=question["question_options"],
            answer=question["answer"],
        )

    return quiz
