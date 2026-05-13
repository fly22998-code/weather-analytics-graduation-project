#!/bin/sh
set -e

echo "[entrypoint] Waiting for MySQL..."
python - <<'PY'
import os
import socket
import time

host = os.getenv("DB_HOST", "db")
port = int(os.getenv("DB_PORT", "3306"))
for _ in range(60):
    try:
        with socket.create_connection((host, port), timeout=2):
            print("[entrypoint] MySQL is ready")
            break
    except OSError:
        time.sleep(2)
else:
    raise SystemExit("[entrypoint] MySQL did not become ready in time")
PY

echo "[entrypoint] Running migrations..."
python manage.py migrate --noinput

echo "[entrypoint] Starting Gunicorn..."
exec gunicorn weather_project.wsgi:application --bind 0.0.0.0:8000 --workers 3
