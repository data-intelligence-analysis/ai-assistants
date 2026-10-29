#!/bin/bash

# 1. Configuration - Set your structural paths explicitly
WORKSPACE_DIR="/Users/yourusername/accounting-agent"
TOKEN_PATH="$WORKSPACE_DIR/agent/token.json"
PORT=8501

cd "$WORKSPACE_DIR" || exit 1

# 2. Silent Token Validation & Refresh Cycle
if [ -f "$TOKEN_PATH" ]; then
    echo "Processing live authorization lifecycle tokens..."
    GOOGLE_TOKEN_JSON=$(python3 -c "
import json, os
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request

creds = Credentials.from_authorized_user_file('$TOKEN_PATH')
if creds and creds.expired and creds.refresh_token:
    creds.refresh(Request())
    with open('$TOKEN_PATH', 'w') as f:
        f.write(creds.to_json())
print(creds.to_json())
")
else:
    echo "Error: Required token.json missing at $TOKEN_PATH"
    exit 1
fi

# 3. Recycle Active Ephemeral Assets
echo "Clearing container memory footprint..."
docker compose stop dashboard >/dev/null 2>&1
docker compose rm -f dashboard >/dev/null 2>&1

# 4. Inject Environment Profile and Boot invoice_dashboard_app.py
echo "Spawning containerized Streamlit dashboard application instances..."
export GOOGLE_TOKEN_JSON

# Overriding the default entrypoint to explicitly spin up invoice_dashboard_app.py
docker compose run -d \
  -p ${PORT}:8501 \
  --entrypoint "streamlit run invoice_dashboard_app.py --server.port=8501 --server.address=0.0.0.0" \
  dashboard

# 5. Open Host Workspace Window Interface
sleep 2.5
open "http://localhost:${PORT}"

echo "System lifecycle execution complete."
