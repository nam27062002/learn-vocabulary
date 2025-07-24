# Django i18n Migration Guide

## Overview

This guide explains how to migrate templates and JavaScript files from the legacy `manual_texts` system to Django's standard internationalization (i18n) system.

## Template Migration

### Step 1: Add i18n Load Tag

Add the i18n load tag at the top of your template:

```html
<!-- Add this at the top -->
{% load i18n %}
{% extends "base.html" %}
```

### Step 2: Replace manual_texts with trans Tags

**Before (Legacy):**
```html
<h1>{{ manual_texts.welcome_message }}</h1>
<p>{{ manual_texts.platform_description }}</p>
<button>{{ manual_texts.add_new_words }}</button>
```

**After (Django i18n):**
```html
<h1>{% trans "Welcome to LearnEnglish" %}</h1>
<p>{% trans "Your personal vocabulary learning platform" %}</p>
<button>{% trans "Add New Words" %}</button>
```

### Step 3: Handle Complex Translations

**For translations with variables:**
```html
<!-- Before -->
<p>{{ manual_texts.cards_updated }} {{ count }}</p>

<!-- After -->
{% blocktrans count counter=count %}
{{ counter }} card updated
{% plural %}
{{ counter }} cards updated
{% endblocktrans %}
```

**For translations with HTML:**
```html
<!-- Before -->
<p>{{ manual_texts.get_started_by }} <a href="#">{{ manual_texts.adding_flashcards }}</a></p>

<!-- After -->
{% blocktrans %}
Get started by <a href="#">adding some new flashcards</a>
{% endblocktrans %}
```

### Step 4: Update Form Labels and Placeholders

**Before:**
```html
<label>{{ manual_texts.email_address }}</label>
<input placeholder="{{ manual_texts.answer_placeholder }}">
```

**After:**
```html
<label>{% trans "Email address" %}</label>
<input placeholder="{% trans 'Type your answer...' %}">
```

## JavaScript Migration

### Current Hybrid System

The current system provides `window.manual_texts` with all translations:

```javascript
// This works in current hybrid system
console.log(window.manual_texts.console_welcome);
showMessage(window.manual_texts.saving);
```

### Future Django i18n Integration

When ready to migrate JavaScript:

```javascript
// Future approach using Django's JavaScript i18n
console.log(gettext("🎓 LearnEnglish App"));
showMessage(gettext("Saving..."));
```

### Updating JavaScript Files

**Before:**
```javascript
showMessage(window.manual_texts?.saving || 'Saving...', 'info');
```

**After (when migrating):**
```javascript
showMessage(gettext("Saving..."), 'info');
```

## Translation String Reference

### Common Strings

| Legacy Key | Django i18n String | Vietnamese |
|------------|-------------------|------------|
| `welcome_message` | `"Welcome to LearnEnglish"` | `"Chào mừng đến với LearnEnglish"` |
| `home` | `"Home"` | `"Trang chủ"` |
| `flashcards` | `"Flashcards"` | `"Thẻ từ vựng"` |
| `add_word` | `"Add Word"` | `"Thêm từ"` |
| `study` | `"Study"` | `"Học tập"` |
| `statistics` | `"Statistics"` | `"Thống kê"` |
| `dashboard` | `"Dashboard"` | `"Bảng điều khiển"` |

### Form Strings

| Legacy Key | Django i18n String | Vietnamese |
|------------|-------------------|------------|
| `email_address` | `"Email address"` | `"Địa chỉ email"` |
| `password` | `"Password"` | `"Mật khẩu"` |
| `sign_in` | `"Sign in"` | `"Đăng nhập"` |
| `sign_up` | `"Sign up"` | `"Đăng ký"` |
| `save` | `"Save"` | `"Lưu"` |
| `cancel` | `"Cancel"` | `"Hủy"` |

### Study Interface Strings

| Legacy Key | Django i18n String | Vietnamese |
|------------|-------------------|------------|
| `correct` | `"Correct"` | `"Đúng"` |
| `incorrect` | `"Incorrect"` | `"Sai"` |
| `check` | `"Check"` | `"Kiểm tra"` |
| `show_answer` | `"Show Answer"` | `"Hiện đáp án"` |
| `next_card` | `"Next Card →"` | `"Thẻ tiếp theo →"` |

## Template Migration Checklist

For each template file:

- [ ] Add `{% load i18n %}` at the top
- [ ] Replace all `{{ manual_texts.* }}` with `{% trans "..." %}`
- [ ] Test in both English and Vietnamese
- [ ] Verify all text displays correctly
- [ ] Check that language switching works
- [ ] Validate HTML structure is preserved

## JavaScript Migration Checklist

For each JavaScript file:

- [ ] Identify all uses of `window.manual_texts`
- [ ] Plan migration strategy (immediate or gradual)
- [ ] Update to use `gettext()` when ready
- [ ] Test dynamic language switching
- [ ] Verify all user interactions work

## Testing Your Migration

### 1. Visual Testing
```bash
python manage.py runserver
# Visit both /en/ and /vi/ versions
# Verify all text appears correctly
```

### 2. Language Switching
- Use the language dropdown in navigation
- Verify all migrated text changes language
- Check that URLs update correctly

### 3. JavaScript Console Testing
```javascript
// Test current translations
console.log(window.manual_texts);

// Test future i18n (when implemented)
console.log(gettext("Home"));
```

## Common Migration Issues

### Issue 1: Missing Translation
**Problem:** Text appears as the English key instead of translated text.

**Solution:** Check that the string exists in both `.po` files:
```bash
grep -n "Your string here" locale/*/LC_MESSAGES/django.po
```

### Issue 2: HTML Escaping
**Problem:** HTML tags appear as text instead of rendering.

**Solution:** Use `{% blocktrans %}` for HTML content:
```html
{% blocktrans %}
Click <a href="#">here</a> to continue
{% endblocktrans %}
```

### Issue 3: JavaScript Undefined
**Problem:** `window.manual_texts.key` is undefined.

**Solution:** Check that the key is included in the context processor's `js_translations`.

## Best Practices

### 1. Keep Strings Simple
```html
<!-- Good -->
{% trans "Save Changes" %}

<!-- Avoid -->
{% trans "Click the 'Save Changes' button to save your work" %}
```

### 2. Use Consistent Terminology
- Always use the same translation for the same concept
- Check existing translations before adding new ones

### 3. Test Both Languages
- Always test your changes in both English and Vietnamese
- Verify text fits in UI elements in both languages

### 4. Preserve Context
- Keep related strings together in templates
- Use comments to explain complex translations

## Getting Help

### 1. Check Existing Translations
Look in `locale/en/LC_MESSAGES/django.po` and `locale/vi/LC_MESSAGES/django.po` for existing strings.

### 2. Reference Documentation
- [Django Internationalization Documentation](https://docs.djangoproject.com/en/5.2/topics/i18n/)
- [Translation Template Tags](https://docs.djangoproject.com/en/5.2/topics/i18n/translation/#internationalization-in-template-code)

### 3. Test Your Changes
Always run the development server and test both languages before committing changes.

## Migration Priority

### High Priority (Complete First)
1. User-facing templates (study, flashcards, dashboard)
2. Authentication templates
3. Navigation and common UI elements

### Medium Priority
1. Admin interfaces
2. Error pages
3. Less frequently used features

### Low Priority
1. Debug/development templates
2. Internal tools
3. Documentation templates
