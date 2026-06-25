#!/bin/sh
set -e

if [ -n "$MYSQL_HOST" ]; then
  echo "Waiting for MySQL at $MYSQL_HOST:${MYSQL_PORT:-3306}..."
  python - <<'PY'
import os
import socket
import time

host = os.environ["MYSQL_HOST"]
port = int(os.environ.get("MYSQL_PORT", "3306"))
while True:
    try:
        with socket.create_connection((host, port), timeout=1):
            break
    except OSError:
        time.sleep(1)
PY
fi

python manage.py collectstatic --noinput

exec "$@"
