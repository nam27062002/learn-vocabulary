# Localization Rule

## Quy tắc sử dụng Localization trong dự án

### 1. Sử dụng Context Processors thay vì Django i18n

**KHÔNG sử dụng:**
- `{% load i18n %}`
- `{% trans "text" %}`
- `gettext()`
- `django.mo` files

**SỬ DỤNG:**
- `vocabulary/context_processors.py` - File chính chứa tất cả translations
- `{{ manual_texts.key_name }}` trong templates
- `manual_texts` dictionary trong JavaScript

### 2. Cấu trúc Context Processors

File `vocabulary/context_processors.py` chứa:
- Dictionary `translations` với keys là language codes ('en', 'vi')
- Mỗi language có dictionary con với key-value pairs
- Key names nên có prefix mô tả chức năng (ví dụ: `study_mode`, `deck_name`)

### 3. Cách thêm text mới

1. **Thêm vào context_processors.py:**
```python
'en': {
    'new_text_key': 'English text',
    # ...
},
'vi': {
    'new_text_key': 'Tiếng Việt text',
    # ...
}
```

2. **Sử dụng trong template:**
```html
{{ manual_texts.new_text_key }}
```

3. **Sử dụng trong JavaScript:**
```javascript
STUDY_CFG.labels.new_text_key
```

### 4. Naming Convention

- Sử dụng snake_case cho key names
- Nhóm các key liên quan với comment
- Ví dụ:
```python
# Study Mode Selection
'study_mode': 'Study Mode',
'normal_study_by_decks': 'Normal Study (by Decks)',
'study_random_words': 'Study Random Words',
```

### 5. Lý do sử dụng Context Processors

1. **Đơn giản hơn**: Không cần compile .mo files
2. **Dễ maintain**: Tất cả translations ở một chỗ
3. **Flexible**: Có thể thêm logic phức tạp nếu cần
4. **Performance**: Không cần load external files

### 6. Files cần cập nhật khi thêm tính năng mới

1. `vocabulary/context_processors.py` - Thêm text labels
2. Templates - Sử dụng `{{ manual_texts.key }}`
3. JavaScript - Sử dụng `STUDY_CFG.labels.key`

### 7. Checklist khi thêm tính năng mới

- [ ] Thêm text labels vào context_processors.py (cả EN và VI)
- [ ] Cập nhật templates để sử dụng manual_texts
- [ ] Cập nhật JavaScript để sử dụng STUDY_CFG.labels
- [ ] Test với cả hai ngôn ngữ
- [ ] Không sử dụng Django i18n tags

### 8. Ví dụ hoàn chỉnh

**Context Processors:**
```python
'study_mode': 'Study Mode',
'normal_study_by_decks': 'Normal Study (by Decks)',
'study_random_words': 'Study Random Words',
```

**Template:**
```html
<h2>{{ manual_texts.study_mode }}</h2>
<span>{{ manual_texts.normal_study_by_decks }}</span>
```

**JavaScript:**
```javascript
const STUDY_CFG = {
    labels: {
        study_mode: "{{ manual_texts.study_mode }}",
        normal_study_by_decks: "{{ manual_texts.normal_study_by_decks }}",
    }
};
```

**Kết quả:**
- EN: "Study Mode", "Normal Study (by Decks)"
- VI: "Chế độ học tập", "Học bình thường (theo bộ thẻ)" 