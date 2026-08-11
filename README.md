# Quizly Backend

The backend for **Quizly** – an app that turns a YouTube video into a ready-to-use quiz. You send a YouTube URL, and the backend downloads the audio, transcribes it, and uses Google Gemini to generate a 10-question multiple-choice quiz from the content.

The API covers user authentication with cookie-based JWT, the full quiz-generation pipeline (download → transcription → AI generation), and standard CRUD operations for a user's own quizzes.

## Features & Tech Stack

- **Framework:** Django & Django REST Framework (DRF)
- **Authentication:** Cookie-based JWT (`djangorestframework-simplejwt`) — access and refresh tokens are stored in HttpOnly cookies, with refresh-token blacklisting on logout
- **Quiz Pipeline:** YouTube audio download (`yt-dlp`), speech-to-text transcription (OpenAI `whisper`), and quiz generation via the Google Gemini API (`google-genai`)
- **Data Model:** A `Quiz` owns many `Question` objects; answer options are stored in a `JSONField`, and deleting a quiz cascades to its questions
- **Permissions:** Object-level `IsOwner` permission so users can only access their own quizzes (correct `403` vs `404` behavior)
- **Testing:** pytest & pytest-django, run against an in-memory SQLite database with a fast password hasher; external services (yt-dlp, Whisper, Gemini) are mocked
- **Admin:** A clean Django Admin panel with quizzes and inline questions
- **Database:** SQLite (development)

## Prerequisites

In addition to Python, this project needs **FFmpeg** installed on your system (it is used by Whisper to process audio). This is a system dependency, not a pip package.

- **Windows:** `winget install --id Gyan.FFmpeg -e --source winget`
- **macOS:** `brew install ffmpeg`
- **Verify:** run `ffmpeg -version` in a new terminal — you should see version information.

You will also need a free **Google Gemini API key** from [ai.google.dev](https://ai.google.dev/).

> **Note on Whisper:** The first quiz generation downloads the Whisper model (~1.5 GB) automatically. This happens only once and may take a few minutes.

## Local Development Setup

Follow these steps to get the development server running locally.

> **Note:** On macOS/Linux you may need to use `python3` and `pip3` instead of `python` and `pip`, depending on your setup.

### 1. Clone the repository & enter the directory

```
git clone https://github.com/KKrntzk/quizly_backend
cd quizly_backend
```

### 2. Create the virtual environment

```
python -m venv .venv
```

### 3. Activate the virtual environment

**Windows (PowerShell)**

```
.venv\Scripts\Activate.ps1
```

**macOS / Linux**

```
source .venv/bin/activate
```

### 4. Install dependencies

```
python -m pip install --upgrade pip
pip install -r requirements.txt
```

### 5. Configure environment variables

The project requires a `.env` file for local configuration and secrets. Copy the provided template and fill in your local values:

**Windows (PowerShell)**

```
Copy-Item .env.template .env
```

**macOS / Linux**

```
cp .env.template .env
```

Open the newly created `.env` file and set the following variables:

- `SECRET_KEY` – a local development key (e.g. `SECRET_KEY=your-local-dev-key`)
- `DEBUG` – set to `True` for local development
- `GEMINI_API_KEY` – your Google Gemini API key from [ai.google.dev](https://ai.google.dev/)

### 6. Run database migrations

```
python manage.py migrate
```

### 7. Create an administrative superuser

To access the Django Admin interface, create a superuser account:

```
python manage.py createsuperuser
```

Follow the interactive prompts to set a username, email, and password.

### 8. Start the development server

```
python manage.py runserver
```

The server will be available locally at: http://127.0.0.1:8000/

## Running Tests

Tests run with pytest against an in-memory SQLite database (see `core/test_settings.py`). External services (YouTube download, transcription, and Gemini) are mocked, so tests run fast and offline.

```
pytest

pytest quiz_app

pytest --cov

pytest --cov --cov-report html
```

## API Endpoints (Documentation)

All quiz endpoints require authentication. Authentication is handled via HttpOnly cookies that are set automatically on login — no manual `Authorization` header is needed.

### Authentication

- `POST /api/register/` – Registers a new user (requires `username`, `email`, `password`, `confirmed_password`).
- `POST /api/login/` – Validates credentials and sets `access_token` and `refresh_token` cookies.
- `POST /api/logout/` – Blacklists the refresh token and clears the auth cookies. Permission: Authenticated.
- `POST /api/token/refresh/` – Issues a new `access_token` cookie using the `refresh_token` cookie.

### Quizzes

- `POST /api/quizzes/` – Creates a quiz from a YouTube URL by running the full pipeline. Permission: Authenticated.
- `GET /api/quizzes/` – Lists the authenticated user's own quizzes. Permission: Authenticated.
- `GET /api/quizzes/<int:pk>/` – Retrieves a single quiz with its questions. Permission: Owner only.
- `PATCH /api/quizzes/<int:pk>/` – Partially updates a quiz (only `title` and `description`). Permission: Owner only.
- `DELETE /api/quizzes/<int:pk>/` – Deletes a quiz and all its questions. Permission: Owner only.

### Permissions & Status Codes (Examples)

| Endpoint             | Action | Allowed For         | Expected Status Codes                                                         |
| -------------------- | ------ | ------------------- | ----------------------------------------------------------------------------- |
| `/api/quizzes/`      | POST   | Authenticated users | 201 (Created), 400 (Invalid URL), 401 (Unauthenticated), 500 (Pipeline Error) |
| `/api/quizzes/`      | GET    | Authenticated users | 200 (OK), 401 (Unauthenticated)                                               |
| `/api/quizzes/<pk>/` | GET    | Owner only          | 200 (OK), 401 (Unauthenticated), 403 (Not Owner), 404 (Not Found)             |
| `/api/quizzes/<pk>/` | PATCH  | Owner only          | 200 (Updated), 400 (Invalid Data), 401, 403 (Not Owner), 404 (Not Found)      |
| `/api/quizzes/<pk>/` | DELETE | Owner only          | 204 (No Content), 401, 403 (Not Owner), 404 (Not Found)                       |

## Project Structure

- `core/` – Project configuration: settings, test settings, and root URLs.
- `auth_app/` – Cookie-based JWT authentication: registration, login, logout, token refresh, and the custom cookie authentication class.
- `quiz_app/` – Quiz and Question models, the generation pipeline (`services.py`), API endpoints, the `IsOwner` permission, and the admin panel.

## The Quiz Generation Pipeline

When a quiz is created, the request runs through these steps in `quiz_app/services.py`:

1. **Normalize the URL** – extract the video ID from any YouTube URL format and rebuild a clean watch URL.
2. **Download audio** – `yt-dlp` downloads the best audio track into a temporary directory.
3. **Transcribe** – Whisper converts the audio to text.
4. **Generate** – the transcript is inserted into a prompt template and sent to Google Gemini, which returns the quiz as JSON.
5. **Parse & store** – markdown code fences are stripped, the JSON is parsed, and the quiz and its questions are saved to the database.
6. **Clean up** – the temporary audio file is always removed, even if a step fails.
