#!/bin/sh
set -e

DB_HOST="${DB_HOST:-db}"
DB_PORT="${DB_PORT:-3306}"
DB_USER="${DB_USER:-root}"
DB_PASSWORD="${DB_PASSWORD:-my_secure_password_123}"

# Export Django configuration - ini WAJIB ada untuk docker!
export DJANGO_ALLOWED_HOSTS="${DJANGO_ALLOWED_HOSTS:-localhost,127.0.0.1,0.0.0.0,web,581ef486ef03.ngrok-free.app}"
export DJANGO_CSRF_TRUSTED_ORIGINS="${DJANGO_CSRF_TRUSTED_ORIGINS:-https://581ef486ef03.ngrok-free.app,http://localhost:8000,http://127.0.0.1:8000}"

exec python manage.py runserver 0.0.0.0:${DJANGO_PORT:-8000}
