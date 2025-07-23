# Project Organization

## 📁 Cấu trúc thư mục

### Root Directory
```
learn-vocabulary/
├── README.md                 # Quick start guide
├── docs/                     # 📚 Tất cả documentation
├── vocabulary/               # Main Django app
├── accounts/                 # User authentication
├── learn_english_project/    # Django project settings
├── static/                   # Static files (CSS, JS)
├── staticfiles/              # Collected static files
├── templates/                # HTML templates
├── locale/                   # Django i18n (legacy)
├── media/                    # User uploaded files
├── requirements.txt          # Python dependencies
├── manage.py                 # Django management
└── db.sqlite3               # Database
```

### Documentation Structure
```
docs/
├── INDEX.md                  # 📋 Tổng quan tất cả tài liệu
├── README.md                 # 📖 Hướng dẫn chi tiết
├── LOCALIZATION_RULE.md      # 🌐 Quy tắc localization
├── RANDOM_STUDY_FEATURE.md   # 🎯 Tính năng Study Random Words
├── QUICK_ADD_FEATURE.md      # ⚡ Tính năng Quick Add
├── DROPDOWN_FIX.md           # 🔧 Sửa lỗi dropdown
├── FLASHCARD_UPDATE_FIX.md   # 🔧 Sửa lỗi flashcard
├── ENGLISH_COMMENT_RULE.md   # 📝 Quy tắc comment
├── COMPILE_CHECK_RULE.md     # ✅ Quy tắc kiểm tra
└── PROJECT_ORGANIZATION.md   # 📁 Cấu trúc project (file này)
```

## 🎯 Lợi ích của việc tổ chức lại

### ✅ Trước khi tổ chức:
- 8 file .md rải rác ở root
- Khó tìm documentation
- Project root lộn xộn
- Không có index tổng quan

### ✅ Sau khi tổ chức:
- Tất cả docs trong thư mục `docs/`
- File INDEX.md để tìm kiếm nhanh
- Root directory gọn gàng
- Dễ maintain và mở rộng

## 📝 Quy tắc đặt tên file

### Features:
- `FEATURE_NAME.md` (ví dụ: `RANDOM_STUDY_FEATURE.md`)
- Mô tả tính năng mới hoặc cải tiến

### Bug Fixes:
- `ISSUE_FIX.md` (ví dụ: `DROPDOWN_FIX.md`)
- Mô tả lỗi đã sửa và cách sửa

### Rules:
- `RULE_NAME.md` (ví dụ: `LOCALIZATION_RULE.md`)
- Quy tắc coding hoặc development

## 🔄 Workflow khi thêm documentation mới

1. **Tạo file .md** trong thư mục `docs/`
2. **Đặt tên** theo quy tắc đã định
3. **Cập nhật** `docs/INDEX.md` để thêm link
4. **Commit** với message mô tả rõ ràng

## 📋 Checklist khi thêm tính năng mới

- [ ] Implement tính năng
- [ ] Tạo documentation trong `docs/`
- [ ] Cập nhật `docs/INDEX.md`
- [ ] Test tính năng
- [ ] Commit changes

## 🎨 Formatting Guidelines

### Sử dụng emoji để phân loại:
- 📚 Documentation
- 🚀 Features
- 🔧 Bug Fixes
- 📝 Rules
- ✅ Checklist
- 🎯 Examples

### Cấu trúc file:
```markdown
# Title

## Tổng quan
Brief description

## Chi tiết
Detailed explanation

## Cách sử dụng
Usage instructions

## Files đã sửa đổi
List of changed files
```

## 🔗 Quick Access

- **Documentation Index**: [docs/INDEX.md](INDEX.md)
- **Localization Rules**: [docs/LOCALIZATION_RULE.md](LOCALIZATION_RULE.md)
- **Study Features**: [docs/RANDOM_STUDY_FEATURE.md](RANDOM_STUDY_FEATURE.md)

---

*Last updated: 2025-01-23* 