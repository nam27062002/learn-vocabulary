#!/usr/bin/env bash
# exit on error
set -o errexit

# Install both requirements files to ensure all dependencies
pip install -r requirements.txt
pip install -r requirements_simple.txt

# Explicitly install jwt packages
pip install PyJWT==2.10.1
pip install jwt==1.3.1
pip install python-jwt==4.0.0

# Set simple production settings (no PostgreSQL)
export DJANGO_SETTINGS_MODULE=learn_english_project.settings_simple

python manage.py collectstatic --no-input
python manage.py migrate