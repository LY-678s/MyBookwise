#!/bin/sh
set -e

if [ -n "$MYSQL_HOST" ]; then
  echo "Waiting for MySQL at $MYSQL_HOST:${MYSQL_PORT:-3306}..."
  until nc -z "$MYSQL_HOST" "${MYSQL_PORT:-3306}"; do
    sleep 1
  done
fi

python manage.py collectstatic --noinput

exec "$@"
