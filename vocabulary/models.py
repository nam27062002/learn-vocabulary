from django.db import models

class Flashcard(models.Model):
    word = models.CharField(max_length=255, unique=True)
    part_of_speech = models.CharField(max_length=50, blank=True, null=True)
    audio_url = models.URLField(max_length=500, blank=True, null=True)
    image = models.ImageField(upload_to='flashcard_images/', blank=True, null=True)
    general_synonyms = models.TextField(blank=True, null=True, help_text="Comma-separated list of general synonyms")
    general_antonyms = models.TextField(blank=True, null=True, help_text="Comma-separated list of general antonyms")
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.word

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
