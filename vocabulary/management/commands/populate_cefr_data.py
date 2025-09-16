"""
Management command to populate CEFR level data for flashcards.

This command:
1. Loads sample CEFR data into the classifier
2. Updates existing flashcards with CEFR levels
3. Provides statistics about the classification results
"""

from django.core.management.base import BaseCommand
from django.db import transaction
from vocabulary.models import Flashcard
from vocabulary.cefr_service import cefr_classifier, populate_cefr_data_from_sample


class Command(BaseCommand):
    help = 'Populate CEFR level data for flashcards'

    def add_arguments(self, parser):
        parser.add_argument(
            '--update-existing',
            action='store_true',
            help='Update CEFR levels for existing flashcards',
        )
        parser.add_argument(
            '--force',
            action='store_true',
            help='Force update even if CEFR level already exists',
        )

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('Starting CEFR data population...'))
        
        # Step 1: Load sample CEFR data
        self.stdout.write('Loading sample CEFR data...')
        populate_cefr_data_from_sample()
        
        # Show statistics
        stats = cefr_classifier.get_statistics()
        self.stdout.write(f'Loaded CEFR data: {stats["total"]} total words')
        for level in ['A1', 'A2', 'B1', 'B2', 'C1', 'C2']:
            self.stdout.write(f'  {level}: {stats[level]} words')
        
        # Step 2: Update existing flashcards if requested
        if options['update_existing']:
            self.stdout.write('\nUpdating existing flashcards...')
            self.update_flashcard_cefr_levels(force=options['force'])
        
        self.stdout.write(self.style.SUCCESS('\nCEFR data population completed!'))

    def update_flashcard_cefr_levels(self, force=False):
        """Update CEFR levels for existing flashcards."""
        
        # Get flashcards to update
        if force:
            flashcards = Flashcard.objects.all()
            self.stdout.write('Updating all flashcards (force mode)...')
        else:
            flashcards = Flashcard.objects.filter(cefr_level__isnull=True)
            self.stdout.write('Updating flashcards without CEFR levels...')
        
        total_cards = flashcards.count()
        if total_cards == 0:
            self.stdout.write('No flashcards to update.')
            return
        
        updated_count = 0
        level_counts = {level: 0 for level in ['A1', 'A2', 'B1', 'B2', 'C1', 'C2']}
        
        self.stdout.write(f'Processing {total_cards} flashcards...')
        
        # Process in batches to avoid memory issues
        batch_size = 100
        for i in range(0, total_cards, batch_size):
            batch = flashcards[i:i + batch_size]
            
            with transaction.atomic():
                for flashcard in batch:
                    if flashcard.update_cefr_level(save=False):
                        level_counts[flashcard.cefr_level] += 1
                        updated_count += 1
                
                # Bulk update the batch
                Flashcard.objects.bulk_update(
                    batch, 
                    ['cefr_level', 'cefr_level_auto'], 
                    batch_size=batch_size
                )
            
            # Progress indicator
            processed = min(i + batch_size, total_cards)
            self.stdout.write(f'Processed {processed}/{total_cards} flashcards...', ending='\r')
        
        self.stdout.write('')  # New line
        self.stdout.write(f'Updated {updated_count} flashcards with CEFR levels:')
        for level, count in level_counts.items():
            if count > 0:
                self.stdout.write(f'  {level}: {count} flashcards')
        
        not_classified = total_cards - updated_count
        if not_classified > 0:
            self.stdout.write(f'  Not classified: {not_classified} flashcards')
