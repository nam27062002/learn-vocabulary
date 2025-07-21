#!/usr/bin/env bash
# exit on error
set -o errexit

pip install -r requirements_minimal.txt

# Set simple production settings (no PostgreSQL)
export DJANGO_SETTINGS_MODULE=learn_english_project.settings_simple

python manage.py collectstatic --no-input
python manage.py migrate