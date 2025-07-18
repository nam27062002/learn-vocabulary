# Project Structure

## Root Directory Layout
```
learn_english_project/
├── manage.py                    # Django management script
├── db.sqlite3                   # SQLite database file
├── requirements.txt             # Python dependencies (if exists)
├── checklist.txt               # Development checklist
├── AUTHENTICATION_SETUP.md     # Auth setup documentation
├── TEST_AUTHENTICATION.md      # Auth testing guide
├── learn_english_project/      # Main Django project
├── accounts/                   # Custom user authentication app
├── vocabulary/                 # Core vocabulary learning app
├── templates/                  # Global HTML templates
├── static/                     # Source static files
├── staticfiles/               # Collected static files (production)
├── media/                     # User uploaded files
├── locale/                    # Internationalization files
├── venv/                      # Virtual environment
└── .venv/                     # Alternative venv location
```

## Django Apps Structure

### Main Project (`learn_english_project/`)
- `settings.py`: Django configuration with i18n, auth, and API settings
- `urls.py`: Root URL configuration with i18n patterns
- `wsgi.py` & `asgi.py`: WSGI/ASGI application entry points

### Accounts App (`accounts/`)
- `models.py`: CustomUser model with email-based authentication
- `admin.py`: Admin interface customizations
- `views.py`: Authentication-related views
- `migrations/`: Database schema changes

### Vocabulary App (`vocabulary/`)
- `models.py`: Core models (Flashcard, Definition, Deck)
- `views.py`: Main application views and API endpoints
- `urls.py`: URL routing for vocabulary features
- `api_services.py`: External API integration services
- `word_details_service.py`: Word lookup and details service
- `context_processors.py`: Template context processors
- `templates/vocabulary/`: App-specific templates
- `admin.py`: Admin interface for vocabulary models
- `tests.py`: Unit tests

## Static Files Organization
```
static/
├── css/                        # Custom stylesheets
└── js/                         # Custom JavaScript files

staticfiles/                    # Collected static files
├── admin/                      # Django admin static files
├── account/                    # django-allauth static files
├── css/                        # Collected CSS
└── js/                         # Collected JavaScript
```

## Templates Structure
```
templates/
├── account/                    # django-allauth template overrides
└── socialaccount/             # Social auth template overrides

vocabulary/templates/vocabulary/
├── dashboard.html              # Main dashboard
├── add_flashcard.html         # Flashcard creation
├── flashcard_list.html        # Flashcard listing
├── deck_list.html             # Deck management
├── deck_detail.html           # Individual deck view
├── study.html                 # Study interface
├── statistics.html            # Progress statistics
└── language_test.html         # i18n testing
```

## Media Files
```
media/
└── flashcard_images/          # User-uploaded flashcard images
```

## Internationalization
```
locale/
├── en/                        # English translations
│   └── LC_MESSAGES/
└── vi/                        # Vietnamese translations
    └── LC_MESSAGES/
```

## Key Architectural Patterns

### Model Relationships
- **User-centric**: All models linked to authenticated users
- **Hierarchical**: User → Deck → Flashcard → Definition
- **Spaced Repetition**: SM-2 algorithm fields in Flashcard model

### URL Patterns
- **i18n URLs**: Language-prefixed URLs for internationalization
- **RESTful APIs**: `/api/` endpoints for AJAX interactions
- **Authentication**: `/accounts/` for auth-related URLs

### File Upload Handling
- **Image Storage**: `media/flashcard_images/` for user uploads
- **Cleanup**: Automatic file deletion on model deletion

### Service Layer
- **External APIs**: Separated into dedicated service modules
- **Translation**: Multiple translation service providers
- **Word Data**: Integrated word lookup and definition services

## Development Conventions
- **App Isolation**: Each app handles its own URLs, templates, and static files
- **User Filtering**: All queries filtered by `request.user`
- **API Responses**: Consistent JSON response format
- **Error Handling**: Comprehensive try-catch blocks with user-friendly messages
- **Debug Mode**: `ENABLE_DEBUG` setting for development logging