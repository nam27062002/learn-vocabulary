"""
CLI tool to find every flashcard missing an image and generate one for it
via the local Stable Diffusion WebUI backend.

Runs strictly sequentially: the SD WebUI backend processes generations one
at a time on the GPU anyway, so there is no concurrency knob here - it would
only cause requests to queue up and time out instead of speeding anything up.
Reliability (via the retry logic in image_service.py) matters more than
throughput for this tool.

Usage:
    python manage.py generate_all_images
    python manage.py generate_all_images --dry-run
    python manage.py generate_all_images --deck-id 110
    python manage.py generate_all_images --limit 20 --start-from 50
"""

import base64
import time

from django.core.files.base import ContentFile
from django.core.management.base import BaseCommand

from vocabulary.models import Flashcard


def _format_duration(seconds: float) -> str:
    seconds = int(seconds)
    minutes, seconds = divmod(seconds, 60)
    hours, minutes = divmod(minutes, 60)
    if hours:
        return f'{hours}h{minutes:02d}m{seconds:02d}s'
    if minutes:
        return f'{minutes}m{seconds:02d}s'
    return f'{seconds}s'


class Command(BaseCommand):
    help = 'Find all flashcards missing an image and generate one for each'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='List the cards that would be processed without generating anything',
        )
        parser.add_argument(
            '--deck-id',
            type=int,
            help='Only process cards in a specific deck ID',
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
            help='Skip the first N cards (useful for resuming a previous run)',
        )

    def handle(self, *args, **options):
        dry_run = options['dry_run']
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
        self.stdout.write(f'Found {total} flashcard(s) missing an image\n')

        if total == 0:
            return

        if dry_run:
            current_deck_name = None
            for i, card in enumerate(cards, start=1):
                deck_name = card.deck.name if card.deck else 'No deck'
                if deck_name != current_deck_name:
                    current_deck_name = deck_name
                    self.stdout.write(self.style.MIGRATE_HEADING(f'\n--- {deck_name} ---'))
                self.stdout.write(f'  [{i}/{total}] {card.word}')
            self.stdout.write(f'\nDry run complete. Would generate {total} image(s). Nothing was changed.')
            return

        from vocabulary.image_service import generate_word_image

        success_count = 0
        fail_count = 0
        current_deck_name = None
        start_time = time.time()
        failed_words = []

        for i, card in enumerate(cards, start=1):
            deck_name = card.deck.name if card.deck else 'No deck'
            if deck_name != current_deck_name:
                current_deck_name = deck_name
                self.stdout.write(self.style.MIGRATE_HEADING(f'\n--- {deck_name} ---'))

            first_def = ''
            defs = card.definitions.first()
            if defs:
                first_def = defs.english_definition or ''

            elapsed = time.time() - start_time
            avg_per_card = elapsed / (i - 1) if i > 1 else None
            eta = _format_duration(avg_per_card * (total - i + 1)) if avg_per_card else '?'
            percent = (i - 1) / total * 100

            self.stdout.write(
                f'[{i}/{total}] ({percent:.0f}%) generating "{card.word}"... '
                f'(elapsed {_format_duration(elapsed)}, ETA {eta})'
            )

            try:
                b64 = generate_word_image(card.word, first_def)
            except Exception as e:
                b64 = None
                self.stdout.write(self.style.ERROR(f'  -> unexpected error: {e}'))

            if b64:
                image_bytes = base64.b64decode(b64)
                filename = f'ai_{card.word.lower().replace(" ", "_")}_{int(time.time() * 1000)}.png'
                card.image.save(filename, ContentFile(image_bytes), save=True)
                success_count += 1
                self.stdout.write(self.style.SUCCESS(f'  -> OK'))
            else:
                fail_count += 1
                failed_words.append(card.word)
                self.stdout.write(self.style.ERROR(f'  -> FAILED (no image returned after retries)'))

        total_elapsed = time.time() - start_time
        self.stdout.write(
            self.style.SUCCESS(
                f'\nDone in {_format_duration(total_elapsed)}. '
                f'Generated {success_count}/{total} image(s). Failed: {fail_count}.'
            )
        )
        if failed_words:
            self.stdout.write(self.style.WARNING(f'Failed words: {", ".join(failed_words)}'))
            self.stdout.write('Re-run the same command later to retry only the still-missing ones.')
