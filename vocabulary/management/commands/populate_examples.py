"""
Management command to populate example sentences for all flashcards.
Uses word_details_service (Cambridge first, LLM fallback).
"""
import logging
from django.core.management.base import BaseCommand
from django.db.models import Q
from vocabulary.models import Flashcard
from vocabulary.word_details_service import get_word_details

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Populate example sentences for flashcards that are missing them'

    def add_arguments(self, parser):
        parser.add_argument('--dry-run', action='store_true',
            help='Show what would be updated without writing to DB')
        parser.add_argument('--force', action='store_true',
            help='Re-generate examples even if already present')
        parser.add_argument('--limit', type=int,
            help='Process at most N flashcards (applied after --force filter)')

    def handle(self, *args, **options):
        dry_run = options['dry_run']
        force = options['force']
        limit = options['limit']

        qs = Flashcard.objects.all().order_by('id')
        if not force:
            qs = qs.filter(Q(example_sentence__isnull=True) | Q(example_sentence=''))
        if limit:
            qs = qs[:limit]

        cards = list(qs)
        total = len(cards)
        self.stdout.write(f'Found {total} flashcard(s) to process')

        if dry_run:
            for card in cards:
                self.stdout.write(f'  [dry-run] {card.word}')
            self.stdout.write(f'\nDry run complete. Would process {total} card(s).')
            return

        success, fail = 0, 0
        for i, card in enumerate(cards, 1):
            try:
                data = get_word_details(card.word)
                example = data.get('example_sentence', '')
                source = data.get('example_source', '')
                if example:
                    card.example_sentence = example
                    card.example_source = source
                    card.save(update_fields=['example_sentence', 'example_source'])
                    success += 1
                    self.stdout.write(
                        self.style.SUCCESS(f'  [{i}/{total}] {card.word} -> {source}')
                    )
                else:
                    fail += 1
                    self.stdout.write(
                        self.style.WARNING(f'  [{i}/{total}] {card.word} -> no example returned')
                    )
            except Exception as e:
                fail += 1
                logger.warning('populate_examples: skipping %s due to error: %s', card.word, e)
                self.stdout.write(
                    self.style.ERROR(f'  [{i}/{total}] {card.word} -> ERROR: {e}')
                )

        self.stdout.write(self.style.SUCCESS(
            f'\nDone! Updated {success}/{total}. Failed/skipped: {fail}'
        ))
