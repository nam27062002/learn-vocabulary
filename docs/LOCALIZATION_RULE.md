# Localization Rules (Updated)

## New Django i18n System (Preferred)

### 1. Use Django's Standard i18n System

**RECOMMENDED (New System):**
- `{% load i18n %}` at the top of templates
- `{% trans "text" %}` for simple translations
- `{% blocktrans %}` for complex translations with variables/HTML
- `gettext()` in Python code
- `.po` and `.mo` files in `locale/` directory

**LEGACY SUPPORT (Being Phased Out):**
- `{{ manual_texts.key_name }}` in templates (still works)
- `window.manual_texts` in JavaScript (still works)
- `vocabulary/context_processors.py` (hybrid system)

### 2. New System Usage

**In Templates:**
```html
{% load i18n %}
<h1>{% trans "Welcome to LearnEnglish" %}</h1>
<p>{% trans "Your personal vocabulary learning platform" %}</p>

<!-- For complex translations -->
{% blocktrans count counter=cards %}
{{ counter }} card
{% plural %}
{{ counter }} cards
{% endblocktrans %}
```

**In Python Code:**
```python
from django.utils.translation import gettext as _

def my_view(request):
    message = _("Welcome to LearnEnglish")
    return render(request, 'template.html', {'message': message})
```

**In JavaScript (Current Hybrid System):**
```javascript
// Still works - uses hybrid system
console.log(window.manual_texts.console_welcome);

// Future approach (when fully migrated)
console.log(gettext("Welcome to LearnEnglish"));
```

### 3. Adding New Translations

1. **Add to .po files:**
```bash
# In locale/en/LC_MESSAGES/django.po
msgid "New Feature"
msgstr "New Feature"

# In locale/vi/LC_MESSAGES/django.po
msgid "New Feature"
msgstr "Tính năng mới"
```

2. **Use in templates:**
```html
{% trans "New Feature" %}
```

3. **Compile translations:**
```bash
python compile_messages.py  # Custom script
# or when gettext is available:
python manage.py compilemessages
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