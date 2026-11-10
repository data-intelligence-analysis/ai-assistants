#!/bin/bash
set -e

WORKSPACE_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
COMPOSE_FILE="$WORKSPACE_DIR/docker_compose.yml"
TOKEN_PATH="$WORKSPACE_DIR/dashboard/token.json"
PORT=8501
MODE="${1:-production}"

cd "$WORKSPACE_DIR" || exit 1

if [[ "$MODE" != "test" && "$MODE" != "production" ]]; then
    echo "Usage: $0 [test|production]" >&2
    exit 2
fi

export APP_DATA_MODE="$MODE"
export APP_EMAIL_FILTER="${APP_EMAIL_FILTER:-in:inbox invoice}"

if [ "$MODE" = "production" ]; then
    if [ ! -f "$TOKEN_PATH" ]; then
        echo "Error: Required token.json missing at $TOKEN_PATH" >&2
        exit 1
    fi

    echo "Processing live Gmail authorization..."
    GOOGLE_TOKEN_JSON="$(python3 -c "
import json
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request

with open('$TOKEN_PATH') as token_file:
    token_info = json.load(token_file)
if 'https://www.googleapis.com/auth/gmail.readonly' not in token_info.get('scopes', []):
    raise SystemExit('Gmail read-only access is required. Re-authorize using dashboard/generate_token.py.')

creds = Credentials.from_authorized_user_file('$TOKEN_PATH')
if creds and creds.expired and creds.refresh_token:
    creds.refresh(Request())
    with open('$TOKEN_PATH', 'w') as f:
        f.write(creds.to_json())
print(creds.to_json())
    ")"
export GOOGLE_TOKEN_JSON
else
    unset GOOGLE_TOKEN_JSON
    echo "Starting with bundled invoice sample data..."
fi

echo "Clearing container memory footprint..."
docker compose -f "$COMPOSE_FILE" stop dashboard >/dev/null 2>&1 || true
docker compose -f "$COMPOSE_FILE" rm -f dashboard >/dev/null 2>&1 || true

echo "Starting $MODE invoice dashboard..."
RUN_OPTIONS=(-e APP_DATA_MODE -e APP_EMAIL_FILTER -p "${PORT}:8501")
if [ "$MODE" = "production" ]; then
    RUN_OPTIONS+=(-e GOOGLE_TOKEN_JSON)
fi
docker compose -f "$COMPOSE_FILE" run --build -d \
  "${RUN_OPTIONS[@]}" \
  dashboard

sleep 2.5
if command -v open >/dev/null 2>&1; then
    open "http://localhost:${PORT}"
else
    echo "Open http://localhost:${PORT} in your browser."
fi

echo "$MODE invoice dashboard is ready at http://localhost:${PORT}."
