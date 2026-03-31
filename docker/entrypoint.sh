#!/bin/sh
set -eu

HOST="${HOST:-0.0.0.0}"
PORT="${PORT:-8011}"
WORKERS="${GUNICORN_WORKERS:-2}"
TIMEOUT="${GUNICORN_TIMEOUT:-120}"
CERT_FILE="${SSL_CERT_FILE:-/app/certs/server.crt}"
KEY_FILE="${SSL_KEY_FILE:-/app/certs/server.key}"

if [ -f "$CERT_FILE" ] && [ -f "$KEY_FILE" ]; then
  echo "Starting Gunicorn with HTTPS using ${CERT_FILE} and ${KEY_FILE}"
  exec gunicorn backend.webapp:app \
    --bind "${HOST}:${PORT}" \
    --workers "${WORKERS}" \
    --timeout "${TIMEOUT}" \
    --certfile "$CERT_FILE" \
    --keyfile "$KEY_FILE"
fi

echo "Starting Gunicorn over HTTP"
exec gunicorn backend.webapp:app \
  --bind "${HOST}:${PORT}" \
  --workers "${WORKERS}" \
  --timeout "${TIMEOUT}"
