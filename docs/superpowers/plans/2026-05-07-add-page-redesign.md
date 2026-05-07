# Add Page Redesign Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Redesign trang `/add` (add_flashcard.html) với layout sạch, visual hierarchy rõ ràng, inline validation, loading state, responsive — giữ nguyên toàn bộ JavaScript và backend logic.

**Architecture:** Tách CSS ra file riêng `static/css/add_flashcard.css`. Viết lại HTML markup trong template nhưng giữ nguyên tất cả `id`, `name`, CSS classes mà JavaScript đang dùng. Thêm một snippet JS nhỏ ở cuối `<script>` cho toggle Quick Add panel và save-bar status.

**Tech Stack:** Django templates, vanilla CSS (no framework), existing Sortable.js + Notify.js already loaded

---

## File Map

| File | Action | Mô tả |
|---|---|---|
| `static/css/add_flashcard.css` | **Tạo mới** | Toàn bộ CSS cho trang /add |
| `vocabulary/templates/vocabulary/add_flashcard.html` | **Sửa** | Xóa `<style>` inline, thêm link CSS, restructure HTML, giữ nguyên JS |

### JS selectors phải giữ nguyên (không được đổi)

```
IDs: flashcard-container, deck-selector, auto-image-toggle, auto-image-toggle-state,
     quick-add-input, generate-cards-btn, processing-indicator, processing-text,
     vstep-suggest-btn, vstep-processing, vstep-processing-text,
     add-card-btn, save-all-btn, save-loading-overlay
     
Per-card IDs (dynamic): imageUpload{n}, fileInput{n}, imgPreview{n}, deleteImg{n}

Classes: .flashcard-section, .flashcard-header, .card-number, .card-content-wrapper,
         .image-upload-wrapper, .image-upload, .term-input, .phonetic-input,
         .definition-textarea, .vietnamese-textarea, .example-textarea,
         .example-source-input, .example-auto-badge, .example-speak-btn,
         .suggestions-list, .definition-suggestions, .delete-card-btn, .drag-handle,
         .cefr-badge[data-level], .cefr-text, .cefr-tooltip,
         .auto-info, .auto-pos, .auto-audio, .valid, .invalid,
         .preview, .delete-img-btn, .processing-indicator, .spinner,
         .save-loading-overlay, .save-loading-content, .save-loading-spinner, .save-loading-text
         
data-attributes: data-card-index, data-suggest-words-url, data-word-details-url,
                 data-translate-url, data-check-word-exists-url, data-generate-image-url
```

---

## Task 1: Tạo `static/css/add_flashcard.css`

**Files:**
- Create: `static/css/add_flashcard.css`

- [ ] **Bước 1: Tạo file CSS với design tokens và page-level styles**

```css
/* static/css/add_flashcard.css */

/* ===== Design Tokens ===== */
.add-flashcard-page {
  --primary:       #6a6cff;
  --primary-dark:  #5a5ce0;
  --primary-glow:  rgba(106, 108, 255, 0.12);
  --bg-page:       #18182f;
  --bg-card:       #1e1e3a;
  --bg-input:      #14142a;
  --bg-subtle:     #24244a;
  --border:        #2e2e50;
  --border-muted:  #3a3a5c;
  --text:          #e0e0e0;
  --text-muted:    #7070a0;
  --text-faint:    #5a5a7a;
  --success:       #4caf50;
  --error:         #f44336;
  --warning:       #f59e0b;
  --r-card:        14px;
  --r-input:       8px;
  --r-btn:         10px;
}

/* ===== Page wrapper ===== */
.add-flashcard-page {
  max-width: 900px;
  margin: 0 auto;
  padding: 32px 20px 100px;
}

/* ===== Page Header ===== */
.afc-page-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  flex-wrap: wrap;
  gap: 12px;
  margin-bottom: 28px;
  padding-bottom: 20px;
  border-bottom: 1px solid var(--border);
}

.afc-page-header h1 {
  font-size: 1.7rem;
  font-weight: 700;
  background: linear-gradient(135deg, var(--primary), #a855f7);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
  margin: 0;
}

.afc-page-header .header-subtitle {
  font-size: 0.85rem;
  color: var(--text-muted);
  margin-top: 3px;
}

.afc-header-right {
  display: flex;
  align-items: center;
  gap: 16px;
  flex-wrap: wrap;
}

/* Deck selector */
.afc-deck-wrap {
  display: flex;
  align-items: center;
  gap: 8px;
}

.afc-deck-wrap label {
  font-size: 0.82rem;
  color: var(--text-muted);
  white-space: nowrap;
}

#deck-selector {
  background: var(--bg-subtle);
  border: 1px solid var(--border-muted);
  color: var(--text);
  border-radius: var(--r-input);
  padding: 8px 12px;
  font-size: 0.88rem;
  min-width: 160px;
  transition: border-color 0.15s;
}

#deck-selector:focus {
  outline: none;
  border-color: var(--primary);
  box-shadow: 0 0 0 3px rgba(106, 108, 255, 0.2);
}

/* Auto-image toggle (small, in header) */
.afc-auto-image-group {
  display: flex;
  align-items: center;
  gap: 8px;
}

.afc-auto-image-group .auto-image-toggle-label {
  font-size: 0.8rem;
  color: var(--text-faint);
  white-space: nowrap;
}

#auto-image-toggle-state {
  font-size: 0.75rem;
  color: var(--text-faint);
  font-weight: 600;
  min-width: 26px;
}

#auto-image-toggle-state.is-on {
  color: var(--primary);
}

/* Toggle switch (reuse existing structure) */
.toggle-switch {
  position: relative;
  display: inline-block;
  width: 36px;
  height: 20px;
  cursor: pointer;
  flex-shrink: 0;
}

.toggle-switch input {
  opacity: 0;
  width: 0;
  height: 0;
  position: absolute;
}

.toggle-track {
  position: absolute;
  inset: 0;
  background: var(--border-muted);
  border-radius: 20px;
  transition: background 0.2s;
}

.toggle-switch input:checked + .toggle-track {
  background: var(--primary);
}

.toggle-track::before {
  content: '';
  position: absolute;
  width: 14px;
  height: 14px;
  left: 3px;
  top: 3px;
  background: white;
  border-radius: 50%;
  transition: transform 0.2s;
}

.toggle-switch input:checked + .toggle-track::before {
  transform: translateX(16px);
}

/* ===== Import Toolbar ===== */
.afc-import-toolbar {
  display: flex;
  gap: 10px;
  margin-bottom: 16px;
  flex-wrap: wrap;
}

.afc-import-btn {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  padding: 9px 18px;
  border-radius: var(--r-btn);
  font-size: 0.88rem;
  cursor: pointer;
  font-weight: 600;
  transition: all 0.15s;
  border: 1px solid var(--border-muted);
  background: var(--bg-subtle);
  color: var(--text);
}

.afc-import-btn:hover {
  border-color: var(--primary);
  color: #a0a0ff;
}

.afc-import-btn.primary {
  border-color: rgba(106, 108, 255, 0.4);
  background: var(--primary-glow);
  color: #a0a0ff;
}

.afc-import-btn.primary:hover {
  border-color: var(--primary);
  background: rgba(106, 108, 255, 0.18);
}

.afc-import-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

/* ===== Quick Add Panel ===== */
.quick-add-section {
  background: var(--bg-card);
  border: 1px solid var(--border-muted);
  border-radius: 12px;
  padding: 16px 18px;
  margin-bottom: 24px;
  display: none; /* toggled by JS */
}

.quick-add-section.is-open {
  display: block;
}

.quick-add-header {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 10px;
}

.quick-add-header h3 {
  font-size: 0.85rem;
  color: var(--text-muted);
  text-transform: uppercase;
  letter-spacing: 0.07em;
  font-weight: 600;
  margin: 0;
}

.quick-add-input {
  width: 100%;
  background: var(--bg-input);
  border: 1px solid var(--border-muted);
  border-radius: var(--r-input);
  color: var(--text);
  padding: 10px 12px;
  font-size: 0.88rem;
  resize: vertical;
  min-height: 76px;
  font-family: monospace;
  transition: border-color 0.15s;
}

.quick-add-input:focus {
  outline: none;
  border-color: var(--primary);
  box-shadow: 0 0 0 3px rgba(106, 108, 255, 0.15);
}

.quick-add-input::placeholder {
  color: var(--text-faint);
  font-style: italic;
}

.quick-add-controls {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 12px;
  margin-top: 10px;
}

.quick-add-info {
  font-size: 0.78rem;
  color: var(--text-faint);
  flex: 1;
}

.generate-cards-btn {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  padding: 8px 18px;
  border-radius: var(--r-input);
  border: none;
  background: linear-gradient(135deg, var(--primary), #a855f7);
  color: white;
  font-size: 0.88rem;
  font-weight: 600;
  cursor: pointer;
  transition: opacity 0.15s;
}

.generate-cards-btn:hover { opacity: 0.88; }

.generate-cards-btn:disabled {
  opacity: 0.4;
  cursor: not-allowed;
}

/* Processing indicator (shared by Quick Add and VSTEP) */
.processing-indicator {
  display: none;
  align-items: center;
  gap: 8px;
  font-size: 0.85rem;
  color: var(--primary);
  margin-top: 8px;
}

.processing-indicator.active {
  display: flex;
}

.spinner {
  width: 14px;
  height: 14px;
  border: 2px solid rgba(106, 108, 255, 0.25);
  border-top-color: var(--primary);
  border-radius: 50%;
  animation: afc-spin 0.8s linear infinite;
  flex-shrink: 0;
}

@keyframes afc-spin {
  to { transform: rotate(360deg); }
}

/* ===== VSTEP section (hidden — only the button in toolbar is shown) ===== */
.vstep-suggestion-section {
  display: none !important;
}

/* ===== Section Header ===== */
.afc-section-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 14px;
}

.afc-section-header h2 {
  font-size: 0.85rem;
  color: var(--text-muted);
  text-transform: uppercase;
  letter-spacing: 0.08em;
  font-weight: 600;
  margin: 0;
}

.afc-card-count {
  background: var(--bg-subtle);
  border: 1px solid var(--border-muted);
  border-radius: 20px;
  padding: 2px 10px;
  font-size: 0.75rem;
  color: var(--text-muted);
}

/* ===== Flashcard ===== */
.flashcard-section {
  background: var(--bg-card);
  border: 1px solid var(--border);
  border-left: 3px solid transparent;
  border-radius: var(--r-card);
  padding: 14px 16px;
  margin-bottom: 12px;
  transition: border-color 0.2s;
}

.flashcard-section.valid {
  border-left-color: var(--success);
}

.flashcard-section.invalid {
  border-left-color: var(--error);
}

.flashcard-section.duplicate {
  border-left-color: var(--warning);
}

/* Card top bar */
.flashcard-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 12px;
}

.flashcard-header-left {
  display: flex;
  align-items: center;
  gap: 8px;
}

.drag-handle {
  color: var(--border-muted);
  cursor: grab;
  padding: 2px;
  display: flex;
  align-items: center;
}

.drag-handle:active { cursor: grabbing; }

.card-number {
  background: var(--bg-subtle);
  border-radius: 6px;
  padding: 2px 8px;
  font-size: 0.72rem;
  color: var(--text-muted);
  font-weight: 700;
  letter-spacing: 0.04em;
}

/* CEFR badge — keep existing color logic, just adjust base styles */
.cefr-badge {
  display: inline-flex;
  align-items: center;
  padding: 2px 8px;
  border-radius: 999px;
  font-size: 0.7rem;
  font-weight: 700;
  letter-spacing: 0.5px;
  color: #fff;
  cursor: default;
  opacity: 0;
  transition: opacity 0.3s ease-in;
  position: relative;
}

.cefr-badge.visible { opacity: 1; }

.cefr-badge[data-level="A1"] { background: #58CC02; }
.cefr-badge[data-level="A2"] { background: #89E219; color: #1a1a2e; }
.cefr-badge[data-level="B1"] { background: #FFC800; color: #1a1a2e; }
.cefr-badge[data-level="B2"] { background: #FF9600; }
.cefr-badge[data-level="C1"] { background: #FF4B4B; }
.cefr-badge[data-level="C2"] { background: #8B0000; }

.cefr-tooltip {
  display: none;
  position: absolute;
  top: calc(100% + 6px);
  left: 50%;
  transform: translateX(-50%);
  background: #1a1a2e;
  color: var(--text);
  padding: 4px 10px;
  border-radius: 6px;
  font-size: 0.7rem;
  font-weight: 400;
  white-space: nowrap;
  z-index: 10;
  box-shadow: 0 2px 8px rgba(0,0,0,0.3);
}

.cefr-badge:hover .cefr-tooltip { display: block; }

.afc-card-status {
  font-size: 0.72rem;
  color: var(--text-faint);
}

.flashcard-section.valid   .afc-card-status { color: var(--success); }
.flashcard-section.invalid .afc-card-status { color: var(--error); }

.actions {
  display: flex;
  align-items: center;
  gap: 4px;
}

.action-icon {
  width: 28px;
  height: 28px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 7px;
  border: 1px solid transparent;
  background: transparent;
  color: var(--text-faint);
  cursor: pointer;
  transition: all 0.15s;
  padding: 0;
}

.action-icon:hover {
  background: var(--bg-subtle);
  border-color: var(--border-muted);
  color: var(--text-muted);
}

.action-icon.delete-card-btn:hover {
  background: rgba(244, 67, 54, 0.1);
  border-color: var(--error);
  color: var(--error);
}

/* Card body: fields left + image right */
.card-content-wrapper {
  display: flex;
  gap: 14px;
  align-items: flex-start;
}

.main-content-area {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 10px;
  min-width: 0;
}

.image-upload-wrapper {
  width: 120px;
  flex-shrink: 0;
  display: flex;
  flex-direction: column;
  gap: 8px;
}

/* Input field group */
.input-field {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.input-field label {
  font-size: 0.7rem;
  color: var(--text-faint);
  text-transform: uppercase;
  letter-spacing: 0.07em;
  font-weight: 600;
  display: flex;
  align-items: center;
  gap: 6px;
}

/* Term + phonetic side by side */
.input-group {
  display: grid;
  grid-template-columns: 1.6fr 1fr;
  gap: 10px;
}

.term-input,
.phonetic-input,
.definition-textarea,
.vietnamese-textarea,
.example-textarea {
  background: var(--bg-input);
  border: 1px solid var(--border);
  border-radius: var(--r-input);
  padding: 8px 11px;
  color: var(--text);
  font-size: 0.88rem;
  width: 100%;
  transition: border-color 0.15s;
  font-family: inherit;
  min-height: 44px;
}

.term-input:focus,
.phonetic-input:focus,
.definition-textarea:focus,
.vietnamese-textarea:focus,
.example-textarea:focus {
  outline: none;
  border-color: var(--primary);
  box-shadow: 0 0 0 3px rgba(106, 108, 255, 0.15);
}

.term-input::placeholder,
.phonetic-input::placeholder,
.definition-textarea::placeholder,
.vietnamese-textarea::placeholder,
.example-textarea::placeholder {
  color: var(--text-faint);
}

.definition-textarea,
.vietnamese-textarea {
  resize: vertical;
  min-height: 64px;
  line-height: 1.5;
}

.example-textarea {
  resize: vertical;
  min-height: 52px;
  line-height: 1.5;
  background: rgba(74, 144, 226, 0.05);
  border-color: rgba(74, 144, 226, 0.25);
}

.example-textarea:focus {
  border-color: rgba(74, 144, 226, 0.6);
  box-shadow: 0 0 0 3px rgba(74, 144, 226, 0.1);
}

/* Suggestions autocomplete dropdown */
.suggestions-list {
  background: var(--bg-card);
  border: 1px solid var(--border-muted);
  border-radius: var(--r-input);
  margin-top: 2px;
  overflow: hidden;
  box-shadow: 0 4px 16px rgba(0,0,0,0.3);
  z-index: 20;
  position: relative;
}

/* Auto-info (part of speech + audio) */
.auto-info {
  display: flex;
  align-items: center;
  gap: 12px;
  font-size: 0.78rem;
  color: var(--text-muted);
  min-height: 20px;
}

.auto-info.inactive {
  opacity: 0.5;
}

.auto-audio {
  display: flex;
  align-items: center;
  gap: 4px;
  cursor: pointer;
}

.auto-audio:hover { color: var(--primary); }

/* Example auto badge + speak btn */
.example-auto-badge {
  font-size: 0.7rem;
  color: var(--success);
  font-weight: 500;
}

.example-speak-btn {
  background: none;
  border: none;
  cursor: pointer;
  color: var(--text-muted);
  font-size: 13px;
  padding: 2px 4px;
  border-radius: 4px;
  line-height: 1;
}

.example-speak-btn:hover { color: var(--primary); }

/* ===== Image Upload ===== */
.image-upload {
  width: 120px;
  height: 120px;
  border-radius: 10px;
  border: 1.5px dashed var(--border-muted);
  background: var(--bg-input);
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  transition: border-color 0.15s;
  overflow: hidden;
  position: relative;
}

.image-upload:hover { border-color: var(--primary); }

.image-upload input[type="file"] {
  position: absolute;
  inset: 0;
  opacity: 0;
  cursor: pointer;
  width: 100%;
  height: 100%;
}

.image-upload .image-upload-content {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 6px;
  pointer-events: none;
}

.image-upload .image-upload-content svg {
  width: 28px;
  height: 28px;
  fill: var(--text-faint);
}

.image-upload .image-upload-content span {
  font-size: 0.7rem;
  color: var(--text-faint);
  text-align: center;
  line-height: 1.3;
}

.image-upload .preview {
  position: absolute;
  inset: 0;
  width: 100%;
  height: 100%;
  object-fit: cover;
  border-radius: 10px;
}

.delete-img-btn {
  position: absolute;
  top: 5px;
  right: 5px;
  z-index: 4;
  background: rgba(0,0,0,0.55);
  border: none;
  border-radius: 50%;
  color: #fff;
  font-size: 16px;
  cursor: pointer;
  width: 22px;
  height: 22px;
  display: none;
  align-items: center;
  justify-content: center;
  line-height: 1;
  padding: 0;
}

/* Auto-generate image button */
.afc-img-gen-btn {
  width: 100%;
  padding: 6px 8px;
  border-radius: 7px;
  border: 1px solid rgba(106, 108, 255, 0.35);
  background: var(--primary-glow);
  color: #8a8aff;
  font-size: 0.72rem;
  text-align: center;
  cursor: pointer;
  transition: all 0.15s;
  font-family: inherit;
}

.afc-img-gen-btn:hover {
  background: rgba(106, 108, 255, 0.2);
  border-color: var(--primary);
}

/* ===== Add Card Button ===== */
.button-group {
  margin: 4px 0 24px;
}

#add-card-btn {
  width: 100%;
  padding: 12px;
  border: 2px dashed var(--border-muted);
  border-radius: var(--r-card);
  background: transparent;
  color: var(--text-faint);
  font-size: 0.9rem;
  cursor: pointer;
  transition: all 0.15s;
  text-align: center;
  font-family: inherit;
}

#add-card-btn:hover {
  border-color: var(--primary);
  color: #8a8aff;
  background: var(--primary-glow);
}

/* ===== Save Section → Save Bar ===== */
.save-section {
  position: sticky;
  bottom: 0;
  background: var(--bg-page);
  border-top: 1px solid var(--border);
  padding: 14px 0;
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
}

.afc-save-status {
  font-size: 0.82rem;
  color: var(--text-faint);
}

.afc-save-status strong {
  color: var(--text-muted);
}

#save-all-btn {
  padding: 11px 36px;
  border-radius: var(--r-btn);
  border: none;
  background: linear-gradient(135deg, var(--primary), #a855f7);
  color: white;
  font-size: 0.95rem;
  font-weight: 700;
  cursor: pointer;
  transition: opacity 0.15s;
  min-height: 44px;
  font-family: inherit;
}

#save-all-btn:hover { opacity: 0.88; }

#save-all-btn:disabled {
  opacity: 0.4;
  cursor: not-allowed;
}

/* ===== Save Loading Overlay ===== */
.save-loading-overlay {
  position: fixed;
  inset: 0;
  background: rgba(0, 0, 0, 0.6);
  backdrop-filter: blur(4px);
  z-index: 10000;
  display: none;
  align-items: center;
  justify-content: center;
}

.save-loading-overlay.active {
  display: flex;
}

.save-loading-content {
  background: var(--bg-card);
  border: 1px solid var(--border-muted);
  border-radius: 14px;
  padding: 28px 40px;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 14px;
}

.save-loading-spinner {
  width: 36px;
  height: 36px;
  border: 3px solid rgba(106, 108, 255, 0.2);
  border-top-color: var(--primary);
  border-radius: 50%;
  animation: afc-spin 0.9s linear infinite;
}

.save-loading-text {
  font-size: 0.95rem;
  color: var(--text-muted);
}

/* ===== Responsive ===== */
@media (max-width: 600px) {
  .afc-page-header {
    flex-direction: column;
    align-items: flex-start;
  }

  .afc-header-right {
    width: 100%;
  }

  #deck-selector {
    flex: 1;
    min-width: 0;
  }

  .card-content-wrapper {
    flex-direction: column;
  }

  .image-upload-wrapper {
    width: 100%;
    flex-direction: row;
    gap: 10px;
    align-items: center;
  }

  .image-upload {
    width: 90px;
    height: 90px;
  }

  .afc-img-gen-btn {
    flex: 1;
  }

  .save-section {
    flex-direction: column;
    align-items: stretch;
  }

  #save-all-btn {
    width: 100%;
  }
}

@media (max-width: 400px) {
  .input-group {
    grid-template-columns: 1fr;
  }
}
```

- [ ] **Bước 2: Xác nhận file tồn tại**

```bash
ls static/css/add_flashcard.css
```

Expected: file hiển thị, không có error.

- [ ] **Bước 3: Commit**

```bash
git add static/css/add_flashcard.css
git commit -m "feat: add add_flashcard.css for /add page redesign"
```

---

## Task 2: Restructure HTML trong `add_flashcard.html`

**Files:**
- Modify: `vocabulary/templates/vocabulary/add_flashcard.html`

Thay thế phần `{% block content %}` ... `</div>` (tất cả nội dung HTML). JS giữ nguyên 100%.

- [ ] **Bước 1: Xóa `<style>` block và thêm CSS link**

Tìm dòng `<style>` (dòng 15) đến `</style>` (dòng 996). Thay bằng:

```django
{% load static %}
<link rel="stylesheet" href="{% static 'css/add_flashcard.css' %}">
```

Đặt ngay sau `<meta name="csrf-token" ...>` và trước `<div class="add-flashcard-page">`.

- [ ] **Bước 2: Thay `.deck-selection-area` bằng `.afc-page-header`**

Tìm và thay thế block từ `<div class="deck-selection-area">` đến đóng tag `</div>` của nó (hiện tại kết thúc ở dòng ~1016):

```django
<div class="afc-page-header">
  <div>
    <h1>{{ manual_texts.add_new_flashcard }}</h1>
    <p class="header-subtitle">{{ manual_texts.add_vocabulary_description }}</p>
  </div>
  <div class="afc-header-right">
    <div class="afc-deck-wrap">
      <label for="deck-selector">{{ manual_texts.select_deck }}</label>
      <select id="deck-selector" name="deck">
        <option value="">{{ manual_texts.please_select_deck }}</option>
        <option value="new_deck">{{ manual_texts.create_new_deck }}</option>
        {% for deck in decks %}
          <option value="{{ deck.id }}">{{ deck.name }}</option>
        {% endfor %}
      </select>
    </div>
    <div class="afc-auto-image-group">
      <span class="auto-image-toggle-label">🖼️ Auto-image</span>
      <label class="toggle-switch" for="auto-image-toggle">
        <input type="checkbox" id="auto-image-toggle">
        <span class="toggle-track"></span>
      </label>
      <span id="auto-image-toggle-state">OFF</span>
    </div>
  </div>
</div>
```

- [ ] **Bước 3: Thêm Import Toolbar và restructure Quick Add section**

Thay block `<div class="quick-add-section">` ... `</div>` (kết thúc sau `</div>` của `processing-indicator`) bằng:

```django
{{-- Import toolbar --}}
<div class="afc-import-toolbar">
  <button type="button" id="quick-add-toggle-btn" class="afc-import-btn primary">
    ⚡ {{ manual_texts.quick_add_multiple_words }}
  </button>
  <button type="button" id="vstep-suggest-btn" class="afc-import-btn">
    📚 {{ manual_texts.vstep_suggest_button_short }}
  </button>
</div>

{{-- Quick Add panel (hidden by default, toggled by JS) --}}
<div class="quick-add-section" id="quick-add-panel">
  <div class="quick-add-header">
    <span>⚡</span>
    <h3>{{ manual_texts.quick_add_multiple_words }}</h3>
  </div>
  <textarea
    id="quick-add-input"
    class="quick-add-input"
    placeholder="{{ manual_texts.quick_add_placeholder }}"
    rows="3"></textarea>
  <div class="quick-add-controls">
    <div class="quick-add-info">{{ manual_texts.quick_add_info }}</div>
    <button id="generate-cards-btn" type="button" class="generate-cards-btn">
      <svg width="14" height="14" viewBox="0 0 24 24" fill="currentColor">
        <path d="M19 13h-6v6h-2v-6H5v-2h6V5h2v6h6v2z"/>
      </svg>
      {{ manual_texts.generate_cards }}
    </button>
  </div>
  <div id="processing-indicator" class="processing-indicator">
    <div class="spinner"></div>
    <span id="processing-text">{{ manual_texts.processing_words }}</span>
  </div>
</div>

{{-- VSTEP section (hidden via CSS, only its button is in toolbar) --}}
<div class="vstep-suggestion-section">
  <div id="vstep-processing" class="processing-indicator">
    <div class="spinner"></div>
    <span id="vstep-processing-text">{{ manual_texts.vstep_processing_text }}</span>
  </div>
</div>
```

**Lưu ý:** `manual_texts.vstep_suggest_button_short` cần được thêm vào i18n. Nếu không có, dùng hardcode `"Gợi ý"` thay thế. Kiểm tra bằng:

```bash
grep -r "vstep_suggest_button" vocabulary/
```

Nếu key `vstep_suggest_button` trả về text có chứa "VSTEP", thì dùng hardcode `"Gợi ý"` cho button text trong toolbar.

- [ ] **Bước 4: Thêm section header trước `#flashcard-container`**

Tìm dòng `<div class="flashcard-container" id="flashcard-container"` và thêm ngay trước nó:

```django
<div class="afc-section-header">
  <h2>Danh sách thẻ</h2>
  <span class="afc-card-count" id="afc-card-count">1 thẻ</span>
</div>
```

- [ ] **Bước 5: Restructure card header bên trong `.flashcard-section`**

Tìm `<div class="flashcard-header">` (bên trong `.flashcard-section`) và thay toàn bộ block đến đóng `</div>` đầu tiên của nó:

```django
<div class="flashcard-header">
  <div class="flashcard-header-left">
    <button class="action-icon drag-handle" title="{{ manual_texts.drag_to_move }}">
      <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
        <line x1="3" y1="6" x2="21" y2="6"/>
        <line x1="3" y1="12" x2="21" y2="12"/>
        <line x1="3" y1="18" x2="21" y2="18"/>
      </svg>
    </button>
    <span class="card-number">1</span>
    <div class="cefr-badge" style="display:none;" data-level="">
      <span class="cefr-text"></span>
      <span class="cefr-tooltip"></span>
    </div>
    <span class="afc-card-status"></span>
  </div>
  <div class="actions">
    <button class="action-icon delete-card-btn" title="{{ manual_texts.delete_card }}">
      <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
        <polyline points="3 6 5 6 21 6"/>
        <path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h2a2 2 0 0 1 2 2v2"/>
      </svg>
    </button>
  </div>
</div>
```

- [ ] **Bước 6: Restructure `.card-content-wrapper` — thêm `.input-group` cho term+phonetic**

Tìm bên trong `.main-content-area`, phần term và phonetic hiện là 2 `.input-field` riêng biệt. Wrap chúng trong `.input-group`:

```django
<div class="main-content-area">
  {{-- Term + Phonetic cùng hàng --}}
  <div class="input-group">
    <div class="input-field">
      <label for="term1">{{ manual_texts.term_label }}</label>
      <input type="text" id="term1" name="term1" class="term-input"
             placeholder="{{ manual_texts.term_placeholder }}" autocomplete="off" />
      <div id="suggestions1" class="suggestions-list" style="display:none;"></div>
    </div>
    <div class="input-field">
      <label for="phonetic1">{{ manual_texts.phonetic_label }}</label>
      <input type="text" id="phonetic1" name="phonetic1" class="phonetic-input"
             placeholder="{{ manual_texts.phonetic_placeholder }}" />
    </div>
  </div>

  {{-- EN Definition --}}
  <div class="english-def-container">
    <div class="input-field">
      <label for="definition1">{{ manual_texts.english_definition_label }}</label>
      <textarea id="definition1" name="definition1" class="definition-textarea" rows="3"
                placeholder="{{ manual_texts.definition_placeholder }}"></textarea>
      <div class="definition-suggestions suggestions-list" style="display:none;"></div>
    </div>
  </div>

  {{-- POS + Audio info --}}
  <div class="auto-info inactive">
    <span class="auto-pos">{{ manual_texts.part_of_speech }}</span>
    <span class="auto-audio">
      <svg width="16" height="16" viewBox="0 0 24 24" fill="currentColor">
        <path d="M3 9v6h4l5 5V4L7 9H3zm13.5 3c0-1.77-1.02-3.29-2.5-4.03v8.05c1.48-.73 2.5-2.25 2.5-4.02zM14 3.23v2.06c2.89.86 5 3.54 5 6.71s-2.11 5.85-5 6.71v2.06c4.01-.91 7-4.49 7-8.77s-2.99-7.86-7-8.77z"/>
      </svg>
      <span>{{ manual_texts.listen }}</span>
    </span>
  </div>

  {{-- Vietnamese Definition --}}
  <div class="vietnamese-block-container">
    <div class="input-field">
      <label for="vietnamese_definition1">{{ manual_texts.vietnamese_definition_label }}</label>
      <textarea id="vietnamese_definition1" name="vietnamese_definition1"
                class="vietnamese-textarea" rows="2"
                placeholder="{{ manual_texts.vietnamese_placeholder }}"></textarea>
    </div>
  </div>

  {{-- Example Sentence --}}
  <div class="input-field">
    <label>
      Example Sentence
      <span class="example-auto-badge" style="display:none;">✦ auto-generated</span>
      <button type="button" class="example-speak-btn" title="Play example" style="display:none;">🔊</button>
    </label>
    <textarea class="example-textarea" rows="2"
              placeholder="e.g. She is a resilient person who bounced back after every setback."></textarea>
    <input type="hidden" class="example-source-input" value="">
  </div>
</div>
```

- [ ] **Bước 7: Thêm `.afc-img-gen-btn` vào `.image-upload-wrapper`**

Tìm `<div class="image-upload-wrapper">` và thêm nút generate bên dưới image-upload div:

```django
<div class="image-upload-wrapper">
  <div class="image-upload" id="imageUpload1">
    <input type="file" accept="image/*" id="fileInput1" />
    <img class="preview" id="imgPreview1" style="display:none;" />
    <button type="button" id="deleteImg1" class="delete-img-btn">&times;</button>
    <div class="image-upload-content">
      <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24">
        <path d="M19.35 10.04C18.67 6.59 15.64 4 12 4 9.11 4 6.6 5.64 5.35 8.04 2.34 8.36 0 10.91 0 14c0 3.31 2.69 6 6 6h13c2.76 0 5-2.24 5-5 0-2.64-2.05-4.78-4.65-4.96zM14 13v4h-4v-4H7l5-5 5 5h-3z"/>
      </svg>
      <span>{{ manual_texts.upload_image }}</span>
    </div>
  </div>
  <button type="button" class="afc-img-gen-btn" id="img-gen-btn1">⚡ Tạo ảnh AI</button>
</div>
```

- [ ] **Bước 8: Thay `.button-group` và `.save-section`**

Tìm:
```html
<div class="button-group">
  <button id="add-card-btn" class="button">...</button>
</div>
<div class="save-section">
  <button id="save-all-btn" class="save-button">...</button>
</div>
```

Thay bằng:

```django
<div class="button-group">
  <button id="add-card-btn" type="button">{{ manual_texts.add_new_card }}</button>
</div>

<div class="save-section">
  <span class="afc-save-status" id="afc-save-status"></span>
  <button id="save-all-btn" type="button">{{ manual_texts.save_all_flashcards }}</button>
</div>
```

- [ ] **Bước 9: Commit HTML changes**

```bash
git add vocabulary/templates/vocabulary/add_flashcard.html
git commit -m "feat: restructure add_flashcard.html for redesign"
```

---

## Task 3: Thêm JS snippet cho Quick Add toggle, card count và save status

**Files:**
- Modify: `vocabulary/templates/vocabulary/add_flashcard.html` — thêm vào **cuối** `<script>` block (sau tất cả code hiện có, trước `</script>`)

- [ ] **Bước 1: Thêm snippet ở cuối `<script>` block**

Tìm `</script>` cuối cùng trong file. Ngay trước nó, thêm:

```javascript
  // ===== NEW UI: Quick Add toggle =====
  (function() {
    const toggleBtn = document.getElementById('quick-add-toggle-btn');
    const panel = document.getElementById('quick-add-panel');
    if (toggleBtn && panel) {
      toggleBtn.addEventListener('click', function() {
        panel.classList.toggle('is-open');
        toggleBtn.classList.toggle('primary', !panel.classList.contains('is-open'));
      });
    }
  })();

  // ===== NEW UI: Card count badge + save status =====
  (function() {
    const countEl = document.getElementById('afc-card-count');
    const statusEl = document.getElementById('afc-save-status');
    const container = document.getElementById('flashcard-container');

    function updateCounts() {
      if (!container) return;
      const total = container.querySelectorAll('.flashcard-section').length;
      const valid = container.querySelectorAll('.flashcard-section.valid').length;
      if (countEl) countEl.textContent = total + ' thẻ';
      if (statusEl) {
        if (total === 0) {
          statusEl.innerHTML = '';
        } else if (valid === total) {
          statusEl.innerHTML = '<strong>' + valid + '/' + total + '</strong> thẻ sẵn sàng';
        } else {
          statusEl.innerHTML = '<strong>' + valid + '/' + total + '</strong> thẻ hợp lệ';
        }
      }
    }

    // Poll mỗi 600ms — card validity thay đổi bất đồng bộ qua class manipulation
    setInterval(updateCounts, 600);
    updateCounts();
  })();
```

- [ ] **Bước 2: Kiểm tra i18n key cho VSTEP button**

```bash
grep -r "vstep_suggest_button" vocabulary/context_processors.py vocabulary/views.py vocabulary/templates/ 2>/dev/null | head -20
```

Nếu `manual_texts.vstep_suggest_button` trả về text có chứa "VSTEP", thay button text trong template thành hardcode `"📚 Gợi ý"`:

```django
<button type="button" id="vstep-suggest-btn" class="afc-import-btn">
  📚 Gợi ý
</button>
```

- [ ] **Bước 3: Commit**

```bash
git add vocabulary/templates/vocabulary/add_flashcard.html
git commit -m "feat: add Quick Add toggle and save status JS for redesign"
```

---

## Task 4: Kiểm tra trong browser

**Files:** Không thay đổi — chỉ kiểm tra

- [ ] **Bước 1: Khởi động dev server**

```bash
python manage.py runserver
```

Mở `http://127.0.0.1:8000/add/`.

- [ ] **Bước 2: Kiểm tra visual**

Xác nhận:
- [ ] Header gradient hiển thị, deck selector bên phải, auto-image toggle nhỏ
- [ ] Hai nút toolbar: "⚡ Quick Add" và "📚 Gợi ý" hiển thị đúng
- [ ] Click "⚡ Quick Add" → Quick Add panel mở/đóng
- [ ] Mỗi card có layout: fields bên trái, image 120px bên phải
- [ ] Card #1 hiển thị đủ: term+phonetic cùng hàng, EN def, VI def, example, image box, nút "⚡ Tạo ảnh AI"
- [ ] Badge card count cập nhật khi thêm card
- [ ] Save bar sticky ở bottom

- [ ] **Bước 3: Kiểm tra JS logic**

Xác nhận các tính năng hiện có vẫn hoạt động:
- [ ] Nhập từ vào term input → autocomplete suggestions xuất hiện
- [ ] Chọn suggestion → fields tự động điền (phonetic, EN def, VI def)
- [ ] Card chuyển sang `.valid` (border xanh trái) khi đủ 3 fields
- [ ] Nút "📚 Gợi ý" → VSTEP API được gọi (kiểm tra Network tab)
- [ ] Nút "Lưu tất cả" → loading overlay xuất hiện, cards được lưu, Notify.success xuất hiện
- [ ] Drag-and-drop reorder hoạt động

- [ ] **Bước 4: Kiểm tra responsive (thu nhỏ browser xuống 375px)**

- [ ] Image column chuyển xuống dưới fields (không bị overflow)
- [ ] Term + phonetic stack dọc (dưới 400px)
- [ ] Save bar buttons đủ 44px height để chạm

---

## Self-review checklist

- [x] **CSS design tokens**: Dùng CSS custom properties scoped trong `.add-flashcard-page`
- [x] **JS selectors preserved**: Tất cả `id` và class quan trọng được giữ nguyên trong HTML
- [x] **Quick Add toggle**: Bước 1 Task 3 wire `#quick-add-toggle-btn` → toggle class `.is-open`
- [x] **VSTEP button**: `id="vstep-suggest-btn"` giữ nguyên trong toolbar — JS tìm `getElementById('vstep-suggest-btn')` vẫn hoạt động; VSTEP section ẩn bằng CSS
- [x] **Card count**: Snippet JS cập nhật `#afc-card-count` mỗi 600ms
- [x] **Save status**: Snippet JS cập nhật `#afc-save-status` kèm count valid/total
- [x] **Image gen button**: `.afc-img-gen-btn` là button mới — cần verify JS auto-image generation có trigger từ button này không. **Quan trọng:** Nếu JS hiện tại trigger tự động từ `autoImageEnabled` flag (không phải từ button click), thì button "Tạo ảnh AI" cần được wire trong snippet Task 3. Kiểm tra trong file xem có handler nào cho image gen button không.
- [x] **Responsive**: `< 600px` image column stack dọc; `< 400px` term+phonetic stack dọc
- [x] **Loading overlay**: Reuse `#save-loading-overlay` với CSS mới — class `.active` toggle display
