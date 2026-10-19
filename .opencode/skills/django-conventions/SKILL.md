---
name: django-conventions
description: Project-specific Django conventions for the learn-vocabulary codebase (Django 5.2, allauth, hybrid custom i18n, services migration in progress). Use when writing or modifying Django models, views, templates, urls, signals, or API endpoints in this repo.
---

# Django Conventions — learn-vocabulary

## Environment

- Windows + venv. ALWAYS: `& .\.venv\Scripts\python.exe manage.py <command>` (plain `python` lacks Django).
- Verify with `manage.py check` after edits; test before claiming done.

## Layout map

- Apps: `vocabulary` (main domain: decks, flashcards, study, audio, AI services), `accounts` (custom user, avatars), `dictation` (dictation quiz feature), project config in `learn_english_project`.
- Page URLs in `vocabulary/urls.py`; JSON endpoints registered in `vocabulary/api_urls.py` (paths under `/api/`).
- Static: `static/css/<page>.css`, `static/js/<page>.js` (file name matches the template name when possible).

## During the active refactor (REFACTOR_PLAN.md)

- `views.py` is being split into `vocabulary/views/` package + `vocabulary/services/` for pure logic. New function-based views go in the matching package file; new business logic (no HTTP concerns) goes in services that return plain data.
- In `views/` package: re-export stable names from `vocabulary/views/__init__.py` so existing imports keep working during the transition.

## Models

- Study logic uses the custom difficulty-preview system (see `docs/DIFFICULTY_BASED_SYSTEM.md`), not SM-2 spaced repetition.
- `Flashcard.ease_factor` / `interval` are legacy and unused: never delete (separate migration task planned), never write new logic against them.

## Templates & frontend

- No new inline `<script>` logic or `<style>` blocks in templates. Put code in `static/js/`, `static/css/` using the page name.
- Pass Django context to JS via `data-*` attributes, never via string interpolation into scripts.
- Tailwind is loaded via CDN but the codebase is mixed Tailwind + custom CSS; match the style conventions of the file you are editing instead of introducing a new system.

## i18n (custom-hybrid, NOT Django i18n)

- `USE_I18N = False`. Strings are exposed through `vocabulary.context_processors.i18n_compatible_translations` (see `window.manual_texts` in templates).
- Never add `{% trans %}` / `{% blocktrans %}` tags, never re-enable `LocaleMiddleware`.

## API responses

- JSON endpoints return `{"success": true/false, ...}` and errors use `{"success": false, "error": "..."}` with proper HTTP status codes (400 for validation, 404/403 as appropriate); `@login_required` guards everything user-scoped.
- Report parsing routes through `vocabulary/word_details_service.py`; audio through `vocabulary/audio_service.py`; translations through the LLM/translation services with fallback chain. Match existing fallback patterns instead of adding new duplicates.

## Tests

- Suite baseline: full `manage.py test` must end with 0 failures. Feature tests in top-level `tests/test_<feature>.py`; app-level cases in `vocabulary/tests.py` or dedicated `tests_<service>.py` modules. Do not relocate tests unless the refactor plan says so.
- Do not write tests that assert on raw template substrings (like "JS contains string X") unless marking them clearly as convention pins; prefer endpoint/view tests.
