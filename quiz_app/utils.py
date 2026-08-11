from urllib.parse import urlparse, parse_qs

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


def strip_markdown_fences(text):
    """Remove surrounding markdown code fences from a string if present."""
    cleaned = text.strip()
    if cleaned.startswith("```"):
        lines = cleaned.split("\n")
        lines = lines[1:]
        if lines and lines[-1].strip() == "```":
            lines = lines[:-1]
        cleaned = "\n".join(lines)
    return cleaned.strip()
