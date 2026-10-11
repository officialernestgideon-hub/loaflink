#!/usr/bin/env bash
# Exit on any error
set -o errexit

# Install dependencies
pip install --upgrade pip
pip install -r requirements.txt

# Collect static files (for WhiteNoise to serve)
python manage.py collectstatic --no-input

# Apply database migrations
python manage.py migrate

# Optional: create a superuser from env vars
# Only runs if you set DJANGO_SUPERUSER_PHONE and DJANGO_SUPERUSER_PASSWORD
if [[ -n "$DJANGO_SUPERUSER_PHONE" ]] && [[ -n "$DJANGO_SUPERUSER_PASSWORD" ]]; then
  python manage.py createsuperuser --noinput || echo "Superuser may already exist."
fi