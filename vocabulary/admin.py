from django.contrib import admin
from .models import Flashcard, Definition, Deck

@admin.register(Deck)
class DeckAdmin(admin.ModelAdmin):
    list_display = ['name', 'user', 'created_at', 'flashcard_count']
    list_filter = ['created_at', 'user']
    search_fields = ['name', 'user__username']
    readonly_fields = ['created_at']

    def flashcard_count(self, obj):
        return obj.flashcards.count()
    flashcard_count.short_description = 'Cards'

@admin.register(Flashcard)
class FlashcardAdmin(admin.ModelAdmin):
    list_display = [
        'word', 'user', 'deck', 'difficulty_level', 'accuracy_percentage',
        'total_reviews', 'times_seen_today', 'next_review', 'last_reviewed'
    ]
    list_filter = [
        'deck', 'difficulty_score', 'next_review', 'last_reviewed',
        'times_seen_today', 'created_at'
    ]
    search_fields = ['word', 'user__username', 'deck__name']
    readonly_fields = [
        'created_at', 'last_reviewed', 'last_seen_date', 'total_reviews',
        'correct_reviews', 'times_seen_today', 'difficulty_level', 'accuracy_percentage'
    ]

    fieldsets = (
        ('Basic Information', {
            'fields': ('user', 'deck', 'word', 'phonetic', 'part_of_speech')
        }),
        ('Media', {
            'fields': ('audio_url', 'image', 'related_image_url'),
            'classes': ('collapse',)
        }),
        ('Spaced Repetition', {
            'fields': (
                'ease_factor', 'repetitions', 'interval', 'next_review', 'last_reviewed'
            )
        }),
        ('Enhanced Tracking', {
            'fields': (
                'difficulty_score', 'difficulty_level', 'total_reviews', 'correct_reviews',
                'accuracy_percentage', 'times_seen_today', 'last_seen_date'
            ),
            'classes': ('collapse',)
        }),
        ('Synonyms & Antonyms', {
            'fields': ('general_synonyms', 'general_antonyms'),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('created_at',),
            'classes': ('collapse',)
        })
    )

    def difficulty_level(self, obj):
        return obj.difficulty_level
    difficulty_level.short_description = 'Difficulty'

    def accuracy_percentage(self, obj):
        return f"{obj.accuracy_percentage}%"
    accuracy_percentage.short_description = 'Accuracy'

@admin.register(Definition)
class DefinitionAdmin(admin.ModelAdmin):
    list_display = ['flashcard', 'english_definition_short', 'vietnamese_definition_short']
    list_filter = ['flashcard__deck', 'flashcard__user']
    search_fields = ['flashcard__word', 'english_definition', 'vietnamese_definition']

    def english_definition_short(self, obj):
        return obj.english_definition[:50] + "..." if len(obj.english_definition) > 50 else obj.english_definition
    english_definition_short.short_description = 'English Definition'

    def vietnamese_definition_short(self, obj):
        return obj.vietnamese_definition[:50] + "..." if len(obj.vietnamese_definition) > 50 else obj.vietnamese_definition
    vietnamese_definition_short.short_description = 'Vietnamese Definition'
