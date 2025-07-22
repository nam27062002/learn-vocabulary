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
    # Spaced repetition scheduling fields
    ease_factor = models.FloatField(default=2.5, help_text="SM-2 ease factor")
    repetitions = models.PositiveIntegerField(default=0, help_text="Number of successful reviews in a row")
    interval = models.PositiveIntegerField(default=0, help_text="Interval (days) until next review")
    next_review = models.DateField(default=timezone.now)
    last_reviewed = models.DateTimeField(blank=True, null=True)

    # Enhanced spaced repetition fields
    times_seen_today = models.PositiveIntegerField(default=0, help_text="Number of times seen today (reset daily)")
    last_seen_date = models.DateField(blank=True, null=True, help_text="Last date this card was shown")
    difficulty_score = models.FloatField(default=0.0, help_text="Difficulty score based on user performance")
    total_reviews = models.PositiveIntegerField(default=0, help_text="Total number of times reviewed")
    correct_reviews = models.PositiveIntegerField(default=0, help_text="Number of correct reviews")

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.word

    @property
    def difficulty_level(self):
        """Return a user-friendly difficulty level based on difficulty_score."""
        if self.difficulty_score <= 0.2:
            return "Very Easy"
        elif self.difficulty_score <= 0.4:
            return "Easy"
        elif self.difficulty_score <= 0.6:
            return "Medium"
        elif self.difficulty_score <= 0.8:
            return "Hard"
        else:
            return "Very Hard"

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

class Definition(models.Model):
    flashcard = models.ForeignKey(Flashcard, related_name='definitions', on_delete=models.CASCADE)
    english_definition = models.TextField()
    vietnamese_definition = models.TextField()
    definition_synonyms = models.TextField(blank=True, null=True, help_text="Comma-separated list of synonyms for this definition")
    definition_antonyms = models.TextField(blank=True, null=True, help_text="Comma-separated list of antonyms for this definition")

    def __str__(self):
        return f"{self.flashcard.word} - {self.english_definition[:50]}..."
