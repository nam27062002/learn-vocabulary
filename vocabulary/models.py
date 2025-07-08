from django.db import models
import os
from django.conf import settings

class Flashcard(models.Model):
    word = models.CharField(max_length=255, unique=True)
    phonetic = models.CharField(max_length=100, blank=True, null=True, help_text="Phonetic transcription (e.g., /rɪˈzɪliənt/)")
    part_of_speech = models.CharField(max_length=50, blank=True, null=True)
    audio_url = models.URLField(max_length=500, blank=True, null=True)
    image = models.ImageField(upload_to='flashcard_images/', blank=True, null=True)
    related_image_url = models.URLField(max_length=500, blank=True, null=True, help_text="Auto-fetched related image URL")
    general_synonyms = models.TextField(blank=True, null=True, help_text="Comma-separated list of general synonyms")
    general_antonyms = models.TextField(blank=True, null=True, help_text="Comma-separated list of general antonyms")
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.word

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

class Definition(models.Model):
    flashcard = models.ForeignKey(Flashcard, related_name='definitions', on_delete=models.CASCADE)
    english_definition = models.TextField()
    vietnamese_definition = models.TextField()
    definition_synonyms = models.TextField(blank=True, null=True, help_text="Comma-separated list of synonyms for this definition")
    definition_antonyms = models.TextField(blank=True, null=True, help_text="Comma-separated list of antonyms for this definition")

    def __str__(self):
        return f"{self.flashcard.word} - {self.english_definition[:50]}..."
