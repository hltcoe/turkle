#!/bin/bash
set -e

printenv > /etc/environment

ADDITIONAL_FLAGS=""

if [ ! -z $WORKERS ]; then
    ADDITIONAL_FLAGS="${ADDITIONAL_FLAGS} --workers=${WORKERS}"
fi

if [ ! -z $CONNECTIONS ]; then
    ADDITIONAL_FLAGS="${ADDITIONAL_FLAGS} --worker-connections=${CONNECTIONS}"
fi

if [ ! -z $THREADS ]; then
    ADDITIONAL_FLAGS="${ADDITIONAL_FLAGS} --threads=${THREADS}"
fi

if [ "$TURKLE_DATABASE_BACKEND" = "MySQL" ]; then
  echo "Waiting for MySQL at $TURKLE_DB_HOST:3306..."
  wait-for-it.sh "$TURKLE_DB_HOST:3306" --timeout=60 --strict -- echo "MySQL is up"
fi

python manage.py migrate --noinput
cron &
gunicorn --env TURKLE_DOCKER=1 ${ADDITIONAL_FLAGS} --capture-output --bind 0.0.0.0:8080 turkle_site.wsgi
