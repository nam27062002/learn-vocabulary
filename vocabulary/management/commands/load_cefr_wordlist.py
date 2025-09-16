"""
Management command to load CEFR-J wordlist from Excel file.

This command downloads and processes the official CEFR-J Wordlist Version 1.6
from Tokyo University of Foreign Studies.

Usage:
    python manage.py load_cefr_wordlist [--url URL] [--force]
"""

import os
import requests
import tempfile
from django.core.management.base import BaseCommand
from django.conf import settings
from vocabulary.cefr_service import cefr_classifier


class Command(BaseCommand):
    help = 'Load CEFR-J wordlist from Excel file'

    def add_arguments(self, parser):
        parser.add_argument(
            '--url',
            type=str,
            help='URL to download CEFR-J wordlist Excel file',
            default='http://www.cefr-j.org/download/cefrj_wordlist_v1_6.xlsx'
        )
        parser.add_argument(
            '--file',
            type=str,
            help='Local path to CEFR-J wordlist Excel file'
        )
        parser.add_argument(
            '--force',
            action='store_true',
            help='Force reload even if data already exists'
        )

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('Loading CEFR-J Wordlist...'))
        
        # Check if we already have data
        stats = cefr_classifier.get_statistics()
        if stats['total'] > 100 and not options['force']:
            self.stdout.write(
                self.style.WARNING(
                    f'CEFR data already loaded ({stats["total"]} words). Use --force to reload.'
                )
            )
            return
        
        # Try to load from local file first, then download
        excel_file = None
        if options['file']:
            if os.path.exists(options['file']):
                excel_file = options['file']
                self.stdout.write(f'Using local file: {excel_file}')
            else:
                self.stdout.write(self.style.ERROR(f'File not found: {options["file"]}'))
                return
        else:
            # Try to download the file
            excel_file = self.download_wordlist(options['url'])
            if not excel_file:
                self.stdout.write(
                    self.style.WARNING(
                        'Could not download CEFR-J wordlist. Using sample data instead.'
                    )
                )
                self.load_sample_data()
                return
        
        # Process the Excel file
        try:
            self.process_excel_file(excel_file)
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Error processing Excel file: {e}'))
            self.stdout.write('Loading sample data instead...')
            self.load_sample_data()
        finally:
            # Clean up downloaded file
            if not options['file'] and excel_file and os.path.exists(excel_file):
                os.unlink(excel_file)

    def download_wordlist(self, url):
        """Download CEFR-J wordlist Excel file."""
        try:
            self.stdout.write(f'Downloading from: {url}')
            response = requests.get(url, timeout=30)
            response.raise_for_status()
            
            # Save to temporary file
            with tempfile.NamedTemporaryFile(delete=False, suffix='.xlsx') as tmp_file:
                tmp_file.write(response.content)
                self.stdout.write(f'Downloaded to: {tmp_file.name}')
                return tmp_file.name
                
        except requests.RequestException as e:
            self.stdout.write(self.style.ERROR(f'Download failed: {e}'))
            return None

    def process_excel_file(self, excel_file):
        """Process CEFR-J wordlist Excel file."""
        try:
            import pandas as pd
        except ImportError:
            self.stdout.write(
                self.style.ERROR(
                    'pandas is required to process Excel files. Install with: pip install pandas openpyxl'
                )
            )
            raise
        
        self.stdout.write('Processing Excel file...')
        
        # Read all sheets (A1, A2, B1, B2, etc.)
        excel_data = pd.ExcelFile(excel_file)
        
        total_words = 0
        level_counts = {}
        
        for sheet_name in excel_data.sheet_names:
            # Skip non-level sheets
            if sheet_name not in ['A1', 'A2', 'B1', 'B2', 'C1', 'C2']:
                continue
            
            self.stdout.write(f'Processing sheet: {sheet_name}')
            
            try:
                df = pd.read_excel(excel_file, sheet_name=sheet_name)
                
                # Look for headword column (might be named differently)
                word_column = None
                for col in df.columns:
                    if 'headword' in col.lower() or 'word' in col.lower():
                        word_column = col
                        break
                
                if word_column is None:
                    self.stdout.write(f'Warning: Could not find word column in sheet {sheet_name}')
                    continue
                
                # Extract words and add to classifier
                words = df[word_column].dropna().unique()
                count = 0
                
                for word in words:
                    if isinstance(word, str) and word.strip():
                        # Clean the word (remove variants like "word1/word2")
                        clean_word = word.split('/')[0].strip().lower()
                        if clean_word:
                            cefr_classifier.add_word_to_level(clean_word, sheet_name)
                            count += 1
                
                level_counts[sheet_name] = count
                total_words += count
                self.stdout.write(f'  Added {count} words from {sheet_name}')
                
            except Exception as e:
                self.stdout.write(f'Error processing sheet {sheet_name}: {e}')
        
        # Save to cache
        cefr_classifier.update_cache()
        
        self.stdout.write(self.style.SUCCESS(f'Successfully loaded {total_words} words:'))
        for level, count in level_counts.items():
            self.stdout.write(f'  {level}: {count} words')

    def load_sample_data(self):
        """Load sample CEFR data as fallback."""
        from vocabulary.cefr_service import populate_cefr_data_from_sample
        
        self.stdout.write('Loading sample CEFR data...')
        populate_cefr_data_from_sample()
        
        stats = cefr_classifier.get_statistics()
        self.stdout.write(self.style.SUCCESS(f'Loaded sample data: {stats["total"]} words'))
        for level in ['A1', 'A2', 'B1', 'B2', 'C1', 'C2']:
            self.stdout.write(f'  {level}: {stats[level]} words')
