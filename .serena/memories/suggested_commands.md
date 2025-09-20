# LearnEnglish - Essential Development Commands

## Setup and Installation
```bash
pip install -r requirements.txt
python manage.py migrate
python manage.py runserver
```

## Database Operations
```bash
python manage.py makemigrations
python manage.py migrate  
python manage.py createsuperuser
python manage.py dbshell
```

## Testing
```bash
python manage.py test                    # Run all tests
python manage.py test vocabulary         # Test vocabulary app
python manage.py test tests.test_*       # Test specific modules
```

## Custom Management Commands
```bash
# Statistics and Analysis
python manage.py analyze_study_algorithm
python manage.py diagnose_statistics
python manage.py fix_statistics
python manage.py populate_statistics
python manage.py test_statistics

# CEFR and Audio
python manage.py load_cefr_wordlist
python manage.py populate_cefr_data  
python manage.py update_all_cefr_levels
python manage.py test_enhanced_audio_api

# User Management (accounts app)
python manage.py delete_user
python manage.py cleanup_avatars
```

## Development Tools
```bash
python manage.py shell                   # Django shell
python manage.py check                   # Check for issues
python manage.py collectstatic           # Collect static files
```

## Database Utilities (tools/ directory)
```bash
python tools/migrate_database.py
python tools/clear_database.py
python tools/setup_new_db.py
run_migration.bat                        # Windows batch script
```

## Windows-Specific Commands
- Use `dir` instead of `ls`
- Use `type` instead of `cat`
- Use `findstr` instead of `grep`
- Use backslashes `\` for paths