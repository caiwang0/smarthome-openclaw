run_linux_guest_install() {
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

mkdir -p "$WORKSPACE"

echo "Using workspace: $WORKSPACE"

# --- Clone or update repo ---
TARGET="$WORKSPACE/$REPO_DIR"
INSTALL_STATE_FILE="$TARGET/$INSTALL_STATE_REL"

is_missing_or_placeholder_token() {
  local token="${1:-}"
  [ -z "$token" ] || [ "$token" = "$PLACEHOLDER_TOKEN" ]
}

read_install_state_field() {
  local field="$1"
  python3 - "$INSTALL_STATE_FILE" "$field" <<'PY'
import json
import sys
from pathlib import Path

path = Path(sys.argv[1])
field = sys.argv[2]
if not path.is_file():
    raise SystemExit(0)

try:
    payload = json.loads(path.read_text())
except json.JSONDecodeError:
    raise SystemExit(0)

value = payload.get(field, "")
if value is None:
    value = ""
print(value)
PY
}

write_install_state() {
  local phase="$1"
  local token="${2:-}"
  local username="${3:-}"
  local name="${4:-}"
  OPENCLAW_INSTALL_PHASE="$phase" \
  OPENCLAW_INSTALL_TOKEN="$token" \
  OPENCLAW_INSTALL_USERNAME="$username" \
  OPENCLAW_INSTALL_NAME="$name" \
  python3 - "$INSTALL_STATE_FILE" <<'PY'
import json
import os
import sys
import tempfile
from pathlib import Path

path = Path(sys.argv[1])
path.parent.mkdir(parents=True, exist_ok=True)
path.parent.chmod(0o700)

payload = {"phase": os.environ["OPENCLAW_INSTALL_PHASE"]}
for key, env_name in (
    ("token", "OPENCLAW_INSTALL_TOKEN"),
    ("username", "OPENCLAW_INSTALL_USERNAME"),
    ("name", "OPENCLAW_INSTALL_NAME"),
):
    value = os.environ.get(env_name, "")
    if value:
        payload[key] = value

with tempfile.NamedTemporaryFile(
    mode="w",
    encoding="utf-8",
    dir=path.parent,
    prefix=f".{path.name}.",
    delete=False,
) as tmp:
    json.dump(payload, tmp)
    tmp.write("\n")
    temp_path = Path(tmp.name)

temp_path.chmod(0o600)
temp_path.replace(path)
PY
}

clear_install_state() {
  rm -f "$INSTALL_STATE_FILE"
}

sync_env_token() {
  local token="$1"
  python3 - ".env" "$token" <<'PY'
import stat
import sys
import tempfile
from pathlib import Path

path = Path(sys.argv[1])
token = sys.argv[2]
existing_mode = stat.S_IMODE(path.stat().st_mode) if path.exists() else 0o600
lines = path.read_text().splitlines() if path.exists() else []

updated = []
replaced = False
for line in lines:
    if line.startswith("HA_TOKEN="):
        updated.append("HA_TOKEN=" + token)
        replaced = True
    else:
        updated.append(line)

if not replaced:
    updated.append("HA_TOKEN=" + token)

with tempfile.NamedTemporaryFile(
    mode="w",
    encoding="utf-8",
    dir=path.parent,
    prefix=f".{path.name}.",
    delete=False,
) as tmp:
    tmp.write("\n".join(updated) + "\n")
    temp_path = Path(tmp.name)

temp_path.chmod(existing_mode or 0o600)
temp_path.replace(path)
PY
}

CURRENT_PHASE=""
SEED_JSON_FILE=""
SEED_ERR_FILE=""

start_phase() {
  CURRENT_PHASE="$1"
  echo "[install] START: $CURRENT_PHASE"
}

complete_phase() {
  local phase="${1:-$CURRENT_PHASE}"
  echo "[install] DONE: $phase"
  CURRENT_PHASE=""
}

report_phase_failure() {
  local rc="$1"
  if [ "$rc" -ne 0 ] && [ -n "${CURRENT_PHASE:-}" ]; then
    echo "[install] FAILED: $CURRENT_PHASE"
  fi
}

cleanup_seed_json() {
  if [ -n "${SEED_JSON_FILE:-}" ] && [ -f "$SEED_JSON_FILE" ]; then
    rm -f "$SEED_JSON_FILE"
  fi
  if [ -n "${SEED_ERR_FILE:-}" ] && [ -f "$SEED_ERR_FILE" ]; then
    rm -f "$SEED_ERR_FILE"
  fi
}

on_install_exit() {
  local rc="$1"
  cleanup_seed_json
  report_phase_failure "$rc"
}

trap 'on_install_exit $?' EXIT

start_phase "repo sync"
if [ "${SMARTHUB_BOOTSTRAP_REEXEC:-0}" = "1" ] && [ "$SCRIPT_DIR" = "$TARGET" ] && [ -d "$TARGET/.git" ]; then
  echo "Repo already bootstrapped by install.sh."
else
  if [ -d "$TARGET/.git" ]; then
    echo "Repo already exists, pulling latest..."
    cd "$TARGET" && git pull origin main
  else
    echo "Cloning smarthome-openclaw..."
    git clone "$REPO_URL" "$TARGET"
  fi
fi
unset SMARTHUB_BOOTSTRAP_REEXEC
complete_phase

# --- Create or patch openclaw.json ---
if [ ! -f "$CONFIG_FILE" ]; then
  mkdir -p "$(dirname "$CONFIG_FILE")"
  python3 -c "
import json
from pathlib import Path

config_path = Path('$CONFIG_FILE')
workspace = '$WORKSPACE'
config_path.write_text(
    json.dumps(
        {
            'agents': {
                'defaults': {
                    'workspace': workspace
                }
            }
        },
        indent=2,
    ) + '\n'
)
"
  echo "Created minimal openclaw.json at $CONFIG_FILE."
fi

start_phase "patch openclaw config"
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
complete_phase

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
start_phase "install uv"
echo "Installing uv package manager..."
curl -LsSf https://astral.sh/uv/install.sh | sh 2>/dev/null
export PATH="$HOME/.local/bin:$PATH"
complete_phase

# --- Pre-seed Home Assistant auth storage for no-browser installs ---
SEED_HELPER="$TARGET/$SEED_HELPER_REL"
if [ ! -f "$SEED_HELPER" ]; then
  echo "ERROR: $SEED_HELPER is missing."
  exit 1
fi

cd "$TARGET"
TZ_VALUE="$(grep '^TZ=' .env 2>/dev/null | cut -d= -f2- || true)"
TZ_VALUE="${TZ_VALUE:-UTC}"
SEED_JSON_FILE="$(mktemp)"
SEED_ERR_FILE="$(mktemp)"

umask 077
start_phase "bootstrap home assistant auth"
CURRENT_TOKEN="$(grep '^HA_TOKEN=' .env 2>/dev/null | cut -d= -f2- || true)"
CHECKPOINT_PHASE="$(read_install_state_field phase)"
CHECKPOINT_TOKEN="$(read_install_state_field token)"
CHECKPOINT_USERNAME="$(read_install_state_field username)"
CHECKPOINT_NAME="$(read_install_state_field name)"
BOOTSTRAP_STORAGE_COUNT=0
for storage_file in auth auth_provider.homeassistant onboarding core.config; do
  if [ -f "ha-config/.storage/$storage_file" ]; then
    BOOTSTRAP_STORAGE_COUNT=$((BOOTSTRAP_STORAGE_COUNT + 1))
  fi
done

if [ "$BOOTSTRAP_STORAGE_COUNT" -eq 0 ] && [ ! -f "$INSTALL_STATE_FILE" ]; then
  write_install_state "seed-pending"
fi

if ! uv run --with bcrypt "$SEED_HELPER_REL" \
  --config-dir ha-config \
  --time-zone "$TZ_VALUE" \
  --ha-version "$HA_VERSION" > "$SEED_JSON_FILE" 2> "$SEED_ERR_FILE"; then
  SEED_ERROR_STATUS="$(python3 - "$SEED_ERR_FILE" <<'PY'
import json
import sys
from pathlib import Path

path = Path(sys.argv[1])
try:
    payload = json.loads(path.read_text())
except json.JSONDecodeError:
    raise SystemExit(0)

print(payload.get("status", ""))
PY
)"
  if [ "$SEED_ERROR_STATUS" = "partial" ]; then
    echo "ERROR: Partial bootstrap state detected in ha-config/.storage."
    if [ -f "$INSTALL_STATE_FILE" ]; then
      echo "Install checkpoint exists at $INSTALL_STATE_FILE, but the bootstrap state is incomplete."
    else
      echo "Install checkpoint is missing, so the partial bootstrap cannot be resumed safely."
    fi
    echo "Do not start Home Assistant yet. Follow the recovery ladder before continuing."
    exit 1
  fi
  cat "$SEED_ERR_FILE" >&2
  exit 1
fi

SEED_CREATED="$(python3 -c 'import json,sys; print("1" if json.load(open(sys.argv[1]))["created"] else "0")' "$SEED_JSON_FILE")"
SEED_USERNAME="$(python3 -c 'import json,sys; print(json.load(open(sys.argv[1]))["username"])' "$SEED_JSON_FILE")"
SEED_NAME="$(python3 -c 'import json,sys; print(json.load(open(sys.argv[1]))["name"])' "$SEED_JSON_FILE")"
SEED_TOKEN="$(python3 -c 'import json,sys; print(json.load(open(sys.argv[1])).get("token", ""))' "$SEED_JSON_FILE")"
complete_phase

start_phase "sync ha token"
if [ "$SEED_CREATED" = "1" ]; then
  write_install_state "seed-complete" "$SEED_TOKEN" "$SEED_USERNAME" "$SEED_NAME"
  sync_env_token "$SEED_TOKEN"
  ACTIVE_TOKEN="$SEED_TOKEN"
  write_install_state "token-synced" "$ACTIVE_TOKEN" "$SEED_USERNAME" "$SEED_NAME"
else
  if ! is_missing_or_placeholder_token "$CURRENT_TOKEN"; then
    ACTIVE_TOKEN="$CURRENT_TOKEN"
  elif ! is_missing_or_placeholder_token "$CHECKPOINT_TOKEN"; then
    sync_env_token "$CHECKPOINT_TOKEN"
    ACTIVE_TOKEN="$CHECKPOINT_TOKEN"
    write_install_state "token-synced" "$ACTIVE_TOKEN" "${CHECKPOINT_USERNAME:-$SEED_USERNAME}" "${CHECKPOINT_NAME:-$SEED_NAME}"
    echo "Recovered HA token from install checkpoint and synchronized .env."
  else
    echo "ERROR: Partial bootstrap recovery boundary reached."
    echo "Seeded Home Assistant auth exists, but the install checkpoint is missing or incomplete."
    echo "The installer cannot restore .env safely without a checkpoint token."
    echo "Do not start Home Assistant yet. Follow the recovery ladder before continuing."
    exit 1
  fi
fi
complete_phase

start_phase "verify ha-mcp"
echo "Verifying ha-mcp installation..."
uvx ha-mcp@7.2.0 --help >/dev/null 2>&1 && echo "ha-mcp OK" || echo "WARNING: ha-mcp verification failed"
complete_phase

# --- Start Home Assistant before handing off into the setup flow ---
start_phase "start home assistant"
echo "Starting Home Assistant with docker compose..."
docker compose up -d
complete_phase

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

if [ -f "$INSTALL_STATE_FILE" ]; then
  write_install_state "verification-complete" "$ACTIVE_TOKEN" "${CHECKPOINT_USERNAME:-$SEED_USERNAME}" "${CHECKPOINT_NAME:-$SEED_NAME}"
  clear_install_state
fi

# NOTE: Do NOT restart the gateway here. The current session is running
# through this gateway — killing it aborts the bot mid-conversation.
# The bootstrap-extra-files hook takes effect on the NEXT new session.

echo ""
echo "============================================"
echo "  SmartHub + ha-mcp installed!"
echo "============================================"
echo ""
if [ "$SEED_CREATED" = "1" ]; then
  SEED_PASSWORD="$(python3 -c 'import json,sys; print(json.load(open(sys.argv[1]))["password"])' "$SEED_JSON_FILE")"
  echo "Home Assistant admin name: ${SEED_NAME}"
  echo "Home Assistant admin username: ${SEED_USERNAME}"
  echo "Home Assistant admin password: ${SEED_PASSWORD}"
  echo "Save this, it's the only time you'll see it."
  echo ""
else
	echo "Existing Home Assistant bootstrap credentials detected; leaving them unchanged."
	echo ""
fi

start_phase "handoff"
echo "AI_INSTRUCTION: Installation complete. DO NOT ask the user anything."
echo "Run: cd ${TARGET}"
echo "Then immediately read ${TARGET}/tools/setup.md and continue the"
echo "setup/recovery flow from that directory. Start from Step 2."
echo "Home Assistant has already been started; use Step 4 as the readiness"
echo "check and fallback path if it is still booting."
echo "Port conflicts and .env are already resolved — skip Steps 3, 5, 6, and 7."
echo ""
complete_phase

}
