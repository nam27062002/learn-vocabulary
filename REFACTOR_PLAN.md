# Refactor Plan — Learn Vocabulary

> Mục tiêu: giảm tech debt cấu trúc (backend) + hiện đại hóa frontend, **giữ nguyên hành vi** hiện tại.
> Nguyên tắc: mỗi phase là tile nhỏ độc lập, verify bằng `python manage.py test` sau mỗi tile.

## 1. Baseline hiện tại (ngày audit: 2026-10-19)

### Test suite
- **88 tests — 83 pass, 5 fail (stale tests, không phải bug thật):**
  1. `test_api_update_flashcard_with_language_prefix` — expect URL có prefix `/en/` chạy được → trả 404 (dự án đã tắt i18n, URL scheme đổi)
  2. `test_api_update_flashcard_without_language_prefix_fails` — ngược lại: expect 404 nhưng trả 200
  3. `test_quick_add_clearing_functionality` — assert JS chứa chuỗi `'Clearing existing cards'` (đã bị xóa khỏi template)
  4. `test_quick_add_confirmation_dialog` — assert `'showCancelButton: true'` (đã thay đổi)
  5. `test_quick_add_styling` — assert template chứa inline CSS `.quick-add-section` (CSS đã chuyển sang static)

- Comment trong test file thừa nhận: *"Tests assert template content that isn't there... treated as"debt to refactor later"* → 5 test này cần update lại theo trạng thái hiện tại để có baseline xanh sạch trước khi refactor.

### Hotspots backend
| File | Dòng | Vấn đề |
|---|---|---|
| `vocabulary/views.py` | ~2.355 | God-file: dashboard, study, decks, favorites, statistics, ~40 API endpoints, logic học tập — trộn lẫn |
| `vocabulary/context_processors.py` | 451 | Hệ i18n "hybrid" tự chế + các processor khác |
| `vocabulary/audio_service.py` | 433 | Service lớn gộp nhiều nguồn phát âm (Cambridge/YouTube/TTS) |
| `vocabulary/models.py` | 415 | OK về size, nhưng có legacy fields (ease_factor, interval) không dùng |

### Hotspots frontend
| File | Dòng | Vấn đề |
|---|---|---|
| `static/css/study.css` | 4.639 | CSS khổng lồ cho 1 trang |
| `static/js/study.js` | 4.201 | God-file JS: queue, timer, quiz-type, animation, audio… |
| `vocabulary/templates/vocabulary/blacklist_management.html` | 2.054 | HTML + inline style/script |
| `static/js/deck_detail.js` | 2.097 | God-file JS |
| `vocabulary/templates/vocabulary/deck_detail.html` | 1.911 | Inline JS (~1.000 dòng script nhúng) |
| `vocabulary/templates/vocabulary/add_flashcard.html` | 1.390 | Inline JS khổng lồ + Tailwind CDN |
| Template còn lại (6/10) | — | Đều có `<style>` nhúng → CSS đánh cắp lặp lại |

### Stack ghi nhận
- Django 5.2.1 / allauth 65.10 / gunicorn / whitenoise / SQLite (prod PostgreSQL chỉ commented).
- Tailwind nạp qua **CDN runtime** (`cdn.tailwindcss.com`) — tổn hiệu năng XSS/package khuyến nghị bỏ cho prod; cùng tồn tại với custom CSS → trùng lặp.
- 8/11 template có inline `<style>`; add_flashcard + deck_detail có inline `<script>` hàng trăm dòng.
- Không có linter/formatter cấu hình cho Python.

---

## 2. Chiến lược tổng thể

- **Behavior-preserving trước, delight sau**: mỗi tile chỉ đổi 1 thứ (cấu trúc **hoặc** hành vi, không cả hai cùng lúc).
- Thứ tự: nền móng (tests) → backend module hóa → templates/JS/CSS bom tách → vòng dọn cuối.
- Mỗi tile: 1 commit rõ ràng + `python manage.py test` xanh trước khi sang tile kế.

---

## 3. Các phase

### Phase 0 — Nền móng (~half day)
1. Backup/branch: `refactor/main` từ `main`; (SQLite → copy file).
2. **Cập nhật 5 stale tests** để suite chạy xanh sạch (theo hành vi hiện tại, không fake) → đây là baseline rej thai.
3. Thêm `ruff` vào requirements-dev + cấu hình nhẹ (pycodestyle sag цик rehearsal). Không reformat救人 trên 1 commit lớn — `ruff check --fix` thiết lập CI-prep.
4. Tạo `REFACTOR_LOG.md` — mỗi tile ghi 1 dòng.

**Verify:** `python manage.py test` → 0 fail.

### Phase 1 — Backend module hóa views.py (~2–3 tile)
Tách `views.py` (2.355 dòng) thành package `vocabulary/views/`:
```
vocabulary/views/
  __init__.py       # re-export, giữ import cũ tương thích
  dashboard.py
  study.py          # study view + _get_next_card_enhanced + learning queue
  decks.py
  flashcards.py     # CRUD flashcard + add_flashcard flow
  api/              # ~40 endpoint JSON tách theo domain
```
Đồng thời tách business logic thuần ra `services/`:
```
vocabulary/services/
  study_selection.py   # difficulty weighting, MAX_DAILY_REVIEWS
  session_service.py   # StudySession handling
  stats_service.py     # Daily/Weekly statistics aggregation
```
- Tile 1: extract `services/` (import trong views gọi lại — không đổi URL/hành vi)
- Tile 2: split `views.py` thành package (re-export giữ tương thích import)
- Tile 3: split `api_views.py` → `api/` theo domain

**Verify:** test xanh; `manage.py check`.

### Phase 2 — Models cleanup (~1 tile)
- Đánh dấu deprecated các field legacy (`ease_factor`, `interval`) — không xóa (cần migration + quyết định dữ), chỉ annotate + thêm TODO migration plan.
- Gom query helpers lặp trong views thành `managers.py` / `querysets.py` sau khi views tách xong.

### Phase 3 — Templates + inline assets (~3–4 tile)
- **Tile 3a**: tách inline `<style>` của 9 template thành `static/css/` riêng (partial giữ `{% static %}` link).
- **Tile 3b**: tách inline `<script>` của add_flashcard.html + deck_detail.html và template khác ra `static/js/` module + dùng `data-*` attributes để truyền URL từ Django.
- **Tile 3c**: tách component dùng chung thành partials (navbar, paginator, deck-card, card-form, audio-buttons, cefr-badge…) — giảm duplication giữa templates.

**Verify:** test + smoke các trang chính bằng browser.

### Phase 4 — CSS/JS modular hóa (~2–3 tile)
- **Tile 4a**: `study.css` 4.639 dòng → tách theo component (study-layout, study-card, study-sidebar…) hoặc giữ 1 file nhưng phân section schema tokens.
- **Tile 4b**: `study.js` 4.201 dòng → ES module: `study/queue.js, study/flash.js, study/listening.js, study/quiz.js, study/audio.js`; deck_detail.js tương tự.
- **Tile 4c**: đánh giá thay Tailwind CDN bằngać build CSS (dùng `bun` + `tailwindcss`) — chốt sau khi UI ổn vì ảnh hưởng prod pipeline.

### Phase 5 — Dọn dẹp cuối (~1 tile)
- Xóa đoạn code dead (legacy imports, commented blocks lớn).
- Điền `REFACTOR_LOG.md` total, chạy `ruff check` sạch.
- Sâu hơn: đưa các service Databricks/SD request vào 1 `llm_service.py` duy nhất nếu còn rải rác.

---

## 4. Kriteria hoàn tất (Definition of Done)

- [ ] `python manage.py test` — **88+ test pass, 0 fail**, không có skip mới (BREAKING stale tests phải update hay thay bằng behavior test thật).
- [ ] `views.py` không còn file >400 dòng.
- [ ] 0 template chứa inline `<script>` logic >50 dòng; 0 template chứa `<style>` khối quá phs lớn.
- [ ] `ruff check` sạch.
- [ ] Trang chủ các route chính smoke-test được nhanh (browser).

---

## 5. Điều chưa quyết (để báo)
- Tailwind build pipeline (thay CDN) — ảnh hưởng deploy Render; quyết ở Phase 4c.
- PostgreSQL activation hiện tại chưa thực hiện (chỉ commented) — có thể là tile riêng nằm ngoài scope refactor.
