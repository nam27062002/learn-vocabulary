# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a Django-based vocabulary learning application that helps users build and study English vocabulary through flashcards with spaced repetition. The app uses a difficulty-based learning system instead of traditional spaced repetition algorithms.

## Development Commands

### Setup and Installation
```bash
pip install -r requirements.txt
python manage.py migrate
python manage.py runserver
```

### Database Operations
```bash
python manage.py makemigrations
python manage.py migrate
python manage.py createsuperuser
```

### Testing
```bash
python manage.py test
python manage.py test vocabulary
python manage.py test tests.test_specific_module
```

### Custom Management Commands
The app includes several custom management commands in `vocabulary/management/commands/`:
```bash
python manage.py analyze_study_algorithm
python manage.py diagnose_statistics  
python manage.py fix_statistics
python manage.py populate_statistics
python manage.py test_enhanced_audio_api
python manage.py test_statistics
```

### Static Files
```bash
python manage.py collectstatic
```

## Architecture Overview

### Apps Structure
- **vocabulary/**: Core app containing flashcards, decks, study sessions, and learning algorithms
- **accounts/**: Custom user authentication with email-based login and Google OAuth
- **learn_english_project/**: Main Django project settings and configuration

### Key Models
- **Flashcard**: Core vocabulary card with word, definitions, phonetics, images, and difficulty tracking
- **Deck**: Organization system for grouping related flashcards
- **StudySession**: Tracks individual study sessions and progress
- **WeeklyStatistics**: Aggregates learning statistics and progress tracking

### Learning System
The app uses a **difficulty-based system** instead of traditional SM-2 spaced repetition:
- Cards are shown based on difficulty scores (0.0=Again, 0.33=Hard, 0.67=Good, 1.0=Easy)
- Daily repetition limits prevent overwhelming users
- Progress is tracked through statistics and review counts

### External APIs
- **Datamuse API**: Word definitions, synonyms, antonyms
- **LanguageTool API**: Grammar and language checking
- **Unsplash API**: Related images for flashcards
- **Google Translate API**: Translation services

### Frontend Technology
- HTML/CSS/JavaScript with Tailwind CSS
- Audio management system for pronunciation
- Interactive study interfaces with multiple choice and typing modes
- Enhanced statistics dashboard

### Database
- Development: SQLite (`db.sqlite3`)
- Production: PostgreSQL (configured in `settings_production.py`)

### Authentication
- Email-based authentication using django-allauth
- Google OAuth integration
- Custom User model in accounts app

### Important Files
- `vocabulary/models.py`: Core data models and business logic
- `vocabulary/views.py`: Main application views and study logic  
- `vocabulary/api_services.py`: External API integrations
- `vocabulary/audio_service.py`: Audio handling and pronunciation features
- `vocabulary/statistics_utils.py`: Statistics calculation and tracking
- `static/js/study.js`: Frontend study session management
- `templates/vocabulary/study.html`: Main study interface

### Settings Configuration
- `settings.py`: Development settings
- `settings_production.py`: Production configuration
- `settings_minimal.py`: Minimal setup for testing

### Key Features
- Flashcard CRUD operations with rich media (images, audio)
- Deck-based organization system
- Difficulty-based spaced repetition learning
- Multi-modal study (multiple choice, typing, favorites)
- Progress tracking and statistics
- Random study mode across all vocabulary
- Audio pronunciation support
- Image associations for better memory retention

### Testing Structure
- Unit tests in `vocabulary/tests.py` and `vocabulary/tests_enhanced_audio.py`
- Integration tests in `tests/` directory
- Custom management command tests

### Development Notes
- i18n has been disabled to avoid build errors (USE_I18N = False)
- The project uses a hybrid translation system through context processors
- Media files are stored in `media/flashcard_images/`
- Static files are organized in `static/` with CSS, JS, and audio assets