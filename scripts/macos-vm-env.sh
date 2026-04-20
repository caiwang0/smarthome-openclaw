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

smarthub_vm_virtualbox_platform_arch() {
  case "$(smarthub_vm_arch)" in
    amd64)
      printf '%s\n' "x86"
      ;;
    arm64)
      printf '%s\n' "arm"
      ;;
  esac
}

smarthub_vm_virtualbox_ostype() {
  case "$(smarthub_vm_arch)" in
    amd64)
      printf '%s\n' "Oracle_64"
      ;;
    arm64)
      printf '%s\n' "Oracle_arm64"
      ;;
  esac
}

smarthub_vm_virtualbox_graphics_controller() {
  case "$(smarthub_vm_arch)" in
    amd64)
      printf '%s\n' "vmsvga"
      ;;
    arm64)
      printf '%s\n' "qemuramfb"
      ;;
  esac
}

smarthub_vm_haos_asset_basename() {
  case "$(smarthub_vm_arch)" in
    amd64)
      printf '%s\n' "haos_ova"
      ;;
    arm64)
      printf '%s\n' "haos_generic-aarch64"
      ;;
  esac
}

smarthub_vm_disk_extension() {
  case "$(smarthub_vm_arch)" in
    amd64)
      printf '%s\n' "vdi"
      ;;
    arm64)
      printf '%s\n' "vmdk"
      ;;
  esac
}

smarthub_vm_state_dir() {
  printf '%s\n' "${SMARTHUB_VM_STATE_DIR:-$HOME/.smarthub-vm}"
}

smarthub_vm_state_file() {
  printf '%s\n' "$(smarthub_vm_state_dir)/bootstrap-state.json"
}

smarthub_vm_cache_dir() {
  printf '%s\n' "$(smarthub_vm_state_dir)/cache"
}

smarthub_vm_bootstrap_result_file() {
  printf '%s\n' "$(smarthub_vm_state_dir)/ha-bootstrap.json"
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
    local adapter resolved_adapter
    adapter="$(route get default 2>/dev/null | awk '/interface:/{print $2; exit}')"
    if [ -n "$adapter" ]; then
      if command -v VBoxManage >/dev/null 2>&1; then
        resolved_adapter="$(
          VBoxManage list bridgedifs 2>/dev/null | awk -v iface="$adapter" '
            $1 == "Name:" {
              name = substr($0, index($0, $2))
              if (name == iface || index(name, iface ":") == 1) {
                print name
                exit
              }
            }
          '
        )"
        if [ -n "$resolved_adapter" ]; then
          printf '%s\n' "$resolved_adapter"
          return
        fi
      fi
      printf '%s\n' "$adapter"
      return
    fi
  fi

  fail_install \
    "Unable to determine the macOS network adapter for bridged mode." \
    "Set SMARTHUB_VM_BRIDGE_ADAPTER to the interface name you use for internet access, then rerun SmartHub."
}

smarthub_vm_ram_mb() {
  printf '%s\n' "${SMARTHUB_VM_RAM_MB:-2048}"
}

smarthub_vm_cpus() {
  printf '%s\n' "${SMARTHUB_VM_CPUS:-2}"
}

smarthub_vm_ha_base_url() {
  printf '%s\n' "${SMARTHUB_VM_HA_BASE_URL:-http://homeassistant.local:8123}"
}

smarthub_vm_ha_admin_name() {
  printf '%s\n' "${SMARTHUB_VM_HA_ADMIN_NAME:-OpenClaw}"
}

smarthub_vm_ha_admin_username() {
  printf '%s\n' "${SMARTHUB_VM_HA_ADMIN_USERNAME:-openclaw}"
}

smarthub_vm_ha_bootstrap_timeout_seconds() {
  printf '%s\n' "${SMARTHUB_VM_HA_BOOTSTRAP_TIMEOUT_SECONDS:-900}"
}

smarthub_vm_ha_bootstrap_poll_interval_seconds() {
  printf '%s\n' "${SMARTHUB_VM_HA_BOOTSTRAP_POLL_INTERVAL_SECONDS:-5}"
}

smarthub_vm_env_file() {
  printf '%s\n' "${SMARTHUB_VM_ENV_FILE:-$SCRIPT_DIR/.env}"
}

smarthub_vm_env_example_file() {
  printf '%s\n' "${SMARTHUB_VM_ENV_EXAMPLE_FILE:-$SCRIPT_DIR/.env.example}"
}

smarthub_vm_dry_run_enabled() {
  [ "${SMARTHUB_VM_DRY_RUN:-0}" = "1" ]
}
