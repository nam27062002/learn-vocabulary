from django.db import models

# class Flashcard(models.Model):
#     word = models.CharField(max_length=255)
#     meaning = models.TextField()
#     image_url = models.URLField(max_length=500, blank=True, null=True)
    
#     # Spaced Repetition System (SRS) fields
#     ease_factor = models.FloatField(default=2.5)
#     interval = models.IntegerField(default=0)
#     repetitions = models.IntegerField(default=0)
#     next_review_date = models.DateField(auto_now_add=True) # Set to today initially

#     def __str__(self):
#         return self.word

#     class Meta:
#         ordering = ['next_review_date']
