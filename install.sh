#!/usr/bin/env bash
set -euo pipefail

# SmartHub for OpenClaw — One-command installer
# Usage: curl -fsSL https://raw.githubusercontent.com/caiwang0/smarthome-openclaw/main/install.sh -o /tmp/smarthub-install.sh && bash /tmp/smarthub-install.sh

REPO_URL="https://github.com/caiwang0/smarthome-openclaw.git"
REPO_DIR="smarthome-openclaw"
CONFIG_FILE="$HOME/.openclaw/openclaw.json"

# --- Detect workspace ---
if [ -n "${OPENCLAW_WORKSPACE:-}" ]; then
  WORKSPACE="$OPENCLAW_WORKSPACE"
elif [ -f "$CONFIG_FILE" ]; then
  # Try to read workspace from openclaw.json
  WORKSPACE=$(python3 -c "
import json, os
with open('$CONFIG_FILE') as f:
    c = json.load(f)
ws = c.get('agents', {}).get('defaults', {}).get('workspace', '')
print(os.path.expanduser(ws) if ws else '')
" 2>/dev/null || true)
fi

if [ -z "${WORKSPACE:-}" ]; then
  WORKSPACE="$HOME/.openclaw/workspace"
fi

if [ ! -d "$WORKSPACE" ]; then
  echo "ERROR: OpenClaw workspace not found at $WORKSPACE"
  echo "Make sure OpenClaw is installed and configured first."
  exit 1
fi

echo "Using workspace: $WORKSPACE"

# --- Clone or update repo ---
TARGET="$WORKSPACE/$REPO_DIR"

if [ -d "$TARGET/.git" ]; then
  echo "Repo already exists, pulling latest..."
  cd "$TARGET" && git pull origin main
else
  echo "Cloning smarthome-openclaw..."
  git clone "$REPO_URL" "$TARGET"
fi

# --- Patch openclaw.json to add bootstrap-extra-files ---
if [ ! -f "$CONFIG_FILE" ]; then
  echo "ERROR: openclaw.json not found at $CONFIG_FILE"
  exit 1
fi

echo "Configuring bootstrap-extra-files hook..."

python3 -c "
import json, sys

config_path = '$CONFIG_FILE'

with open(config_path, 'r') as f:
    config = json.load(f)

# Ensure hooks.internal.entries exists
hooks = config.setdefault('hooks', {})
internal = hooks.setdefault('internal', {'enabled': True})
internal['enabled'] = True
entries = internal.setdefault('entries', {})

# Configure bootstrap-extra-files
bef = entries.get('bootstrap-extra-files', {})
bef['enabled'] = True

# Merge paths — keep existing, add ours if missing
existing_paths = bef.get('paths', [])
our_paths = [
    '$REPO_DIR/CLAUDE.md',
    '$REPO_DIR/TOOLS.md'
]
for p in our_paths:
    if p not in existing_paths:
        existing_paths.append(p)

bef['paths'] = existing_paths
entries['bootstrap-extra-files'] = bef

with open(config_path, 'w') as f:
    json.dump(config, f, indent=2)

print('  Added:', ', '.join(our_paths))
"

# --- Create .env and resolve port conflicts ---
cd "$TARGET"

if [ ! -f .env ]; then
  cp .env.example .env
  echo "Created .env from .env.example."
fi

# Check if port 8123 is already in use
if ss -tlnp 2>/dev/null | grep -q ':8123 '; then
  echo "Port 8123 is in use. Finding a free port..."
  HA_PORT=""
  for port in 8124 8125 8126 8127 8128; do
    if ! ss -tlnp 2>/dev/null | grep -q ":${port} "; then
      HA_PORT=$port
      break
    fi
  done

  if [ -z "$HA_PORT" ]; then
    echo "WARNING: Could not find a free port in 8124-8128. Defaulting to 8123 (may conflict)."
    HA_PORT=8123
  else
    echo "Assigning HA to port ${HA_PORT}."

    # Write server_port to ha-config/configuration.yaml (only if fresh install)
    mkdir -p ha-config
    if [ ! -s ha-config/configuration.yaml ]; then
      printf "http:\n  server_port: %s\n" "${HA_PORT}" > ha-config/configuration.yaml
      echo "Wrote server_port: ${HA_PORT} to ha-config/configuration.yaml."
    else
      echo "WARNING: ha-config/configuration.yaml already exists."
      echo "Add this manually under the http: section before starting HA:"
      echo "  server_port: ${HA_PORT}"
    fi

    # Update HA_URL in .env
    sed -i "s|HA_URL=.*|HA_URL=http://localhost:${HA_PORT}|" .env
    echo "Updated HA_URL to http://localhost:${HA_PORT} in .env."
  fi
else
  echo "Port 8123 is free."
fi

# Check API port conflict
API_PORT=$(grep API_PORT .env | cut -d= -f2)
API_PORT=${API_PORT:-3001}
if ss -tlnp 2>/dev/null | grep -q ":${API_PORT} "; then
  for port in $(seq $((API_PORT + 1)) $((API_PORT + 10))); do
    if ! ss -tlnp 2>/dev/null | grep -q ":${port} "; then
      sed -i "s|API_PORT=.*|API_PORT=${port}|" .env
      echo "API port conflict: reassigned to ${port}."
      break
    fi
  done
fi

cd - > /dev/null

# --- Install npm dependencies for the SmartHub API ---
if [ -f "$TARGET/api/package.json" ]; then
  echo "Installing API dependencies..."
  cd "$TARGET/api" && npm install --silent 2>/dev/null || true
fi

# --- Restart gateway if running ---
GATEWAY_PID=$(pgrep -f "openclaw-gateway" 2>/dev/null | head -1 || true)

if [ -n "$GATEWAY_PID" ]; then
  echo "Restarting OpenClaw gateway (PID $GATEWAY_PID)..."
  kill "$GATEWAY_PID" 2>/dev/null || true
  sleep 2
  nohup "$(which openclaw 2>/dev/null || echo "$HOME/.npm-global/bin/openclaw")" gateway > /tmp/openclaw-gateway.log 2>&1 &
  sleep 3
  echo "Gateway restarted."
else
  echo "No running gateway found. Start it with: openclaw gateway"
fi

echo ""
echo "============================================"
echo "  SmartHub installed successfully!"
echo "============================================"
echo ""
echo ""
echo "============================================"
echo "  SmartHub installed!"
echo "============================================"
echo ""
echo "NEXT: Read ${TARGET}/tools/setup.md and follow it"
echo "step by step to complete the setup. Start from"
echo "Step 2 (Docker check) — port conflicts and .env"
echo "are already resolved."
echo ""
