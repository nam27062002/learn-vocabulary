# LearnEnglish Vocabulary App

A Django-based vocabulary learning application that helps users build and study English vocabulary through flashcards with spaced repetition.

## Features

- **Flashcard Management**: Create, organize, and manage vocabulary flashcards
- **Deck Organization**: Group flashcards into themed decks
- **Spaced Repetition**: SM-2 algorithm implementation for optimized learning
- **Multi-language Support**: English/Vietnamese interface
- **Study Modes**: Multiple choice and typing practice
- **User Authentication**: Email-based with Google OAuth
- **Progress Tracking**: Statistics and learning analytics

## Tech Stack

- **Backend**: Django 5.1.7, Python
- **Database**: SQLite (development), PostgreSQL (production option)
- **Authentication**: django-allauth with Google OAuth
- **Frontend**: HTML/CSS/JS, Bootstrap
- **APIs**: Datamuse API, LanguageTool API, Unsplash API

## Deployment

This application is deployed on Render at:
https://learn-english-app-4o7h.onrender.com/

## Local Development

```bash
# Clone the repository
git clone <repository-url>
cd learn-english-project

# Create and activate virtual environment
python -m venv venv
source venv/bin/activate  # Linux/Mac
venv\Scripts\activate     # Windows

# Install dependencies
pip install -r requirements.txt

# Run migrations
python manage.py migrate

# Create superuser
python manage.py createsuperuser

# Run development server
python manage.py runserver
```

## Production Settings

For production deployment, the application uses `settings_minimal.py` which:
- Disables DEBUG mode
- Uses SQLite for simplicity
- Configures WhiteNoise for static files
- Sets appropriate security settings

## License

This project is licensed under the MIT License - see the LICENSE file for details.