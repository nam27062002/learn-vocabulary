"""
Management command to generate AI images for all flashcards that don't have one.
Uses gpt-image-1 via the LLM proxy with concurrent requests (max 3).
"""

import time
import os
from concurrent.futures import ThreadPoolExecutor, as_completed
from io import BytesIO

from django.core.management.base import BaseCommand
from django.core.files.base import ContentFile

from vocabulary.models import Flashcard, Deck


class Command(BaseCommand):
    help = 'Generate AI images for all flashcards missing images'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be generated without making changes',
        )
        parser.add_argument(
            '--concurrency',
            type=int,
            default=3,
            help='Max concurrent image generation requests (default: 3)',
        )
        parser.add_argument(
            '--deck-id',
            type=int,
            help='Only generate for a specific deck ID',
        )
        parser.add_argument(
            '--limit',
            type=int,
            help='Limit the number of images to generate',
        )
        parser.add_argument(
            '--start-from',
            type=int,
            default=0,
            help='Skip the first N cards (resume from position)',
        )

    def handle(self, *args, **options):
        dry_run = options['dry_run']
        concurrency = options['concurrency']
        deck_id = options['deck_id']
        limit = options['limit']
        start_from = options['start_from']

        qs = Flashcard.objects.filter(
            image=''
        ).select_related('deck').order_by('deck__id', 'id')

        if deck_id:
            qs = qs.filter(deck_id=deck_id)

        cards = list(qs)

        if start_from > 0:
            cards = cards[start_from:]

        if limit:
            cards = cards[:limit]

        total = len(cards)
        self.stdout.write(f'Found {total} flashcards without images')

        if dry_run:
            for i, card in enumerate(cards):
                deck_name = card.deck.name if card.deck else 'No deck'
                first_def = ''
                defs = card.definitions.first()
                if defs:
                    first_def = defs.english_definition or ''
                self.stdout.write(f'  [{i+1}] {deck_name} | {card.word} | def: {first_def[:60]}...')
            self.stdout.write(f'\nDry run complete. Would generate {total} images.')
            return

        from vocabulary.image_service import generate_word_image

        success_count = 0
        fail_count = 0
        current_deck_name = None

        def gen_image(card_data):
            card_id, word, definition = card_data
            b64 = generate_word_image(word, definition)
            return card_id, word, b64

        card_data_list = []
        for card in cards:
            first_def = ''
            defs = card.definitions.first()
            if defs:
                first_def = defs.english_definition or ''
            card_data_list.append((card.id, card.word, first_def))

        with ThreadPoolExecutor(max_workers=concurrency) as executor:
            futures = {}
            for i, cd in enumerate(card_data_list):
                future = executor.submit(gen_image, cd)
                futures[future] = (i, cd, cards[i])

            for future in as_completed(futures):
                idx, cd, card = futures[future]
                card_id, word, _ = cd
                deck_name = card.deck.name if card.deck else 'No deck'

                if deck_name != current_deck_name:
                    current_deck_name = deck_name
                    self.stdout.write(self.style.MIGRATE_HEADING(f'\n--- {deck_name} ---'))

                try:
                    _, _, b64 = future.result()
                    if b64:
                        import base64
                        image_bytes = base64.b64decode(b64)
                        filename = f'ai_{word.lower().replace(" ", "_")}_{int(time.time() * 1000)}.png'
                        card.image.save(filename, ContentFile(image_bytes), save=True)
                        success_count += 1
                        self.stdout.write(
                            self.style.SUCCESS(f'  [{success_count + fail_count}/{total}] OK {word}')
                        )
                    else:
                        fail_count += 1
                        self.stdout.write(
                            self.style.ERROR(f'  [{success_count + fail_count}/{total}] FAIL {word} (no image returned)')
                        )
                except Exception as e:
                    fail_count += 1
                    self.stdout.write(
                        self.style.ERROR(f'  [{success_count + fail_count}/{total}] FAIL {word} ({e})')
                    )

        self.stdout.write(self.style.SUCCESS(
            f'\nDone! Generated {success_count}/{total} images. Failed: {fail_count}'
        ))
