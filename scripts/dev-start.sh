#!/bin/sh
set -e

pip install Pillow
python manage.py migrate --noinput

python manage.py shell <<'PY'
import os
from django.contrib.auth import get_user_model

User = get_user_model()
username = os.getenv("DJANGO_SUPERUSER_USERNAME", "admin")
email = os.getenv("DJANGO_SUPERUSER_EMAIL", "admin@example.com")
password = os.getenv("DJANGO_SUPERUSER_PASSWORD", "admin")

user, created = User.objects.get_or_create(
    username=username,
    defaults={
        "email": email,
        "is_staff": True,
        "is_superuser": True,
    },
)

changed = created
if not user.is_staff:
    user.is_staff = True
    changed = True
if not user.is_superuser:
    user.is_superuser = True
    changed = True
if user.email != email:
    user.email = email
    changed = True
if not user.check_password(password):
    user.set_password(password)
    changed = True

if changed:
    user.save()

print(f"Superuser ready: {username}")
PY

python manage.py runserver 0.0.0.0:8000