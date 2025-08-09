# LearnEnglish Vocabulary App

A Django-based vocabulary learning application that helps users build and study English vocabulary through flashcards with spaced repetition.

## 🚀 Quick Start

```bash
# Clone and setup
git clone <repository-url>
cd learn-vocabulary

# Install and run
pip install -r requirements.txt
python manage.py migrate
python manage.py runserver
```

## 📚 Documentation

Tài liệu chi tiết nằm trong **[docs/](docs/)**. Lưu ý: dự án đã loại bỏ i18n để tránh lỗi build khi bật tiếng Việt; giao diện dùng tiếng Anh mặc định.

## 🌟 Features

- **Flashcard Management**: Create, organize, and manage vocabulary flashcards
- **Deck Organization**: Group flashcards into themed decks
- **Spaced Repetition**: SM-2 algorithm implementation for optimized learning
- **Multi-language Support**: English/Vietnamese interface
- **Study Modes**: Multiple choice, typing, and dictation practice
- **Random Study**: Study random words from entire vocabulary
- **User Authentication**: Email-based with Google OAuth
- **Progress Tracking**: Statistics and learning analytics

## 🛠 Tech Stack

- **Backend**: Django 5.1.7, Python
- **Database**: SQLite (development), PostgreSQL (production option)
- **Authentication**: django-allauth with Google OAuth
- **Frontend**: HTML/CSS/JS, Tailwind CSS
- **APIs**: Datamuse API, LanguageTool API, Unsplash API

## 🌐 Deployment

This application is deployed on Render at:
https://learn-english-app-4o7h.onrender.com/

## 📖 Full Documentation

Xem **[docs/README.md](docs/README.md)** để biết hướng dẫn chi tiết về cài đặt và sử dụng.

---

*For detailed documentation, see [docs/](docs/) directory* 