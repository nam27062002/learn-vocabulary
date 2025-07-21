#!/usr/bin/env bash
# exit on error
set -o errexit

pip install -r requirements_minimal.txt

# Set production settings
export DJANGO_SETTINGS_MODULE=learn_english_project.settings_production

python manage.py collectstatic --no-input
python manage.py migrate