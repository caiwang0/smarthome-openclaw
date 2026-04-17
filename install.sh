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

smarthub_uname_s() {
  if [ -n "${SMARTHUB_TEST_UNAME:-}" ]; then
    printf '%s\n' "$SMARTHUB_TEST_UNAME"
    return
  fi

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

fail_install() {
  echo "ERROR: $1" >&2
  if [ -n "${2:-}" ]; then
    echo "$2" >&2
  fi
  exit 1
}

run_macos_host_bootstrap() {
  fail_install \
    "macOS VM bootstrap helper missing." \
    "Restore scripts/macos-vm-bootstrap.sh before rerunning SmartHub."
}

LINUX_GUEST_HELPER="$SCRIPT_DIR/scripts/linux-guest-install.sh"
if [ ! -f "$LINUX_GUEST_HELPER" ]; then
  fail_install \
    "Linux guest installer helper missing at $LINUX_GUEST_HELPER." \
    "Re-clone the repo or restore scripts/linux-guest-install.sh before rerunning SmartHub."
fi

# shellcheck source=/dev/null
. "$LINUX_GUEST_HELPER"

MACOS_BOOTSTRAP_HELPER="$SCRIPT_DIR/scripts/macos-vm-bootstrap.sh"
if [ ! -f "$MACOS_BOOTSTRAP_HELPER" ]; then
  fail_install \
    "macOS VM bootstrap helper missing at $MACOS_BOOTSTRAP_HELPER." \
    "Re-clone the repo or restore scripts/macos-vm-bootstrap.sh before rerunning SmartHub."
fi

# shellcheck source=/dev/null
. "$MACOS_BOOTSTRAP_HELPER"

main() {
  if [ "${SMARTHUB_GUEST_INSTALL:-0}" = "1" ]; then
    run_linux_guest_install
    return
  fi

  case "$(smarthub_detect_platform)" in
    linux)
      run_linux_guest_install
      ;;
    macos)
      run_macos_host_bootstrap
      ;;
    *)
      fail_install \
        "Unsupported host OS for SmartHub installer: $(smarthub_uname_s)." \
        "Supported SmartHub host paths are Linux and macOS host bootstrap into Linux VM + SmartHub."
      ;;
  esac
}

main "$@"
