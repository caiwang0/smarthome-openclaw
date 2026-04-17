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
  echo "ERROR: $1"
  if [ -n "${2:-}" ]; then
    echo "$2"
  fi
  exit 1
}

run_macos_host_bootstrap() {
  if ! command -v VBoxManage >/dev/null 2>&1; then
    if command -v brew >/dev/null 2>&1; then
      fail_install \
        "VirtualBox is required for the macOS SmartHub path." \
        "Run brew install --cask virtualbox, approve any macOS prompts, and rerun SmartHub."
    fi

    fail_install \
      "VirtualBox is required for the macOS SmartHub path." \
      "Install VirtualBox first, or install Homebrew so SmartHub can install VirtualBox for you on the next run."
  fi

  fail_install \
    "VirtualBox is installed, but the macOS VM bootstrap helper is not wired in yet." \
    "Phase 2 will attach the macOS host bootstrap here."
}

LINUX_GUEST_HELPER="$SCRIPT_DIR/scripts/linux-guest-install.sh"
if [ ! -f "$LINUX_GUEST_HELPER" ]; then
  fail_install \
    "Linux guest installer helper missing at $LINUX_GUEST_HELPER." \
    "Re-clone the repo or restore scripts/linux-guest-install.sh before rerunning SmartHub."
fi

# shellcheck source=/dev/null
. "$LINUX_GUEST_HELPER"

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
