# LearnEnglish - Key Models and Relationships

## Core Models

### Flashcard (Primary Entity)
- **Purpose**: Core vocabulary card with word, definitions, media, and learning metrics
- **Key Fields**:
  - `word`: CharField - the vocabulary word
  - `phonetic`: CharField - phonetic transcription  
  - `difficulty_score`: FloatField - learning difficulty (0.0-1.0)
  - `times_seen_today`: PositiveIntegerField - daily exposure tracking
  - `cefr_level`: CharField - European framework classification
  - `audio_url`: URLField - pronunciation audio
  - `related_image_url`: URLField - associated image
- **Relationships**: ForeignKey to User, ForeignKey to Deck
- **Indexes**: Comprehensive indexing on user+word, difficulty_score, last_seen_date

### Deck (Organization)
- **Purpose**: Groups related flashcards for organized study
- **Relationships**: ForeignKey to User, OneToMany with Flashcards

### Definition (Content)
- **Purpose**: English and Vietnamese definitions for flashcards
- **Fields**: `english_definition`, `vietnamese_definition`, `example_sentence`
- **Relationships**: ForeignKey to Flashcard

### StudySession & StudySessionAnswer (Learning Tracking)
- **Purpose**: Tracks individual study sessions and responses
- **Key Metrics**: response_time, is_correct, difficulty_rating
- **Relationships**: StudySession -> User, StudySessionAnswer -> StudySession + Flashcard

### Statistics Models
- **DailyStatistics**: Daily aggregated learning metrics per user
- **WeeklyStatistics**: Weekly progress tracking and trends

### Learning Support Models
- **IncorrectWordReview**: Tracks words needing additional review
- **FavoriteFlashcard**: User's favorite cards for targeted study
- **BlacklistFlashcard**: Cards excluded from study sessions

## Authentication

### CustomUser (accounts app)
- **Purpose**: Email-based authentication with avatar support
- **Key Features**: No username field, email as USERNAME_FIELD
- **Fields**: `email`, `avatar`, standard Django user fields
- **Manager**: CustomUserManager for email-based user creation

## Learning Algorithm
- **System**: Difficulty-based (not traditional spaced repetition)
- **Scoring**: 0.0=Again, 0.33=Hard, 0.67=Good, 1.0=Easy
- **Daily Limits**: Prevents overwhelming users with repetitions
- **CEFR Integration**: European framework levels for vocabulary classification