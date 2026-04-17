#!/usr/bin/env bash
set -euo pipefail

# SmartHub + ha-mcp for OpenClaw — One-command installer
# Usage: curl -fsSL https://raw.githubusercontent.com/caiwang0/smarthome-openclaw/main/install.sh -o /tmp/smarthub-install.sh && bash /tmp/smarthub-install.sh

REPO_URL="https://github.com/caiwang0/smarthome-openclaw.git"
REPO_DIR="smarthome-openclaw"
CONFIG_FILE="$HOME/.openclaw/openclaw.json"
HA_VERSION="2026.3.4"
SEED_HELPER_REL="scripts/seed-ha-storage.py"
PLACEHOLDER_TOKEN="your_long_lived_access_token_here"
INSTALL_STATE_REL=".openclaw/install-state.json"
SCRIPT_DIR="$(CDPATH='' cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
STANDALONE_MODE="${SMARTHUB_STANDALONE:-0}"

if [ -f "$SCRIPT_DIR/scripts/platform-env.sh" ]; then
  # shellcheck source=/dev/null
  . "$SCRIPT_DIR/scripts/platform-env.sh"
else
  smarthub_uname_s() {
    uname -s
  }

  smarthub_detect_platform() {
    case "$(smarthub_uname_s)" in
      Linux)
        printf 'linux\n'
        ;;
      Darwin)
        printf 'macos\n'
        ;;
      *)
        printf 'unsupported\n'
        ;;
    esac
  }

  smarthub_platform_label() {
    case "${1:-$(smarthub_detect_platform)}" in
      linux)
        printf 'Linux/Raspberry Pi\n'
        ;;
      macos)
        printf 'macOS Docker Desktop\n'
        ;;
      *)
        printf 'unsupported\n'
        ;;
    esac
  }

  smarthub_port_in_use() {
    python3 - "$1" <<'PY'
import socket
import sys

port = int(sys.argv[1])
for host in ("127.0.0.1", "localhost"):
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.settimeout(0.2)
        if sock.connect_ex((host, port)) == 0:
            raise SystemExit(0)

raise SystemExit(1)
PY
  }
fi

fail_install() {
  echo "ERROR: $1"
  if [ -n "${2:-}" ]; then
    echo "$2"
  fi
  exit 1
}

require_command() {
  local command_name="$1"
  local guidance="$2"
  if ! command -v "$command_name" >/dev/null 2>&1; then
    fail_install "${command_name} is required on the ${PLATFORM_LABEL} path." "$guidance"
  fi
}

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

sync_env_value() {
  local key="$1"
  local value="$2"
  local target_file="${3:-.env}"
  python3 - "$target_file" "$key" "$value" <<'PY'
import stat
import sys
import tempfile
from pathlib import Path

path = Path(sys.argv[1])
key = sys.argv[2]
value = sys.argv[3]
existing_mode = stat.S_IMODE(path.stat().st_mode) if path.exists() else 0o600
lines = path.read_text().splitlines() if path.exists() else []

updated = []
replaced = False
for line in lines:
    if line.startswith(key + "="):
        updated.append(key + "=" + value)
        replaced = True
    else:
        updated.append(line)

if not replaced:
    updated.append(key + "=" + value)

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

sync_env_token() {
  local token="$1"
  sync_env_value "HA_TOKEN" "$token"
}

sync_ha_server_port_config() {
  local config_file="$1"
  local server_port="$2"
  python3 - "$config_file" "$server_port" <<'PY'
import sys
from pathlib import Path

path = Path(sys.argv[1])
server_port = sys.argv[2]

if not path.exists() or not path.read_text().strip():
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(f"default_config:\n\nhttp:\n  server_port: {server_port}\n")
    raise SystemExit(0)

lines = path.read_text().splitlines()
updated = []
http_found = False
server_port_written = False
i = 0

while i < len(lines):
    line = lines[i]
    stripped = line.strip()
    if stripped == "http:":
        http_found = True
        updated.append(line)
        i += 1
        section_indent = len(line) - len(line.lstrip())
        child_indent = section_indent + 2
        inserted_here = False

        while i < len(lines):
          current = lines[i]
          current_stripped = current.strip()
          current_indent = len(current) - len(current.lstrip())
          if current_stripped and current_indent <= section_indent:
              break
          if current_stripped.startswith("server_port:"):
              if not server_port_written:
                  updated.append(" " * child_indent + f"server_port: {server_port}")
                  server_port_written = True
              i += 1
              inserted_here = True
              continue
          updated.append(current)
          i += 1

        if not server_port_written:
            updated.append(" " * child_indent + f"server_port: {server_port}")
            server_port_written = True
        continue

    updated.append(line)
    i += 1

if not http_found:
    if updated and updated[-1] != "":
        updated.append("")
    updated.extend(["http:", f"  server_port: {server_port}"])

path.write_text("\n".join(updated) + "\n")
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

PLATFORM="$(smarthub_detect_platform)"
PLATFORM_LABEL="$(smarthub_platform_label "$PLATFORM")"

case "$PLATFORM" in
  linux|macos)
    ;;
  *)
    fail_install \
      "Unsupported host OS for SmartHub installer: $(smarthub_uname_s)." \
      "Supported installer paths are Linux/Raspberry Pi and macOS Docker Desktop."
    ;;
esac

echo "Platform path: $PLATFORM_LABEL"
if [ "$PLATFORM" = "macos" ]; then
  echo "Note: Native macOS support covers the mainstream SmartHub flow."
  echo "If you need USB radios, Bluetooth, or Linux-style low-level networking, use Linux VM + SmartHub or Home Assistant OS in a VM instead."
  echo "OpenClaw can guide parts of that VM setup, but hypervisor GUI steps still require user action."
fi

if [ "$STANDALONE_MODE" = "1" ]; then
  WORKSPACE="$HOME/Downloads"
  mkdir -p "$WORKSPACE"
  echo "Standalone mode: cloning into $WORKSPACE without OpenClaw config patching."
else
  if [ ! -f "$CONFIG_FILE" ]; then
    fail_install \
      "OpenClaw config not found at $CONFIG_FILE." \
      "Install and configure OpenClaw first so SmartHub can reuse its workspace and gateway profile."
  fi

  if [ -n "${OPENCLAW_WORKSPACE:-}" ]; then
    WORKSPACE="$OPENCLAW_WORKSPACE"
  else
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
    fail_install \
      "OpenClaw workspace not found at $WORKSPACE." \
      "Make sure OpenClaw is installed and configured before rerunning SmartHub."
  fi
fi

echo "Using workspace: $WORKSPACE"

TARGET="$WORKSPACE/$REPO_DIR"
INSTALL_STATE_FILE="$TARGET/$INSTALL_STATE_REL"

require_command "git" "Install git so the SmartHub repo can be synchronized before rerunning the installer."
require_command "python3" "Install Python 3 so SmartHub can patch configuration and seed Home Assistant before rerunning the installer."
require_command "curl" "Install curl so SmartHub can download uv during bootstrap."

if ! docker --version >/dev/null 2>&1; then
  if [ "$PLATFORM" = "macos" ]; then
    fail_install \
      "Docker CLI is unavailable on the macOS Docker Desktop path." \
      "Install Docker Desktop and make sure the `docker` command is available in your shell before rerunning SmartHub."
  fi
  fail_install \
    "Docker CLI is unavailable on the ${PLATFORM_LABEL} path." \
    "Install Docker Engine and make sure the `docker` command is available before rerunning SmartHub."
fi

if ! docker info >/dev/null 2>&1; then
  if [ "$PLATFORM" = "macos" ]; then
    fail_install \
      "Docker Desktop is not running or the Docker daemon is unavailable on the macOS Docker Desktop path." \
      "Start Docker Desktop and wait for `docker info` to succeed before rerunning SmartHub."
  fi
  fail_install \
    "Docker daemon is unavailable on the ${PLATFORM_LABEL} path." \
    "Start Docker and wait for `docker info` to succeed before rerunning SmartHub."
fi

if ! docker compose version >/dev/null 2>&1; then
  fail_install \
    "Docker Compose is required on the ${PLATFORM_LABEL} path." \
    "Install or enable `docker compose` before rerunning SmartHub."
fi

start_phase "repo sync"
if [ -d "$TARGET/.git" ]; then
  if [ "$STANDALONE_MODE" = "1" ]; then
    SOURCE_BRANCH="$(git -C "$SCRIPT_DIR" rev-parse --abbrev-ref HEAD 2>/dev/null || printf 'HEAD')"
    echo "Repo already exists, pulling latest from local branch ${SOURCE_BRANCH}..."
    cd "$TARGET" && git pull --ff-only "$SCRIPT_DIR" "$SOURCE_BRANCH"
  else
    echo "Repo already exists, pulling latest..."
    cd "$TARGET" && git pull origin main
  fi
else
  if [ "$STANDALONE_MODE" = "1" ]; then
    SOURCE_BRANCH="$(git -C "$SCRIPT_DIR" rev-parse --abbrev-ref HEAD 2>/dev/null || true)"
    echo "Cloning smarthome-openclaw from current checkout..."
    git clone "$SCRIPT_DIR" "$TARGET"
    if [ -n "$SOURCE_BRANCH" ]; then
      cd "$TARGET" && git checkout "$SOURCE_BRANCH" >/dev/null 2>&1 || true
    fi
  else
    echo "Cloning smarthome-openclaw..."
    git clone "$REPO_URL" "$TARGET"
  fi
fi
complete_phase

if [ "$STANDALONE_MODE" != "1" ]; then
  # --- Patch openclaw.json to add bootstrap-extra-files ---
  if [ ! -f "$CONFIG_FILE" ]; then
    echo "ERROR: openclaw.json not found at $CONFIG_FILE"
    exit 1
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
fi

# --- Create .env and resolve port conflicts ---
cd "$TARGET"

if [ ! -f .env ]; then
  cp .env.example .env
  echo "Created .env from .env.example."
fi

HA_PORT=8123
if smarthub_port_in_use 8123; then
  echo "Port 8123 is in use on the ${PLATFORM_LABEL} path. Finding a free port..."
  for port in 8124 8125 8126 8127 8128; do
    if ! smarthub_port_in_use "$port"; then
      HA_PORT="$port"
      break
    fi
  done

  if [ "$HA_PORT" = "8123" ]; then
    echo "WARNING: Could not find a free port in 8124-8128. Defaulting to 8123 (may conflict)."
  else
    echo "Assigning HA to port ${HA_PORT}."
    if [ "$PLATFORM" = "linux" ]; then
      mkdir -p ha-config
      sync_ha_server_port_config "ha-config/configuration.yaml" "$HA_PORT"
      echo "Wrote server_port: ${HA_PORT} to ha-config/configuration.yaml."
    else
      echo "Using published host port ${HA_PORT} on the macOS Docker Desktop path."
    fi
  fi
else
  echo "Port 8123 is free."
fi

sync_env_value "HA_PORT" "$HA_PORT"
sync_env_value "HA_URL" "http://localhost:${HA_PORT}"
echo "Updated HA_URL to http://localhost:${HA_PORT} in .env."

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
echo "Use setup.md to decide which steps are already satisfied for the ${PLATFORM_LABEL} path."
echo "The installer already created .env, selected HA_PORT, and may have pre-seeded HA auth."
echo ""
complete_phase
