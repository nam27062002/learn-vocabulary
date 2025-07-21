#!/usr/bin/env bash
# exit on error
set -o errexit

# Install requirements
pip install -r requirements.txt

# Set minimal production settings
export DJANGO_SETTINGS_MODULE=learn_english_project.settings_minimal

python manage.py collectstatic --no-input
python manage.py migrate