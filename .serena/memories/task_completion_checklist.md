# LearnEnglish - Task Completion Checklist

## After Code Changes

### 1. Database Migrations
```bash
python manage.py makemigrations
python manage.py migrate
```

### 2. Testing
```bash
python manage.py test                    # Run full test suite
python manage.py test vocabulary         # Test vocabulary app specifically
python manage.py test tests              # Run integration tests
```

### 3. Static Files (if CSS/JS changed)
```bash
python manage.py collectstatic
```

### 4. Code Quality Checks
```bash
python manage.py check                   # Django system checks
```

### 5. Custom Management Commands (if needed)
```bash
python manage.py populate_statistics     # Update statistics
python manage.py fix_statistics          # Fix any statistics issues
python manage.py update_all_cefr_levels  # Update CEFR classifications
```

## Before Deployment

### 1. Environment Check
- Verify `.env` file configuration
- Check `DEBUG = False` for production
- Validate `ALLOWED_HOSTS` settings

### 2. Database Backup
```bash
python manage.py dumpdata > backup.json
```

### 3. Dependencies Check
```bash
pip freeze > requirements.txt            # Update if needed
```

## Special Considerations
- **Statistics**: Run statistics commands after major data changes
- **CEFR Levels**: Update CEFR data when adding new vocabulary
- **Audio**: Test audio fetching if audio-related changes made
- **Caching**: Clear cache if caching logic modified
- **Migrations**: Review migration files for complex schema changes