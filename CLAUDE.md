# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Commands

```bash
# Run development server
python manage.py runserver

# Apply migrations
python manage.py migrate

# Create new migrations after model changes
python manage.py makemigrations

# Run all tests
python manage.py test

# Run tests for a specific app
python manage.py test vocabulary
python manage.py test accounts

# Run a single test file
python manage.py test tests.test_favorites

# Create superuser
python manage.py createsuperuser

# Create the database cache table (required after fresh setup)
python manage.py createcachetable

# Collect static files
python manage.py collectstatic
```

## Environment Setup

The project uses `python-decouple` to load settings from a `.env` file. Required variables:

```
SECRET_KEY=
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1
EMAIL_HOST_USER=
EMAIL_HOST_PASSWORD=
DEFAULT_FROM_EMAIL=
SERVER_EMAIL=
GOOGLE_OAUTH_CLIENT_ID=
GOOGLE_OAUTH_CLIENT_SECRET=
```

## Architecture Overview

### Apps

- **`vocabulary/`** — Core app. Handles all flashcard/deck/study logic, statistics, and most views. This is where nearly all feature work lives.
- **`accounts/`** — Custom user model (`CustomUser` uses email as `USERNAME_FIELD`, no username). Custom allauth forms for login/signup/password reset.
- **`learn_english_project/`** — Django project config (settings, root URLs).

### URL Structure

- `/` — redirects to dashboard (authenticated) or login
- `/accounts/` — allauth auth routes (login, signup, OAuth, email confirm)
- `/profile/` — `accounts` app URLs (profile management)
- `/api/*` — JSON API endpoints (`vocabulary/api_urls.py`)
- All other page routes — `vocabulary/urls.py` (dashboard, study, decks, favorites, statistics)

### Key Models (`vocabulary/models.py`)

- **`Flashcard`** — Core entity. Each card belongs to a user and optionally a `Deck`. Has a **difficulty-based review system** (not SM-2 — legacy fields like `ease_factor`/`interval` are unused). Active fields: `difficulty_score` (0.0=Again, 0.33=Hard, 0.67=Good, 1.0=Easy), `times_seen_today`, `last_seen_date`.
- **`Definition`** — One-to-many with `Flashcard`. Stores English + Vietnamese definitions plus per-definition synonyms/antonyms.
- **`StudySession` / `StudySessionAnswer`** — Track individual study sessions and per-answer data.
- **`DailyStatistics` / `WeeklyStatistics`** — Aggregated stats updated via signals/utils.
- **`IncorrectWordReview`** — Tracks per-question-type errors for review targeting.
- **`FavoriteFlashcard` / `BlacklistFlashcard`** — User curation models; blacklisted cards are excluded from study sessions.

### Study System

Card selection during study uses a **difficulty-weighted random system** (`views.py` → `_get_next_card_enhanced`). Weights: Again=40%, New=35%, Hard=30%, Good=20%, Easy=10%. Cards are capped at `MAX_DAILY_REVIEWS=5` per day. A **learning queue** (`_get_learning_queue`) re-surfaces incorrect cards within the same session.

### External Services (`vocabulary/api_services.py`, `audio_service.py`, `word_details_service.py`, `cefr_service.py`)

- **Datamuse API** — word suggestions
- **LanguageTool API** — grammar checking
- **Unsplash API** — related images (`UNSPLASH_ACCESS_KEY` env var)
- **Google Translate** (`googletrans` + `deep-translator`) — Vietnamese translations
- **Audio** — fetched and stored via `audio_service.py`
- **CEFR levels** — auto-classified via `cefr_service.py`

### Caching

Uses Django's **database cache** (`cache_table`). Run `python manage.py createcachetable` on fresh setup. Cache helpers live in `vocabulary/cache_utils.py`. Timeouts are configured in `settings.CACHE_TIMEOUTS`.

### i18n

Django's i18n system is **disabled** (`USE_I18N = False`). A custom hybrid translation system is used via the `vocabulary.context_processors.i18n_compatible_translations` context processor. Do not add Django `{% trans %}` tags or re-enable `django.middleware.locale.LocaleMiddleware`.

### Tests

Tests are split between:
- `tests/` — top-level directory with feature-specific test files
- `vocabulary/tests.py` and `vocabulary/tests_enhanced_audio.py` — app-level tests

### Deployment

Deployed on Render. Production uses PostgreSQL (connection config is commented out in `settings.py` — uncomment and set env vars to switch from SQLite). Static files served via WhiteNoise.
