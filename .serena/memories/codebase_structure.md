# LearnEnglish - Codebase Structure

## Root Directory
```
D:\My Projects\Web\LearnEngish\
├── manage.py                    # Django management script
├── requirements.txt             # Python dependencies
├── CLAUDE.md                   # Claude Code instructions
├── README.md                   # Project documentation
└── runtime.txt                 # Python version specification
```

## Core Django Apps

### vocabulary/ (Main App)
```
vocabulary/
├── models.py                   # Core models (Flashcard, Deck, StudySession, etc.)
├── views.py                    # API endpoints and page views
├── urls.py & api_urls.py       # URL routing
├── admin.py                    # Django admin configuration
├── signals.py                  # Django signals
├── tests.py                    # Unit tests
├── api_services.py             # External API integrations
├── audio_service.py            # Audio fetching services
├── word_details_service.py     # Word lookup services
├── statistics_utils.py         # Statistics calculation
├── cache_utils.py              # Caching utilities
├── cefr_service.py             # CEFR level classification
├── context_processors.py       # Custom i18n system
├── management/commands/        # Custom Django commands
└── templates/vocabulary/       # App-specific templates
```

### accounts/ (Authentication)
```
accounts/
├── models.py                   # CustomUser model
├── views.py                    # Authentication views
├── admin.py                    # User admin
├── management/commands/        # User management commands
└── migrations/                 # Database migrations
```

### learn_english_project/ (Settings)
```
learn_english_project/
├── settings.py                 # Main Django settings
├── urls.py                     # Root URL configuration
├── wsgi.py & asgi.py          # WSGI/ASGI configuration
```

## Frontend Structure

### templates/
```
templates/
├── base.html                   # Base template (in vocabulary/templates/)
├── account/                    # Authentication templates
├── socialaccount/              # OAuth templates
└── vocabulary/                 # Main app templates
```

### static/
```
static/
├── css/                        # Stylesheets (main.css, study.css, auth.css)
├── js/                         # JavaScript modules
├── images/                     # Static images
├── audio/                      # Audio feedback files
└── test/                       # Frontend testing files
```

## Support Directories

### tests/ (Integration Tests)
- Feature-specific test files
- Bug fix validation tests
- Audio and UI component tests

### tools/ (Database Utilities)  
- Migration scripts
- Database setup tools
- Windows batch files

### docs/ (Documentation)
- Feature implementation guides
- Project organization docs
- Technical specifications

### debug/ (Debug Information)
- Documentation of bug fixes
- Debug guides and summaries