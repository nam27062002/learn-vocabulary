# Technology Stack

## Backend Framework
- **Django 5.1.7**: Main web framework
- **Python**: Primary programming language
- **SQLite**: Development database (configurable for production)

## Key Dependencies
- **django-allauth**: Authentication and social login (Google OAuth)
- **googletrans**: Translation services
- **deep-translator**: Alternative translation service
- **Pillow**: Image processing for flashcard images
- **requests**: HTTP client for external API calls

## Frontend Technologies
- **HTML/CSS/JavaScript**: Standard web technologies
- **Bootstrap** (implied from staticfiles structure): UI framework
- **AJAX/JSON**: Asynchronous API communication

## External APIs & Services
- **Datamuse API**: Word suggestions and vocabulary data
- **LanguageTool API**: Spell checking functionality
- **Unsplash API**: Related image fetching for flashcards
- **Google Translate**: Translation services
- **Google OAuth**: Social authentication

## Development Environment
- **Virtual Environment**: Python venv for dependency isolation
- **Static Files**: Collected in `staticfiles/` directory
- **Media Files**: User uploads stored in `media/` directory

## Common Commands

### Development Setup
```bash
# Activate virtual environment
venv\Scripts\activate  # Windows
source venv/bin/activate  # Linux/Mac

# Install dependencies
pip install -r requirements.txt

# Database setup
python manage.py makemigrations
python manage.py migrate

# Create superuser
python manage.py createsuperuser

# Collect static files
python manage.py collectstatic

# Run development server
python manage.py runserver
```

### Internationalization
```bash
# Generate translation files
python manage.py makemessages -l vi
python manage.py makemessages -l en

# Compile translations
python manage.py compilemessages
```

### Database Management
```bash
# Create new migrations
python manage.py makemigrations [app_name]

# Apply migrations
python manage.py migrate

# Show migration status
python manage.py showmigrations
```

## Architecture Patterns
- **MVT Pattern**: Django's Model-View-Template architecture
- **RESTful APIs**: JSON-based API endpoints for AJAX interactions
- **Service Layer**: Separate service modules for external API integrations
- **User-based Data Isolation**: All models filtered by authenticated user