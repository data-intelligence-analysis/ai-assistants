#!/usr/bin/env bash
set -euo pipefail

# execute the shell script
# chmod +x siri_launch_leads_data.sh

# Capture the voice text passed by the Apple Shortcut (defaults if empty)
VOICE_TRANSCRIPT="${1:-Launch leads dashboard}"

# 1. Navigate to your local project directory
cd /workspaces/ai-assistants/agents/sales-lead-generator

# 2. Build the local Dockerfile blueprint
docker build -t sales-agent-layer .

# 3. Normalize voice input to lowercase for easier keyword matching
TRANSCRIPT_LOWER=$(printf '%s' "$VOICE_TRANSCRIPT" | tr '[:upper:]' '[:lower:]')

if [[ "$TRANSCRIPT_LOWER" =~ "voice" || "$TRANSCRIPT_LOWER" =~ "speak" || "$TRANSCRIPT_LOWER" =~ "tell me" ]]; then
  
  # ==========================================
  # VOICE INTENT: Run a short-lived container
  # ==========================================
  # We prefix with SPEAK| so your local Apple Shortcut knows to read it aloud
  printf "SPEAK|"
  docker run --rm \
    --env-file .env \
    -v "$(pwd)/service_account.json:/app/service_account.json:ro" \
    -v "$(pwd)/state.json:/app/state.json" \
    sales-agent-layer --voice-command "$VOICE_TRANSCRIPT"

else
  
  # ==========================================
  # BROWSER INTENT: Launch a persistent web app
  # ==========================================
  docker rm -f sales-lead-dashboard >/dev/null 2>&1 || true
  
  # Run container mapping port 3000 directly to your Mac localhost
  docker run -d \
    --name sales-lead-dashboard \
    -p 3000:3000 \
    --env-file .env \
    -v "$(pwd)/service_account.json:/app/service_account.json:ro" \
    -v "$(pwd)/state.json:/app/state.json" \
    sales-agent-layer --voice-command "$VOICE_TRANSCRIPT"

  # Container health check loop
  for attempt in {1..10}; do
    if [[ "$(docker inspect --format '{{.State.Running}}' sales-lead-dashboard 2>/dev/null || true)" == "true" ]]; then
      break
    fi
    sleep 0.5
  done

  if [[ "$(docker inspect --format '{{.State.Running}}' sales-lead-dashboard 2>/dev/null || true)" != "true" ]]; then
    docker logs sales-lead-dashboard >&2
    printf 'Error: Local dashboard container failed to stay running.\n' >&2
    exit 1
  fi
  
  # Open your local web browser directly to localhost
  if [[ "$(uname -s)" == "Darwin" ]]; then
    open "http://localhost:3000"
  else
    printf 'Dashboard running at: http://localhost:3000\n'
  fi
fi
