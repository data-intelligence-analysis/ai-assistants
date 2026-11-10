#!/usr/bin/env bash
set -euo pipefail

CODESPACE_NAME="${1:-${CODESPACE_NAME:-}}"
VOICE_TRANSCRIPT="${2:-Launch leads dashboard}"
if [[ -z "$CODESPACE_NAME" ]]; then
  printf 'Usage: bash siri_launch_leads_data.sh <codespace-name> [spoken-command]\n' >&2
  exit 2
fi

if ! command -v gh >/dev/null 2>&1; then
  printf 'GitHub CLI (gh) is required on the Mac running this script.\n' >&2
  exit 1
fi

TRANSCRIPT_BASE64="$(printf '%s' "$VOICE_TRANSCRIPT" | base64 | tr -d '\n')"
REMOTE_SCRIPT=$(cat <<'REMOTE'
set -euo pipefail
cd /workspaces/ai-assistants/agents/sales-lead-generator
VOICE_TRANSCRIPT="$(printf '%s' '__TRANSCRIPT_BASE64__' | base64 -d)"
docker build -t sales-agent-layer .
docker rm -f sales-lead-dashboard >/dev/null 2>&1 || true
docker run -d \
  --name sales-lead-dashboard \
  -p 3000:3000 \
  --env-file .env \
  -v "$(pwd)/service_account.json:/app/service_account.json:ro" \
  -v "$(pwd)/state.json:/app/state.json" \
  sales-agent-layer --voice-command "$VOICE_TRANSCRIPT"
for attempt in {1..20}; do
  if [[ "$(docker inspect --format '{{.State.Running}}' sales-lead-dashboard 2>/dev/null || true)" == "true" ]]; then
    break
  fi
  if [[ "$(docker inspect --format '{{.State.Status}}' sales-lead-dashboard 2>/dev/null || true)" == "exited" ]]; then
    docker logs sales-lead-dashboard
    exit 1
  fi
  sleep 1
done
if [[ "$(docker inspect --format '{{.State.Running}}' sales-lead-dashboard 2>/dev/null || true)" != "true" ]]; then
  docker logs sales-lead-dashboard
  printf 'Dashboard container did not stay running.\n' >&2
  exit 1
fi
REMOTE
)
REMOTE_SCRIPT="${REMOTE_SCRIPT//__TRANSCRIPT_BASE64__/$TRANSCRIPT_BASE64}"
REMOTE_SCRIPT_BASE64="$(printf '%s' "$REMOTE_SCRIPT" | base64 | tr -d '\n')"
gh codespace ssh --codespace "$CODESPACE_NAME" -- \
  "printf '%s' '$REMOTE_SCRIPT_BASE64' | base64 -d | bash"

DASHBOARD_URL=""
for attempt in {1..20}; do
  DASHBOARD_URL="$(gh codespace ports --codespace "$CODESPACE_NAME" --json sourcePort,browseUrl --jq '.[] | select(.sourcePort == 3000) | .browseUrl' | head -n 1)"
  [[ -n "$DASHBOARD_URL" ]] && break
  sleep 1
done

if [[ -z "$DASHBOARD_URL" ]]; then
  printf 'Codespaces did not provide a forwarded URL for port 3000.\n' >&2
  exit 1
fi

if [[ "$(uname -s)" == "Darwin" ]]; then
  open "$DASHBOARD_URL"
else
  printf '%s\n' "$DASHBOARD_URL"
fi
