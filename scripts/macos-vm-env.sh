smarthub_vm_host_arch_raw() {
  if [ -n "${SMARTHUB_TEST_ARCH:-}" ]; then
    printf '%s\n' "$SMARTHUB_TEST_ARCH"
    return
  fi

  uname -m
}

smarthub_vm_arch() {
  case "$(smarthub_vm_host_arch_raw)" in
    x86_64|amd64)
      printf 'amd64\n'
      ;;
    arm64|aarch64)
      printf 'arm64\n'
      ;;
    *)
      fail_install \
        "Unsupported Mac architecture: $(smarthub_vm_host_arch_raw)." \
        "SmartHub currently supports macOS hosts on amd64 and arm64 only."
      ;;
  esac
}

smarthub_vm_name() {
  printf '%s\n' "${SMARTHUB_VM_NAME:-smarthub-vm}"
}

smarthub_vm_hostname() {
  printf '%s\n' "${SMARTHUB_VM_HOSTNAME:-smarthub-vm}"
}

smarthub_vm_state_dir() {
  printf '%s\n' "${SMARTHUB_VM_STATE_DIR:-$HOME/.smarthub-vm}"
}

smarthub_vm_state_file() {
  printf '%s/bootstrap-state.json\n' "$(smarthub_vm_state_dir)"
}

smarthub_vm_cache_dir() {
  printf '%s/cache\n' "$(smarthub_vm_state_dir)"
}

smarthub_vm_iso_filename() {
  case "$(smarthub_vm_arch)" in
    amd64)
      printf '%s\n' "${SMARTHUB_VM_ISO_FILENAME:-ubuntu-24.04.2-live-server-amd64.iso}"
      ;;
    arm64)
      printf '%s\n' "${SMARTHUB_VM_ISO_FILENAME:-ubuntu-24.04.2-live-server-arm64.iso}"
      ;;
  esac
}

smarthub_vm_iso_url() {
  if [ -n "${SMARTHUB_VM_ISO_URL:-}" ]; then
    printf '%s\n' "$SMARTHUB_VM_ISO_URL"
    return
  fi

  printf 'https://releases.ubuntu.com/noble/%s\n' "$(smarthub_vm_iso_filename)"
}

smarthub_vm_iso_path() {
  printf '%s/%s\n' "$(smarthub_vm_cache_dir)" "$(smarthub_vm_iso_filename)"
}

smarthub_vm_disk_path() {
  printf '%s/%s.vdi\n' "$(smarthub_vm_state_dir)" "$(smarthub_vm_name)"
}

smarthub_vm_ram_mb() {
  printf '%s\n' "${SMARTHUB_VM_RAM_MB:-2048}"
}

smarthub_vm_cpus() {
  printf '%s\n' "${SMARTHUB_VM_CPUS:-2}"
}

smarthub_vm_disk_mb() {
  printf '%s\n' "${SMARTHUB_VM_DISK_MB:-32768}"
}

smarthub_vm_ssh_port() {
  printf '%s\n' "${SMARTHUB_VM_SSH_PORT:-2222}"
}

smarthub_vm_bootstrap_user() {
  printf '%s\n' "${SMARTHUB_VM_BOOTSTRAP_USER:-smarthub}"
}

smarthub_vm_bootstrap_password_file() {
  printf '%s/bootstrap-password.txt\n' "$(smarthub_vm_state_dir)"
}

smarthub_vm_askpass_script() {
  printf '%s/ssh-askpass.sh\n' "$(smarthub_vm_state_dir)"
}

smarthub_vm_bridged_adapter() {
  if [ -n "${SMARTHUB_VM_BRIDGE_ADAPTER:-}" ]; then
    printf '%s\n' "$SMARTHUB_VM_BRIDGE_ADAPTER"
    return
  fi

  if smarthub_vm_dry_run_enabled; then
    printf '%s\n' "en0"
    return
  fi

  if command -v route >/dev/null 2>&1; then
    local adapter
    adapter="$(route get default 2>/dev/null | awk '/interface:/{print $2; exit}')"
    if [ -n "$adapter" ]; then
      printf '%s\n' "$adapter"
      return
    fi
  fi

  fail_install \
    "Unable to determine the macOS network adapter for bridged mode." \
    "Set SMARTHUB_VM_BRIDGE_ADAPTER to the interface name you use for internet access, then rerun SmartHub."
}

smarthub_vm_nat_nic() {
  printf '%s\n' "nat"
}

smarthub_vm_ssh_max_attempts() {
  printf '%s\n' "${SMARTHUB_VM_SSH_MAX_ATTEMPTS:-60}"
}

smarthub_vm_ssh_retry_delay() {
  printf '%s\n' "${SMARTHUB_VM_SSH_RETRY_DELAY:-5}"
}

smarthub_vm_guest_repo_dir() {
  printf '%s\n' "${SMARTHUB_VM_GUEST_REPO_DIR:-/home/$(smarthub_vm_bootstrap_user)/$REPO_DIR}"
}

smarthub_vm_dry_run_enabled() {
  [ "${SMARTHUB_VM_DRY_RUN:-0}" = "1" ]
}
