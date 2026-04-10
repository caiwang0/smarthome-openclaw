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

echo "Patching openclaw.json (bootstrap files + ACPX cwd + model)..."

python3 -c "
import json, sys

config_path = '$CONFIG_FILE'
target = '$TARGET'

with open(config_path, 'r') as f:
    config = json.load(f)

# --- 1. Configure bootstrap-extra-files hook ---
# OpenClaw reads these files into every new session so the bot has CLAUDE.md
# rules + TOOLS.md router loaded without the user having to ask.
hooks = config.setdefault('hooks', {})
internal = hooks.setdefault('internal', {'enabled': True})
internal['enabled'] = True
entries = internal.setdefault('entries', {})

bef = entries.get('bootstrap-extra-files', {})
bef['enabled'] = True

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

# --- 2. Pin ACPX cwd to the repo subdir ---
# OpenClaw's ACPX plugin defaults cwd to agents.defaults.workspace (the
# workspace root), not the repo subdir. Claude Code then fails to find
# .claude/settings.json and \$CLAUDE_PROJECT_DIR resolves one level too
# high, so the PreToolUse approval-gate hook never fires and destructive
# ha-mcp calls (remove_automation etc.) slip past without confirmation.
plugins = config.setdefault('plugins', {})
plugin_entries = plugins.setdefault('entries', {})
acpx = plugin_entries.setdefault('acpx', {})
acpx.setdefault('enabled', True)
acpx_cfg = acpx.setdefault('config', {})
old_cwd = acpx_cfg.get('cwd', '(unset)')
acpx_cfg['cwd'] = target
if old_cwd != target:
    print('  ACPX cwd: ' + old_cwd + ' -> ' + target)
else:
    print('  ACPX cwd: already correct (' + target + ')')

# --- 3. Upgrade model if unset or Haiku ---
# Haiku ignores CRITICAL confirmation rules in CLAUDE.md. Sonnet is more
# reliable as the soft-rule first line of defense; the PreToolUse hook
# remains the authoritative deterministic gate regardless.
agents = config.setdefault('agents', {})
agents_defaults = agents.setdefault('defaults', {})
model = agents_defaults.setdefault('model', {})
current_primary = model.get('primary', '')
if not current_primary or 'haiku' in current_primary.lower():
    old = current_primary or '(unset)'
    model['primary'] = 'claude-cli/claude-sonnet-4-6'
    print('  Model: ' + old + ' -> claude-cli/claude-sonnet-4-6')
else:
    print('  Model: keeping ' + current_primary + ' (not Haiku)')

# --- 4. Clean up stale mcp.servers.ha-mcp ---
# Older install.sh versions wrote ha-mcp to openclaw.json mcp.servers AND
# .claude/settings.json. Dual registration means two ha-mcp subprocesses
# competing for the same HA WebSocket. The repo's .claude/settings.json
# is now the single source of truth; remove any stale duplicate.
mcp_section = config.get('mcp')
if mcp_section and 'servers' in mcp_section and 'ha-mcp' in mcp_section['servers']:
    del mcp_section['servers']['ha-mcp']
    print('  Removed stale mcp.servers.ha-mcp (moved to .claude/settings.json)')

with open(config_path, 'w') as f:
    json.dump(config, f, indent=2)

print('  Added bootstrap paths:', ', '.join(our_paths))
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

# --- Verify .claude/settings.json is on disk ---
# The ha-mcp MCP server definition + PreToolUse approval-gate hook registration
# are both committed in the repo at .claude/settings.json. install.sh no longer
# generates this file at runtime — we rely on the committed version as the
# single source of truth (avoids drift between install.sh heredoc and the
# checked-in file, and prevents dual ha-mcp registration). The ACPX cwd fix
# above is what makes Claude Code actually read this file.
if [ -f "$TARGET/.claude/settings.json" ]; then
  echo "Verified $TARGET/.claude/settings.json (ha-mcp server + approval-gate hook)."
else
  echo "ERROR: $TARGET/.claude/settings.json is missing."
  echo "It should be committed in the repo. Re-clone or check git status in $TARGET."
  exit 1
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
