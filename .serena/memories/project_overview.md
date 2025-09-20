# LearnEnglish - Project Overview

## Purpose
A Django-based vocabulary learning application that helps users build and study English vocabulary through flashcards with difficulty-based learning system (not traditional spaced repetition). Features comprehensive study modes, CEFR level classification, audio pronunciation, and extensive statistics tracking.

## Tech Stack
- **Backend**: Django 5.2.1, Python
- **Database**: SQLite (development), PostgreSQL (production)
- **Authentication**: django-allauth with email-based login, Google/Facebook OAuth
- **Frontend**: HTML/CSS/JavaScript with Tailwind CSS styling
- **External APIs**: Datamuse (definitions), LanguageTool (grammar), Unsplash (images), Google Translate
- **Audio**: Cambridge Dictionary audio fetching, multiple pronunciation sources
- **Environment**: python-decouple for configuration management
- **Deployment**: Gunicorn, Whitenoise for static files

## Key Architecture Components
- **vocabulary/**: Core app with flashcards, decks, study sessions, learning algorithms
- **accounts/**: Custom email-based authentication with avatar support  
- **learn_english_project/**: Main Django project settings
- **static/**: CSS, JavaScript, audio files, images
- **templates/**: Django templates with custom i18n system
- **tests/**: Comprehensive test suite for features and bug fixes
- **tools/**: Database migration and setup utilities

## Core Features
- Difficulty-based learning system (0.0=Again, 0.33=Hard, 0.67=Good, 1.0=Easy)
- Multiple study modes (deck, favorites, random, blacklist management)
- CEFR level classification and filtering
- Audio pronunciation with enhanced fetching
- Image associations via Unsplash API
- Comprehensive statistics (daily/weekly aggregation)
- Vietnamese-English translation support
- Real-time word suggestions and spell checking