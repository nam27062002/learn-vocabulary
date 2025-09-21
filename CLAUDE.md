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
python manage.py load_cefr_wordlist
python manage.py populate_cefr_data
python manage.py update_all_cefr_levels
```

The `accounts/` app also includes utility commands:
```bash
python manage.py delete_user
python manage.py cleanup_avatars
```

### Database Sync Tools
The project includes specialized tools for database synchronization in the `tools/` directory:
```bash
cd tools
pip install -r requirements.txt
python sync_gui.py  # PyQt6 GUI for PostgreSQL ↔ SQLite sync
```

### Static Files
```bash
python manage.py collectstatic
```

### Environment and Development Setup
```bash
# Create .env file in project root with required variables:
# - SECRET_KEY: Django secret key
# - DEBUG: True/False for development/production
# - DATABASE_URL: PostgreSQL connection string (optional, defaults to SQLite)
# - ALLOWED_HOSTS: Comma-separated list of allowed hosts

# Django shell for debugging
python manage.py shell

# Database shell access
python manage.py dbshell

# Check for common issues
python manage.py check

# Load sample data (if available)
python manage.py loaddata db.json
```

## Architecture Overview

### Apps Structure
- **vocabulary/**: Core app containing flashcards, decks, study sessions, and learning algorithms
- **accounts/**: Custom user authentication with email-based login and Google OAuth
- **learn_english_project/**: Main Django project settings and configuration

### Key Models
- **Flashcard**: Core vocabulary card with word, definitions, phonetics, images, and difficulty tracking
- **Definition**: Related English and Vietnamese definitions for each flashcard
- **Deck**: Organization system for grouping related flashcards
- **StudySession**: Tracks individual study sessions and progress
- **StudySessionAnswer**: Individual answers within study sessions with response times
- **DailyStatistics**: Daily aggregated learning metrics for users
- **WeeklyStatistics**: Weekly aggregated learning statistics and progress tracking
- **IncorrectWordReview**: Tracks words that need additional review
- **FavoriteFlashcard**: User's favorite flashcards for targeted study
- **BlacklistFlashcard**: Cards excluded from study sessions

### Learning System
The app uses a **difficulty-based system** instead of traditional SM-2 spaced repetition:
- Cards are shown based on difficulty scores (0.0=Again, 0.33=Hard, 0.67=Good, 1.0=Easy)
- Daily repetition limits prevent overwhelming users
- Progress is tracked through statistics and review counts
- CEFR (Common European Framework of Reference) levels are used for vocabulary classification and filtering

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
- Development: SQLite (`db.sqlite3`) or PostgreSQL (configurable via environment)
- Production: PostgreSQL with connection pooling and SSL
- Database caching enabled using Django's database cache backend
- Comprehensive indexing for performance optimization

### Authentication
- Email-based authentication using django-allauth
- Google OAuth integration
- Custom User model in accounts app

### Important Files
- `vocabulary/models.py`: Core data models and business logic
- `vocabulary/views.py`: Main application views and study logic  
- `vocabulary/api_services.py`: External API integrations (Datamuse, LanguageTool)
- `vocabulary/audio_service.py`: Audio handling and pronunciation features
- `vocabulary/statistics_utils.py`: Statistics calculation and tracking
- `vocabulary/word_details_service.py`: Word lookup and definition services
- `vocabulary/cache_utils.py`: Caching utilities for performance optimization
- `vocabulary/context_processors.py`: Hybrid i18n translation system
- `accounts/models.py`: Custom User model with email-based authentication
- `static/js/study.js`: Frontend study session management
- `templates/vocabulary/study.html`: Main study interface

### Settings Configuration
- `learn_english_project/settings.py`: Main development settings with PostgreSQL configuration
- Environment variables configured via python-decouple in `.env` file

### Key Features
- Flashcard CRUD operations with rich media (images, audio)
- Deck-based organization system with user-specific collections
- Difficulty-based spaced repetition learning (not traditional SM-2)
- Multi-modal study (multiple choice, typing, favorites, random)
- Comprehensive progress tracking and statistics (daily/weekly aggregation)
- Random study mode across entire vocabulary
- Audio pronunciation support with multiple audio sources
- Image associations for better memory retention via Unsplash API
- Favorites and blacklist system for personalized learning
- Real-time word suggestions and spell checking
- Vietnamese-English translation integration

### Testing Structure
- Unit tests in `vocabulary/tests.py` and `vocabulary/tests_enhanced_audio.py`
- Integration tests in `tests/` directory
- Custom management command tests

### Development Notes
- i18n has been disabled to avoid build errors (USE_I18N = False)
- The project uses a hybrid translation system through context processors
- Media files are stored in `media/flashcard_images/`
- Static files are organized in `static/` with CSS, JS, and audio assets
- Environment variables managed via python-decouple for configuration
- Database connection pooling enabled for production performance
- Comprehensive caching system implemented for API responses and database queries
- Custom management commands available for data analysis and debugging
- Deployment: Render.com with PostgreSQL database
- Database sync tools available for local development and backup

### Project Structure
```
LearnEngish/
├── vocabulary/          # Core vocabulary app
├── accounts/           # Authentication and user management
├── learn_english_project/  # Django project settings
├── static/             # Static assets (CSS, JS, audio)
├── templates/          # HTML templates
├── media/              # User-uploaded files
├── tools/              # Database sync utilities
├── docs/               # Project documentation
├── debug/              # Debug documentation and utilities
└── tests/              # Integration tests
```

### Performance Optimizations
- Database indexing on frequently queried fields
- Caching layer for flashcards, study sessions, and API responses
- Connection pooling for database efficiency
- Static file compression and optimization

### Documentation Structure
- `/docs/`: Technical documentation and implementation guides
- `/debug/`: Debugging guides and issue resolution documentation
- `/.kiro/`: Feature specifications and design documents
- Individual `.md` files for specific features and fixes