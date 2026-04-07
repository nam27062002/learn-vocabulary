from django.db import models
from django.conf import settings


class DictationVideo(models.Model):
    SOURCE_CC = 'cc'
    SOURCE_AUTO = 'auto'
    SOURCE_CHOICES = [
        (SOURCE_CC, 'Official CC'),
        (SOURCE_AUTO, 'Auto-generated'),
    ]

    video_id = models.CharField(max_length=20, unique=True)
    title = models.CharField(max_length=500)
    thumbnail_url = models.URLField(blank=True)
    channel_name = models.CharField(max_length=200, blank=True)
    duration_seconds = models.IntegerField(null=True, blank=True)
    subtitle_source = models.CharField(max_length=10, choices=SOURCE_CHOICES, default=SOURCE_AUTO)
    added_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='dictation_videos',
    )
    created_at = models.DateTimeField(auto_now_add=True)
    is_processed = models.BooleanField(default=False)
    segment_count = models.IntegerField(default=0)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return self.title or self.video_id

    @property
    def youtube_url(self):
        return f'https://www.youtube.com/watch?v={self.video_id}'

    @property
    def duration_display(self):
        if not self.duration_seconds:
            return ''
        minutes, seconds = divmod(self.duration_seconds, 60)
        hours, minutes = divmod(minutes, 60)
        if hours:
            return f'{hours}:{minutes:02d}:{seconds:02d}'
        return f'{minutes}:{seconds:02d}'


class DictationSegment(models.Model):
    video = models.ForeignKey(DictationVideo, related_name='segments', on_delete=models.CASCADE)
    order = models.IntegerField()
    start_time = models.FloatField()
    end_time = models.FloatField()
    transcript = models.TextField()
    word_count = models.IntegerField(default=0)

    class Meta:
        ordering = ['order']
        unique_together = ['video', 'order']

    def __str__(self):
        return f'{self.video.title} – Segment {self.order}'

    @property
    def duration(self):
        return round(self.end_time - self.start_time, 2)


class DictationAttempt(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='dictation_attempts',
    )
    segment = models.ForeignKey(DictationSegment, on_delete=models.CASCADE, related_name='attempts')
    user_input = models.TextField()
    score = models.FloatField()
    revealed_answer = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        indexes = [
            models.Index(fields=['user', 'segment']),
            models.Index(fields=['user', 'created_at']),
        ]
        # Keep only latest attempt per user+segment for progress tracking
        # (multiple attempts allowed, we just query the latest)

    def __str__(self):
        return f'{self.user} – Seg {self.segment_id} – {self.score:.0%}'


class VideoQuiz(models.Model):
    video = models.ForeignKey(
        DictationVideo,
        on_delete=models.CASCADE,
        related_name='quizzes',
    )
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f'Quiz for {self.video.title}'


class QuizQuestion(models.Model):
    CHOICE_VALUES = [('a', 'A'), ('b', 'B'), ('c', 'C'), ('d', 'D')]

    quiz = models.ForeignKey(VideoQuiz, on_delete=models.CASCADE, related_name='questions')
    order = models.IntegerField()
    question_text = models.TextField()
    choice_a = models.CharField(max_length=500)
    choice_b = models.CharField(max_length=500)
    choice_c = models.CharField(max_length=500)
    choice_d = models.CharField(max_length=500)
    correct_choice = models.CharField(max_length=1, choices=CHOICE_VALUES)

    class Meta:
        ordering = ['order']
        unique_together = ['quiz', 'order']

    def __str__(self):
        return f'Q{self.order}: {self.question_text[:60]}'


class UserQuizAttempt(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='quiz_attempts',
    )
    quiz = models.ForeignKey(VideoQuiz, on_delete=models.CASCADE, related_name='attempts')
    answers = models.JSONField()   # {"1": "b", "2": "a", ...}  key = str(question.order)
    score = models.FloatField()    # 0.0 – 1.0
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        indexes = [
            models.Index(fields=['user', 'quiz']),
        ]

    def __str__(self):
        return f'{self.user} – Quiz {self.quiz_id} – {self.score:.0%}'
