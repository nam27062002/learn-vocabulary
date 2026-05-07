# Design Spec: Redesign trang `/add`

**Date:** 2026-05-07
**Status:** Approved

---

## Mục tiêu

Redesign giao diện trang `/add` (`add_flashcard.html`) để gọn gàng hơn, có visual hierarchy rõ ràng, UX tốt hơn (inline validation, loading state, toast). Giữ nguyên toàn bộ JavaScript và backend logic.

---

## Quyết định thiết kế

| Quyết định | Lựa chọn |
|---|---|
| Layout tổng thể | Card Grid — nhiều card xếp dọc (giống hiện tại, nhưng clean hơn) |
| Layout trong card | Image cố định bên phải (120×120px), fields text xếp dọc bên trái |
| Fields hiển thị mỗi card | Term + Phonetic (cùng hàng), EN def, VI def, Example sentence, Image |
| Bulk import toolbar | 2 nút: "⚡ Quick Add" (nổi bật) + "📚 Gợi ý" |
| Label nút gợi ý | "Gợi ý" — không có chữ "VSTEP" |
| Implementation approach | **B: HTML + CSS restructure** — viết lại HTML markup, tách CSS ra file riêng, giữ nguyên JS |

---

## Màu sắc & Design Tokens

Dùng lại CSS variables hiện tại của template, bổ sung thêm:

```css
:root {
  --primary:        #6a6cff;
  --primary-dark:   #5a5ce0;
  --primary-glow:   #6a6cff22;
  --bg-page:        #18182f;
  --bg-card:        #1e1e3a;
  --bg-input:       #14142a;
  --bg-subtle:      #24244a;
  --border:         #2e2e50;
  --border-muted:   #3a3a5c;
  --text:           #e0e0e0;
  --text-muted:     #7070a0;
  --text-faint:     #5a5a7a;
  --success:        #4caf50;
  --error:          #f44336;
  --warning:        #f59e0b;
  --radius-card:    14px;
  --radius-input:   8px;
  --radius-btn:     10px;
}
```

---

## Cấu trúc trang

```
page-wrap (max-width: 900px, centered)
├── .page-header
│   ├── tiêu đề "Thêm Flashcard" + subtitle
│   └── deck selector (bên phải)
├── .import-toolbar
│   ├── btn "⚡ Quick Add"   ← toggle quick-add-panel
│   └── btn "📚 Gợi ý"      ← trigger VSTEP suggestions API
├── .quick-add-panel (ẩn mặc định, toggle bởi Quick Add btn)
│   ├── textarea (pipe-separated hoặc newline)
│   ├── hint text
│   └── actions: Huỷ / Tạo cards →
├── .section-header ("Danh sách thẻ" + badge số lượng)
├── #flashcard-container (Sortable.js)
│   └── .flashcard × N
│       ├── .card-topbar (drag handle, số thứ tự, CEFR badge, trạng thái, nút xóa)
│       └── .card-body
│           ├── .card-fields (flex: 1)
│           │   ├── .field-row: [term (flex:1.6)] [phonetic (flex:1)]
│           │   ├── .field-group: EN definition
│           │   ├── .field-group: VI definition
│           │   └── .field-group: example sentence
│           └── .card-image-col (width: 120px)
│               ├── image box (120×120, upload/preview)
│               └── btn "⚡ Tạo ảnh AI"
├── btn "+ Thêm thẻ mới" (dashed border, full width)
└── .save-bar (sticky bottom)
    ├── status text: "X/Y thẻ hợp lệ"
    └── btn "Lưu tất cả" (gradient, loading state)
```

---

## Chi tiết từng component

### Page Header
- H1: gradient text `#6a6cff → #a855f7`
- Subtitle: màu `--text-muted`
- Deck selector: `<select>` styled, bên phải trên desktop, xuống dòng trên mobile

### Import Toolbar
- "⚡ Quick Add": nổi bật với `background: linear-gradient(--primary-glow)`, `border-color: #6a6cff66`
- "📚 Gợi ý": secondary style, `background: --bg-subtle`
- Toggle Quick Add panel bằng JS (hiện có sẵn)

### Quick Add Panel
- Ẩn mặc định (`display: none`), toggle mở bằng nút Quick Add
- Textarea: monospace font, min-height 72px
- Hint: "Phân cách bằng `|` hoặc xuống dòng"
- Buttons: Huỷ (secondary) + "Tạo cards →" (accent)

### Flashcard Card

**Visual states:**
- **Default**: border `1px solid --border`
- **Valid**: `border-left: 3px solid --success` (xanh lá)
- **Invalid**: `border-left: 3px solid --error` (đỏ)
- **Duplicate**: `border-left: 3px solid --warning` (vàng)

**Top bar:**
- Drag handle `⠿` (cursor: grab)
- Badge số thứ tự (`#1`, `#2`, ...)
- CEFR badge (A1–C2, mờ nếu chưa có)
- Trạng thái text: "✓ đủ thông tin" / "⚠ thiếu định nghĩa" / "⚠ từ đã tồn tại"
- Nút duplicate + nút xóa (danger hover)

**Fields:**
- Label: `0.7rem`, uppercase, letter-spacing, màu `--text-faint`
- Required marker: `*` màu đỏ
- Input/textarea: `background: --bg-input`, `border: 1px solid --border`, `border-radius: --radius-input`, `min-height: 44px`
- Focus: `border-color: --primary`
- Filled (auto-filled): màu chữ `#c0c0e0`
- Inline error: `0.72rem`, màu `--error`, hiện ngay dưới field (không đợi submit)
- Auto-fill badge: "⚡ tự động điền" — `0.68rem`, màu `--primary`, clickable

**Image column (120px fixed):**
- Image box: 120×120px, `border: 1.5px dashed --border-muted`, `border-radius: 10px`
- Khi có ảnh: hiển thị preview `object-fit: cover`
- Khi chưa có: icon placeholder + text "Upload ảnh"
- Hover: `border-color: --primary`
- Nút "⚡ Tạo ảnh AI": full-width, `background: --primary-glow`, `color: #8080ff`

### Add Card Button
- Full width, `border: 2px dashed --border-muted`, `border-radius: --radius-card`
- Hover: border và text chuyển sang primary color

### Save Bar (Sticky Bottom)
- `position: sticky; bottom: 0`
- Background: `--bg-page` + `border-top: 1px solid --border`
- Status text: "X/Y thẻ hợp lệ · N thẻ chưa đủ thông tin"
- Nút "Lưu tất cả": `background: linear-gradient(135deg, #6a6cff, #a855f7)`, bold, `min-height: 44px`
- **Loading state**: khi đang submit — nút disabled, text "Đang lưu..." + spinner, ngăn double-submit
- **Disabled state**: khi 0 thẻ valid — `opacity: 0.4`, `cursor: not-allowed`

### Toast Notification
- `position: fixed; top: 20px; right: 20px`
- Success: border `#4caf5088`, icon `✓` màu xanh
- Error: border `#f4433688`, icon `✕` màu đỏ
- Auto-dismiss sau 4 giây
- Slide-in animation từ phải

---

## Responsive

| Breakpoint | Thay đổi |
|---|---|
| `< 600px` | `.card-image-col` chuyển xuống dưới `.card-fields` (stack dọc); deck selector xuống hàng mới trong header |
| `< 400px` | `.field-row` (term + phonetic) chuyển thành stack dọc |
| Mọi kích thước | Tất cả inputs `min-height: 44px` |

---

## Keyboard UX
- `Tab` chuyển field tự nhiên (HTML tab order)
- `Enter` trong textarea: xuống dòng bình thường (không submit)
- Nút "Lưu tất cả" là `type="button"` — submit chỉ qua click hoặc focus + Enter trên nút đó

---

## File changes

| File | Thay đổi |
|---|---|
| `vocabulary/templates/vocabulary/add_flashcard.html` | Viết lại HTML markup; xóa `<style>` inline; thêm `<link>` đến `add_flashcard.css`; giữ nguyên tất cả JS và `id`/`name` attributes |
| `static/css/add_flashcard.css` | File mới — toàn bộ CSS của trang |

---

## Constraints (không thay đổi)
- Tất cả `id`, `name`, `data-*` attributes trên HTML elements giữ nguyên để JS selector không bị break
- Không thêm/sửa bất kỳ view, URL, API endpoint nào
- Không thay đổi JavaScript (kể cả inline script trong template)
- Sortable.js drag-and-drop vẫn hoạt động (giữ `id="flashcard-container"`)
