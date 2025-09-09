from django.db import models
import os
from django.conf import settings
from django.utils import timezone

class Deck(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='decks')
    name = models.CharField(max_length=255)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name

    class Meta:
        ordering = ['-created_at']
        unique_together = ['user', 'name']
        indexes = [
            models.Index(fields=['user', 'created_at']),
            models.Index(fields=['user', 'name']),
        ]

class Flashcard(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='flashcards')
    deck = models.ForeignKey(Deck, on_delete=models.CASCADE, related_name='flashcards', null=True, blank=True)
    word = models.CharField(max_length=255)
    phonetic = models.CharField(max_length=100, blank=True, null=True, help_text="Phonetic transcription (e.g., /rɪˈzɪliənt/)")
    part_of_speech = models.CharField(max_length=50, blank=True, null=True)
    audio_url = models.URLField(max_length=500, blank=True, null=True)
    image = models.ImageField(upload_to='flashcard_images/', blank=True, null=True)
    related_image_url = models.URLField(max_length=500, blank=True, null=True, help_text="Auto-fetched related image URL")
    general_synonyms = models.TextField(blank=True, null=True, help_text="Comma-separated list of general synonyms")
    general_antonyms = models.TextField(blank=True, null=True, help_text="Comma-separated list of general antonyms")
    # Legacy spaced repetition fields (no longer used in difficulty-based system)
    ease_factor = models.FloatField(default=2.5, help_text="Legacy SM-2 ease factor (not used)")
    repetitions = models.PositiveIntegerField(default=0, help_text="Legacy successful reviews count (not used)")
    interval = models.PositiveIntegerField(default=0, help_text="Legacy interval days (not used)")
    next_review = models.DateField(default=timezone.now, help_text="Legacy next review date (not used)")
    last_reviewed = models.DateTimeField(blank=True, null=True, help_text="Last time card was reviewed")

    # Difficulty-based system fields
    times_seen_today = models.PositiveIntegerField(default=0, help_text="Number of times seen today (reset daily)")
    last_seen_date = models.DateField(blank=True, null=True, help_text="Last date this card was shown")
    difficulty_score = models.FloatField(default=None, null=True, blank=True, help_text="Difficulty level: 0.0=Again, 0.33=Hard, 0.67=Good, 1.0=Easy")
    total_reviews = models.PositiveIntegerField(default=0, help_text="Total number of times reviewed")
    correct_reviews = models.PositiveIntegerField(default=0, help_text="Number of correct reviews")

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.word

    @property
    def difficulty_level(self):
        """Return a user-friendly difficulty level based on difficulty_score."""
        if self.difficulty_score is None:
            return "New"
        elif self.difficulty_score == 0.0:
            return "Again"
        elif self.difficulty_score == 0.33:
            return "Hard"
        elif self.difficulty_score == 0.67:
            return "Good"
        elif self.difficulty_score == 1.0:
            return "Easy"
        else:
            # Fallback for any unexpected values
            return "Unknown"

    @property
    def accuracy_percentage(self):
        """Return accuracy as a percentage."""
        if self.total_reviews == 0:
            return 0
        return round((self.correct_reviews / self.total_reviews) * 100, 1)

    def save(self, *args, **kwargs):
        # Xóa file cũ khi update với hình ảnh mới
        if self.pk:
            try:
                old_image = Flashcard.objects.get(pk=self.pk).image
                if old_image and old_image != self.image:
                    if os.path.isfile(old_image.path):
                        os.remove(old_image.path)
            except Flashcard.DoesNotExist:
                pass
        super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        # Xóa file hình ảnh trước khi xóa object
        if self.image:
            if os.path.isfile(self.image.path):
                os.remove(self.image.path)
        super().delete(*args, **kwargs)

    class Meta:
        ordering = ['word']
        unique_together = ['user', 'word']  # Một user không thể có từ trùng lặp
        indexes = [
            models.Index(fields=['user', 'word']),
            models.Index(fields=['user', 'deck']),
            models.Index(fields=['user', 'last_seen_date']),
            models.Index(fields=['user', 'difficulty_score']),
            models.Index(fields=['user', 'times_seen_today']),
            models.Index(fields=['user', 'created_at']),
            models.Index(fields=['difficulty_score', 'times_seen_today']),
            models.Index(fields=['last_seen_date', 'times_seen_today']),
        ]

class Definition(models.Model):
    flashcard = models.ForeignKey(Flashcard, related_name='definitions', on_delete=models.CASCADE)
    english_definition = models.TextField()
    vietnamese_definition = models.TextField()
    definition_synonyms = models.TextField(blank=True, null=True, help_text="Comma-separated list of synonyms for this definition")
    definition_antonyms = models.TextField(blank=True, null=True, help_text="Comma-separated list of antonyms for this definition")

    class Meta:
        indexes = [
            models.Index(fields=['flashcard']),
        ]

    def __str__(self):
        return f"{self.flashcard.word} - {self.english_definition[:50]}..."


class StudySession(models.Model):
    """Track individual study sessions with comprehensive metrics."""
    STUDY_MODE_CHOICES = [
        ('deck', 'Deck Study'),
        ('random', 'Random Study'),
        ('favorites', 'Favorites Study'),
        ('spaced_repetition', 'Spaced Repetition'),
    ]

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='study_sessions')
    session_start = models.DateTimeField(auto_now_add=True)
    session_end = models.DateTimeField(null=True, blank=True)
    study_mode = models.CharField(max_length=20, choices=STUDY_MODE_CHOICES, default='deck')
    decks_studied = models.ManyToManyField(Deck, blank=True, help_text="Decks included in this session")

    # Session metrics
    total_questions = models.PositiveIntegerField(default=0)
    correct_answers = models.PositiveIntegerField(default=0)
    incorrect_answers = models.PositiveIntegerField(default=0)
    session_duration_seconds = models.PositiveIntegerField(default=0, help_text="Total session duration in seconds")

    # Additional tracking
    words_studied = models.PositiveIntegerField(default=0, help_text="Unique words encountered in this session")
    average_response_time = models.FloatField(default=0.0, help_text="Average time per question in seconds")

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-session_start']
        indexes = [
            models.Index(fields=['user', 'session_start']),
            models.Index(fields=['user', 'study_mode']),
        ]

    def __str__(self):
        return f"{self.user.username} - {self.get_study_mode_display()} - {self.session_start.strftime('%Y-%m-%d %H:%M')}"

    @property
    def accuracy_percentage(self):
        """Calculate accuracy percentage for this session."""
        if self.total_questions == 0:
            return 0
        return round((self.correct_answers / self.total_questions) * 100, 1)

    @property
    def duration_formatted(self):
        """Return formatted duration string."""
        if self.session_duration_seconds == 0:
            return "0m 0s"

        minutes = self.session_duration_seconds // 60
        seconds = self.session_duration_seconds % 60

        if minutes > 0:
            return f"{minutes}m {seconds}s"
        else:
            return f"{seconds}s"

    def end_session(self):
        """Mark session as ended and calculate duration."""
        if not self.session_end:
            self.session_end = timezone.now()
            self.session_duration_seconds = int((self.session_end - self.session_start).total_seconds())
            self.save(update_fields=['session_end', 'session_duration_seconds'])


class StudySessionAnswer(models.Model):
    """Track individual answers within study sessions."""
    session = models.ForeignKey(StudySession, on_delete=models.CASCADE, related_name='answers')
    flashcard = models.ForeignKey(Flashcard, on_delete=models.CASCADE)

    # Answer details
    is_correct = models.BooleanField()
    response_time_seconds = models.FloatField(help_text="Time taken to answer in seconds")
    question_type = models.CharField(max_length=20, default='multiple_choice', help_text="Type of question (mc, input, etc.)")

    # Spaced repetition context
    difficulty_before = models.FloatField(help_text="Card difficulty before this answer")
    difficulty_after = models.FloatField(help_text="Card difficulty after this answer")

    answered_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['answered_at']
        indexes = [
            models.Index(fields=['session', 'answered_at']),
            models.Index(fields=['flashcard', 'is_correct']),
        ]

    def __str__(self):
        status = "✓" if self.is_correct else "✗"
        return f"{status} {self.flashcard.word} - {self.response_time_seconds:.1f}s"


class DailyStatistics(models.Model):
    """Aggregate daily statistics for users."""
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='daily_stats')
    date = models.DateField()

    # Study metrics
    total_study_time_seconds = models.PositiveIntegerField(default=0)
    total_questions_answered = models.PositiveIntegerField(default=0)
    correct_answers = models.PositiveIntegerField(default=0)
    incorrect_answers = models.PositiveIntegerField(default=0)
    unique_words_studied = models.PositiveIntegerField(default=0)

    # Session metrics
    study_sessions_count = models.PositiveIntegerField(default=0)
    average_session_duration = models.FloatField(default=0.0, help_text="Average session duration in seconds")

    # Card creation
    new_cards_created = models.PositiveIntegerField(default=0)

    # Streak tracking
    is_study_day = models.BooleanField(default=False, help_text="True if user studied on this day")

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ['user', 'date']
        ordering = ['-date']
        indexes = [
            models.Index(fields=['user', 'date']),
            models.Index(fields=['user', 'is_study_day']),
        ]

    def __str__(self):
        return f"{self.user.username} - {self.date} - {self.total_questions_answered} questions"

    @property
    def accuracy_percentage(self):
        """Calculate accuracy percentage for this day."""
        if self.total_questions_answered == 0:
            return 0
        return round((self.correct_answers / self.total_questions_answered) * 100, 1)

    @property
    def study_time_formatted(self):
        """Return formatted study time string."""
        if self.total_study_time_seconds == 0:
            return "0m"

        hours = self.total_study_time_seconds // 3600
        minutes = (self.total_study_time_seconds % 3600) // 60

        if hours > 0:
            return f"{hours}h {minutes}m"
        else:
            return f"{minutes}m"


class WeeklyStatistics(models.Model):
    """Aggregate weekly statistics for users."""
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='weekly_stats')
    year = models.PositiveIntegerField()
    week_number = models.PositiveIntegerField(help_text="ISO week number (1-53)")
    week_start_date = models.DateField()

    # Study metrics
    total_study_time_seconds = models.PositiveIntegerField(default=0)
    total_questions_answered = models.PositiveIntegerField(default=0)
    correct_answers = models.PositiveIntegerField(default=0)
    incorrect_answers = models.PositiveIntegerField(default=0)
    unique_words_studied = models.PositiveIntegerField(default=0)

    # Session metrics
    study_sessions_count = models.PositiveIntegerField(default=0)
    study_days_count = models.PositiveIntegerField(default=0, help_text="Number of days studied this week")

    # Card creation
    new_cards_created = models.PositiveIntegerField(default=0)

    # Goals and streaks
    weekly_goal_met = models.BooleanField(default=False)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ['user', 'year', 'week_number']
        ordering = ['-year', '-week_number']
        indexes = [
            models.Index(fields=['user', 'year', 'week_number']),
            models.Index(fields=['user', 'week_start_date']),
        ]

    def __str__(self):
        return f"{self.user.username} - Week {self.week_number}/{self.year} - {self.total_questions_answered} questions"

    @property
    def accuracy_percentage(self):
        """Calculate accuracy percentage for this week."""
        if self.total_questions_answered == 0:
            return 0
        return round((self.correct_answers / self.total_questions_answered) * 100, 1)

    @property
    def study_time_formatted(self):
        """Return formatted study time string."""
        if self.total_study_time_seconds == 0:
            return "0h"

        hours = self.total_study_time_seconds // 3600
        minutes = (self.total_study_time_seconds % 3600) // 60

        if hours > 0:
            return f"{hours}h {minutes}m"
        else:
            return f"{minutes}m"

    @property
    def consistency_percentage(self):
        """Calculate study consistency (days studied / 7 days)."""
        return round((self.study_days_count / 7) * 100, 1)


class IncorrectWordReview(models.Model):
    """Track words that users answered incorrectly for review purposes."""

    QUESTION_TYPE_CHOICES = [
        ('mc', 'Multiple Choice'),
        ('type', 'Input Mode'),
        ('dictation', 'Dictation Mode'),
    ]

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='incorrect_words')
    flashcard = models.ForeignKey(Flashcard, on_delete=models.CASCADE, related_name='incorrect_reviews')
    question_type = models.CharField(max_length=10, choices=QUESTION_TYPE_CHOICES)
    error_count = models.PositiveIntegerField(default=1, help_text="Number of times answered incorrectly in this question type")
    first_error_date = models.DateTimeField(auto_now_add=True)
    last_error_date = models.DateTimeField(auto_now=True)
    is_resolved = models.BooleanField(default=False, help_text="True when answered correctly in this question type")
    resolved_date = models.DateTimeField(null=True, blank=True)

    class Meta:
        unique_together = ['user', 'flashcard', 'question_type']
        ordering = ['-last_error_date']
        indexes = [
            models.Index(fields=['user', 'is_resolved']),
            models.Index(fields=['user', 'question_type', 'is_resolved']),
        ]

    def __str__(self):
        return f"{self.user.username} - {self.flashcard.word} ({self.get_question_type_display()})"

    def mark_resolved(self):
        """Mark this incorrect word as resolved (answered correctly)."""
        self.is_resolved = True
        self.resolved_date = timezone.now()
        self.save()

    def add_error(self):
        """Increment error count and update last error date."""
        self.error_count += 1
        self.last_error_date = timezone.now()
        if self.is_resolved:
            # If it was previously resolved but now incorrect again, unresolve it
            self.is_resolved = False
            self.resolved_date = None
        self.save()


class FavoriteFlashcard(models.Model):
    """Track user's favorite flashcards for focused study."""
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='favorite_flashcards')
    flashcard = models.ForeignKey(Flashcard, on_delete=models.CASCADE, related_name='favorited_by')
    favorited_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ['user', 'flashcard']  # Prevent duplicate favorites
        ordering = ['-favorited_at']
        indexes = [
            models.Index(fields=['user', 'favorited_at']),
            models.Index(fields=['user', 'flashcard']),
        ]

    def __str__(self):
        return f"{self.user.email} - {self.flashcard.word} (favorited)"

    @classmethod
    def is_favorited(cls, user, flashcard):
        """Check if a flashcard is favorited by a user."""
        return cls.objects.filter(user=user, flashcard=flashcard).exists()

    @classmethod
    def get_user_favorites_count(cls, user):
        """Get the count of user's favorite flashcards."""
        return cls.objects.filter(user=user).count()

    @classmethod
    def get_user_favorites(cls, user):
        """Get all favorite flashcards for a user."""
        return cls.objects.filter(user=user).select_related('flashcard')

    @classmethod
    def toggle_favorite(cls, user, flashcard):
        """Toggle favorite status for a flashcard. Returns (favorite_obj, created)."""
        favorite, created = cls.objects.get_or_create(
            user=user,
            flashcard=flashcard
        )
        if not created:
            # If it already exists, remove it (unfavorite)
            favorite.delete()
            return None, False
        return favorite, True


class BlacklistFlashcard(models.Model):
    """Track user's blacklisted flashcards to exclude from study sessions."""
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='blacklisted_flashcards')
    flashcard = models.ForeignKey(Flashcard, on_delete=models.CASCADE, related_name='blacklisted_by')
    blacklisted_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ['user', 'flashcard']  # Prevent duplicate blacklists
        ordering = ['-blacklisted_at']
        indexes = [
            models.Index(fields=['user', 'blacklisted_at']),
            models.Index(fields=['user', 'flashcard']),
        ]

    def __str__(self):
        return f"{self.user.email} - {self.flashcard.word} (blacklisted)"

    @classmethod
    def is_blacklisted(cls, user, flashcard):
        """Check if a flashcard is blacklisted by a user."""
        return cls.objects.filter(user=user, flashcard=flashcard).exists()

    @classmethod
    def get_user_blacklist_count(cls, user):
        """Get the count of user's blacklisted flashcards."""
        return cls.objects.filter(user=user).count()

    @classmethod
    def get_user_blacklist(cls, user):
        """Get all blacklisted flashcards for a user."""
        return cls.objects.filter(user=user).select_related('flashcard')

    @classmethod
    def toggle_blacklist(cls, user, flashcard):
        """Toggle blacklist status for a flashcard. Returns (blacklist_obj, created)."""
        blacklist, created = cls.objects.get_or_create(
            user=user,
            flashcard=flashcard
        )
        if not created:
            # If it already exists, remove it (unblacklist)
            blacklist.delete()
            return None, False
        return blacklist, True
