# AGENTS.md — Project Rules

Agent-facing rules for this repo. Architecture overview lives in `CLAUDE.md`.
The active refactor initiative lives in `REFACTOR_PLAN.md` (phases, tiles, DoD).
Historical rule docs live in `docs/` (`ENGLISH_COMMENT_RULE.md`, `COMPILE_CHECK_RULE.md`, …).

## Environment (Windows)

- System `python` does NOT have Django installed. ALWAYS run Python through the project venv:
  ```
  & .\.venv\Scripts\python.exe manage.py <command>
  ```
- Never edit or print `.env` values. Required keys are listed in `CLAUDE.md`.

## Verification commands

```
& .\.venv\Scripts\python.exe manage.py test            # full suite (target: run, 0 failures)
& .\.venv\Scripts\python.exe manage.py check           # project check / "compile" check
& .\.venv\Scripts\python.exe manage.py makemigrations  # after model changes only
& .\.venv\Scripts\python.exe manage.py migrate         # apply migrations
```

## Hard rules

1. **English comments only** — no Vietnamese in code comments (`docs/ENGLISH_COMMENT_RULE.md`).
2. **Check after every change** — run `manage.py check` once modifications are in; fix errors before adding more logic (`docs/COMPILE_CHECK_RULE.md`).
3. **Tests green before "done"** — run the test suite before claiming a task is complete; do not remove or skip failing tests to make them green, fix or properly update them.
4. **i18n is custom-hybrid, NOT Django i18n** — `USE_I18N = False`. Never add `{% trans %}` tags, never re-enable `LocaleMiddleware`. Strings go through `vocabulary.context_processors.i18n_compatible_translations`.
5. **Tests placement** — feature tests go in top-level `tests/test_<feature>.py`; app-edge cases in `vocabulary/tests.py` or the `tests_enhanced_audio.py` style modules. Do not move tests around unless the refactor plan says so.
6. **Legacy model fields are frozen** — `Flashcard.ease_factor` / `interval` are unused legacy. Do not delete; do not write new code against them. Migration removal is a planned, separate task.
7. **New dependencies** — must be pinned (exact versions) in `requirements.txt` with a short comment for the group. Do not install ad-hoc without adding them there.
8. **Templates** — no inline `<script>` logic over ~20 lines and no `<style>` blocks in page templates. Page JS goes to `static/js/<page>.js`, CSS to `static/css/<page>.css`. Pass Django-context values via `data-*` attributes, not string templating.
9. **Refactor protocol** — behavior-preserving refactors only; one concern per tile/commit; verify with tests both before and after; log one line per completed tile in `REFACTOR_LOG.md`. Never mix a feature change into a structural change.
10. **Commits** — do not commit unless the user explicitly asks; keep messages short and imperative.

## Refactor workflow rule

- Before each tile: baseline test run must be green.
- After each tile: tests green + `manage.py check` clean → log the tile in `REFACTOR_LOG.md`.
- Update `REFACTOR_PLAN.md` checkboxes when a phase/tile completes; add newly discovered work as new tiles instead of expanding scope silently.
