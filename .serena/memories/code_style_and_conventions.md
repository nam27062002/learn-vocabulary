# LearnEnglish - Code Style and Conventions

## Django Conventions
- **Models**: CamelCase class names (e.g., `Flashcard`, `StudySession`)
- **Fields**: snake_case field names (e.g., `difficulty_score`, `last_seen_date`)
- **Methods**: snake_case method names with descriptive names
- **Properties**: Use `@property` decorator for calculated fields

## File Organization
- **Models**: Core business logic in `vocabulary/models.py`
- **Views**: API endpoints and page views in `vocabulary/views.py`
- **Services**: External API calls in separate service files (`api_services.py`, `audio_service.py`)
- **Templates**: Extend `base.html`, use vocabulary app templates
- **Static Files**: Organized by type (css/, js/, images/, audio/)

## Naming Conventions
- **Database Fields**: snake_case with descriptive names
- **CSS Classes**: kebab-case (e.g., `study-header`, `card-box`)
- **JavaScript**: camelCase variables and functions
- **Management Commands**: snake_case filenames

## Documentation Style
- **Docstrings**: Use Google-style docstrings for functions
- **Comments**: Mix of English and Vietnamese comments (legacy)
- **Help Text**: Detailed help_text for model fields
- **API Documentation**: Inline comments explaining complex logic

## Code Patterns
- **Error Handling**: Try-catch blocks with proper logging
- **Caching**: Extensive use of Django caching framework
- **Database**: Comprehensive indexing for performance
- **Testing**: Test files named `test_*.py` with descriptive test methods

## API Design
- **Endpoints**: RESTful API with `api_` prefix for view functions
- **Response Format**: JSON responses with consistent error handling
- **Authentication**: User-based filtering for all data access
- **Validation**: Server-side validation with client-side feedback