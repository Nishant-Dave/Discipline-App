#!/usr/bin/env bash
# exit on error
set -o errexit

pip install -r requirements.txt

# Compile Tailwind v4 Standalone
python manage.py tailwind build

python manage.py collectstatic --no-input
python manage.py migrate