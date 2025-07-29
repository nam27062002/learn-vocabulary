# Learn English Vocabulary - Project Structure

## 📁 Directory Organization

This document describes the organized project structure after cleanup and reorganization.

### 🏗️ Main Project Structure

```
learn-vocabulary/
├── 📁 accounts/                    # User account management
├── 📁 debug/                       # Debug templates and assets
├── 📁 dev_tools/                   # Development tools and utilities
├── 📁 docs/                        # Project documentation
├── 📁 learn_english_project/       # Django project settings
├── 📁 locale/                      # Internationalization files
├── 📁 media/                       # User uploaded media files
├── 📁 scripts/                     # Deployment and utility scripts
├── 📁 static/                      # Static assets (CSS, JS, images)
├── 📁 staticfiles/                 # Collected static files (production)
├── 📁 templates/                   # Global Django templates
├── 📁 tests/                       # Test files and debugging scripts
├── 📁 vocabulary/                  # Main vocabulary application
├── 📁 venv/                        # Python virtual environment
├── 📄 manage.py                    # Django management script
├── 📄 requirements.txt             # Python dependencies
├── 📄 runtime.txt                  # Python version specification
└── 📄 README.md                    # Project documentation
```

### 🧪 Tests Directory (`tests/`)

Contains all test files and debugging scripts used during development:

```
tests/
├── 📄 __init__.py                           # Package initialization
├── 📄 test_api_fix.py                       # API functionality tests
├── 📄 test_audio_stats_fix.py               # Audio statistics tests
├── 📄 test_current_audio_ui_fixes.py        # Current audio UI tests
├── 📄 test_deck_navigation.py               # Deck navigation tests
├── 📄 test_enhanced_audio_debug.py          # Enhanced audio debugging
├── 📄 test_enhanced_audio_fixes.py          # Enhanced audio fixes tests
├── 📄 test_enhanced_audio_ux.py             # Enhanced audio UX tests
├── 📄 test_favorites.py                     # Favorites functionality tests
├── 📄 test_favorites_implementation.py      # Favorites implementation tests
└── 📄 test_notification_ui_fixes.py         # Notification UI tests
```

### 🛠️ Development Tools (`dev_tools/`)

Contains development utilities and maintenance scripts:

```
dev_tools/
├── 📄 __init__.py                    # Package initialization
├── 📄 batch_fix_imports.py           # Batch import fixing utility
├── 📄 compile_messages.py            # Message compilation utility
├── 📄 debug_incorrect_words.py       # Word debugging script
└── 📄 fix_test_imports.py            # Test import fixing utility
```

### 📚 Vocabulary Application (`vocabulary/`)

Main application containing the core functionality:

```
vocabulary/
├── 📁 management/                    # Django management commands
├── 📁 migrations/                    # Database migrations
├── 📁 templates/                     # Application templates
├── 📄 admin.py                       # Django admin configuration
├── 📄 api_services.py                # API service functions
├── 📄 api_urls.py                    # API URL routing
├── 📄 apps.py                        # Application configuration
├── 📄 audio_service.py               # Audio processing services
├── 📄 context_processors.py          # Template context processors
├── 📄 models.py                      # Database models
├── 📄 statistics_utils.py            # Statistics utilities
├── 📄 tests.py                       # Django unit tests
├── 📄 tests_enhanced_audio.py        # Enhanced audio tests
├── 📄 urls.py                        # URL routing
├── 📄 views.py                       # View functions
└── 📄 word_details_service.py        # Word details services
```

## 🚀 Running Tests

### From Project Root

All test files can now be run from the project root directory:

```bash
# Run individual test files
python tests/test_deck_navigation.py
python tests/test_enhanced_audio_debug.py
python tests/test_favorites.py

# Run development tools
python dev_tools/compile_messages.py
python dev_tools/debug_incorrect_words.py
```

### Test File Features

- ✅ **Automatic Django setup**: All test files handle Django configuration
- ✅ **Path resolution**: Correct import paths from subdirectories
- ✅ **Database integration**: Full access to Django models and database
- ✅ **User creation**: Automatic test user and data creation
- ✅ **Comprehensive testing**: Step-by-step testing guides included

## 🔧 Development Tools

### Message Compilation (`dev_tools/compile_messages.py`)
- Compiles Django .po files to .mo files
- Handles internationalization without gettext tools
- Supports both English and Vietnamese translations

### Import Fixing (`dev_tools/batch_fix_imports.py`)
- Automatically fixes import paths in moved test files
- Handles Django path resolution
- Batch processing for multiple files

### Debug Scripts (`dev_tools/debug_incorrect_words.py`)
- Debugging utilities for word processing
- Database query helpers
- Development troubleshooting tools

## 📋 Benefits of New Structure

### ✅ Clean Project Root
- Only essential files in root directory
- Professional project appearance
- Easy navigation and maintenance

### ✅ Organized Testing
- All test files in dedicated directory
- Consistent import handling
- Easy test discovery and execution

### ✅ Separated Development Tools
- Development utilities isolated
- Maintenance scripts organized
- Clear separation of concerns

### ✅ Preserved Functionality
- All existing functionality maintained
- Test files work from new locations
- Development workflow unchanged

## 🎯 Usage Guidelines

### Adding New Tests
1. Create test files in `tests/` directory
2. Use the standard Django setup pattern (see existing files)
3. Include comprehensive testing guides
4. Add descriptive docstrings and comments

### Adding Development Tools
1. Create utility scripts in `dev_tools/` directory
2. Include proper error handling
3. Add usage documentation
4. Follow existing naming conventions

### Project Maintenance
- Keep root directory clean
- Organize new files in appropriate directories
- Update documentation when adding new components
- Maintain consistent code style and structure

## 📞 Support

For questions about the project structure or test files, refer to:
- Individual test file documentation
- Django project documentation
- Application-specific README files
- Code comments and docstrings
