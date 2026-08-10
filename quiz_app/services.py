from urllib.parse import urlparse, parse_qs
import os
import tempfile

import whisper
import yt_dlp

YOUTUBE_URL_TEMPLATE = "https://www.youtube.com/watch?v={video_id}"


def extract_video_id(url):
    """Extract the 11-character YouTube video id from various url formats."""
    parsed = urlparse(url)

    if "youtube.com" in parsed.netloc and parsed.path == "/watch":
        query = parse_qs(parsed.query)
        video_id = query.get("v", [None])[0]
        if video_id:
            return video_id

    if "youtu.be" in parsed.netloc:
        video_id = parsed.path.lstrip("/")
        if video_id:
            return video_id

    if "youtube.com" in parsed.netloc and parsed.path.startswith("/embed/"):
        video_id = parsed.path.split("/embed/")[1]
        if video_id:
            return video_id

    raise ValueError("Could not extract a valid YouTube video id from the url.")


def build_youtube_url(video_id):
    """Build a normalized YouTube watch url from a video id."""
    return YOUTUBE_URL_TEMPLATE.format(video_id=video_id)


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
