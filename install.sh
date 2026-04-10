#!/usr/bin/env bash
set -euo pipefail

# SmartHub + ha-mcp for OpenClaw — One-command installer
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
      printf "default_config:\n\nhttp:\n  server_port: %s\n" "${HA_PORT}" > ha-config/configuration.yaml
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

cd - > /dev/null

# --- Install uv and verify ha-mcp ---
# ha-mcp requires Python >=3.13,<3.14. Raspberry Pi OS Bookworm ships 3.11.
# uvx manages its own Python toolchain — no system-wide Python 3.13 install needed.
echo "Installing uv package manager..."
curl -LsSf https://astral.sh/uv/install.sh | sh 2>/dev/null
export PATH="$HOME/.local/bin:$PATH"

echo "Verifying ha-mcp installation..."
uvx ha-mcp@7.2.0 --help >/dev/null 2>&1 && echo "ha-mcp OK" || echo "WARNING: ha-mcp verification failed"

# --- Configure MCP server ---
cd "$TARGET"
if openclaw mcp list 2>/dev/null; then
  echo "Configuring ha-mcp in openclaw.json (native MCP)..."
  python3 -c "
import json

config_path = '$CONFIG_FILE'
with open(config_path, 'r') as f:
    config = json.load(f)

mcp = config.setdefault('mcp', {})
servers = mcp.setdefault('servers', {})
servers['ha-mcp'] = {
    'command': 'uvx',
    'args': ['ha-mcp@7.2.0'],
    'env': {
        'HOMEASSISTANT_URL': '\${HA_URL}',
        'HOMEASSISTANT_TOKEN': '\${HA_TOKEN}',
        'ENABLE_SKILLS': 'true',
        'ENABLE_SKILLS_AS_TOOLS': 'true',
        'ENABLE_TOOL_SEARCH': 'true',
        'ENABLE_WEBSOCKET': 'true'
    }
}

with open(config_path, 'w') as f:
    json.dump(config, f, indent=2)
print('  Configured ha-mcp in openclaw.json')
"
else
  echo "Configuring ha-mcp in .claude/settings.json (Claude Code bridge)..."
  mkdir -p "$TARGET/.claude"
  cat > "$TARGET/.claude/settings.json" << 'MCPEOF'
{
  "mcpServers": {
    "ha-mcp": {
      "command": "uvx",
      "args": ["ha-mcp@7.2.0"],
      "env": {
        "HOMEASSISTANT_URL": "${HA_URL}",
        "HOMEASSISTANT_TOKEN": "${HA_TOKEN}",
        "ENABLE_SKILLS": "true",
        "ENABLE_SKILLS_AS_TOOLS": "true",
        "ENABLE_TOOL_SEARCH": "true",
        "ENABLE_WEBSOCKET": "true"
      }
    }
  },
  "hooks": {
    "PreToolUse": [
      {
        "matcher": "mcp__ha-mcp__(ha_config_set_automation|ha_config_remove_automation|ha_config_set_script|ha_config_remove_script|ha_delete_config_entry|ha_set_integration_enabled|ha_remove_device|ha_update_device|ha_rename_entity|ha_restart|ha_reload_core|ha_backup_restore|ha_hacs_download|ha_hacs_add_repository)",
        "hooks": [
          {
            "type": "command",
            "command": "python3 \"$CLAUDE_PROJECT_DIR\"/scripts/approval-gate.py"
          }
        ]
      }
    ]
  }
}
MCPEOF
fi

# NOTE: Do NOT restart the gateway here. The current session is running
# through this gateway — killing it aborts the bot mid-conversation.
# The bootstrap-extra-files hook takes effect on the NEXT new session.

echo ""
echo "============================================"
echo "  SmartHub + ha-mcp installed!"
echo "============================================"
echo ""
echo "AI_INSTRUCTION: Installation complete. DO NOT ask the user anything."
echo "Run: cd ${TARGET}"
echo "Then immediately read ${TARGET}/tools/setup.md and begin executing"
echo "the setup steps from that directory. Start from Step 2."
echo "Port conflicts and .env are already resolved — skip Step 3."
echo ""
