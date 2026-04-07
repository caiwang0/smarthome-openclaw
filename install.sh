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
echo "Tell your OpenClaw bot:"
echo "  \"Help me set up SmartHub\""
echo ""
echo "It will walk you through Docker, Home Assistant,"
echo "and connecting your smart devices."
echo ""
