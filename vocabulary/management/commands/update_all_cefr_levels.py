"""
Management command to update CEFR levels for ALL flashcards.

This command:
1. Updates flashcards that have exact matches in CEFR database
2. Uses fallback classification for words not in database
3. Ensures every flashcard has a CEFR level
"""

from django.core.management.base import BaseCommand
from django.db import transaction
from vocabulary.models import Flashcard
from vocabulary.cefr_service import cefr_classifier


class Command(BaseCommand):
    help = 'Update CEFR levels for ALL flashcards (including fallback classification)'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be updated without making changes',
        )
        parser.add_argument(
            '--user-id',
            type=int,
            help='Update flashcards for specific user only',
        )

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('Starting comprehensive CEFR level update...'))
        
        # Get flashcards to update
        if options['user_id']:
            flashcards = Flashcard.objects.filter(user_id=options['user_id'])
            self.stdout.write(f'Updating flashcards for user ID: {options["user_id"]}')
        else:
            flashcards = Flashcard.objects.all()
            self.stdout.write('Updating flashcards for ALL users')
        
        total_cards = flashcards.count()
        if total_cards == 0:
            self.stdout.write('No flashcards to update.')
            return
        
        self.stdout.write(f'Processing {total_cards} flashcards...')
        
        # Statistics
        updated_count = 0
        exact_matches = 0
        fallback_classifications = 0
        level_counts = {level: 0 for level in ['A1', 'A2', 'B1', 'B2', 'C1', 'C2']}
        
        # Process in batches
        batch_size = 100
        for i in range(0, total_cards, batch_size):
            batch = list(flashcards[i:i + batch_size])
            
            if not options['dry_run']:
                with transaction.atomic():
                    for flashcard in batch:
                        old_level = flashcard.cefr_level
                        
                        # Get CEFR level (with fallback)
                        new_level = cefr_classifier.get_word_level(flashcard.word)
                        
                        if new_level:
                            # Check if this was an exact match or fallback
                            exact_match = self._is_exact_match(flashcard.word, new_level)
                            
                            flashcard.cefr_level = new_level
                            flashcard.cefr_level_auto = True
                            
                            level_counts[new_level] += 1
                            updated_count += 1
                            
                            if exact_match:
                                exact_matches += 1
                            else:
                                fallback_classifications += 1
                            
                            if old_level != new_level:
                                self.stdout.write(
                                    f'  {flashcard.word}: {old_level or "None"} → {new_level}'
                                    f' {"(exact)" if exact_match else "(fallback)"}'
                                )
                    
                    # Bulk update the batch
                    Flashcard.objects.bulk_update(
                        batch, 
                        ['cefr_level', 'cefr_level_auto'], 
                        batch_size=batch_size
                    )
            else:
                # Dry run - just show what would be updated
                for flashcard in batch:
                    new_level = cefr_classifier.get_word_level(flashcard.word)
                    if new_level and flashcard.cefr_level != new_level:
                        exact_match = self._is_exact_match(flashcard.word, new_level)
                        self.stdout.write(
                            f'  Would update {flashcard.word}: {flashcard.cefr_level or "None"} → {new_level}'
                            f' {"(exact)" if exact_match else "(fallback)"}'
                        )
                        updated_count += 1
                        level_counts[new_level] += 1
                        
                        if exact_match:
                            exact_matches += 1
                        else:
                            fallback_classifications += 1
            
            # Progress indicator
            processed = min(i + batch_size, total_cards)
            self.stdout.write(f'Processed {processed}/{total_cards} flashcards...', ending='\r')
        
        self.stdout.write('')  # New line
        
        # Summary
        if options['dry_run']:
            self.stdout.write(self.style.WARNING('DRY RUN - No changes were made'))
        
        self.stdout.write(self.style.SUCCESS(f'Update completed!'))
        self.stdout.write(f'Total flashcards processed: {total_cards}')
        self.stdout.write(f'Flashcards updated: {updated_count}')
        self.stdout.write(f'Exact matches: {exact_matches}')
        self.stdout.write(f'Fallback classifications: {fallback_classifications}')
        
        self.stdout.write('\nCEFR Level Distribution:')
        for level, count in level_counts.items():
            if count > 0:
                self.stdout.write(f'  {level}: {count} flashcards')
        
        not_classified = total_cards - updated_count
        if not_classified > 0:
            self.stdout.write(f'  Not classified: {not_classified} flashcards')

    def _is_exact_match(self, word, level):
        """Check if the word was found as an exact match in CEFR database."""
        word_clean = word.lower().strip()
        return word_clean in cefr_classifier.wordlist_data[level]
