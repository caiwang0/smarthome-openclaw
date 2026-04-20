MACOS_VM_SCRIPT_DIR="$(CDPATH='' cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"

# shellcheck source=/dev/null
. "$MACOS_VM_SCRIPT_DIR/macos-vm-env.sh"

smarthub_vm_ensure_state_dir() {
  mkdir -p "$(smarthub_vm_state_dir)" "$(smarthub_vm_cache_dir)"
}

smarthub_vm_read_stage() {
  python3 - "$(smarthub_vm_state_file)" <<'PY'
import json
import sys
from pathlib import Path

path = Path(sys.argv[1])
if not path.is_file():
    raise SystemExit(0)

try:
    payload = json.loads(path.read_text())
except json.JSONDecodeError:
    raise SystemExit(0)

print(payload.get("stage", ""))
PY
}

smarthub_vm_write_state() {
  local stage="$1"
  local vm_name="$2"
  smarthub_vm_ensure_state_dir
  SMARTHUB_VM_STAGE="$stage" \
  SMARTHUB_VM_NAME_VALUE="$vm_name" \
  python3 - "$(smarthub_vm_state_file)" <<'PY'
import json
import os
import sys
import tempfile
from pathlib import Path

path = Path(sys.argv[1])
payload = {
    "stage": os.environ["SMARTHUB_VM_STAGE"],
    "vm_name": os.environ["SMARTHUB_VM_NAME_VALUE"],
}

existing = {}
if path.is_file():
    try:
        existing = json.loads(path.read_text())
    except json.JSONDecodeError:
        existing = {}

existing.update(payload)
with tempfile.NamedTemporaryFile(
    mode="w",
    encoding="utf-8",
    dir=path.parent,
    prefix=f".{path.name}.",
    delete=False,
) as tmp:
    json.dump(existing, tmp, indent=2, sort_keys=True)
    tmp.write("\n")
    temp_path = Path(tmp.name)

temp_path.chmod(0o600)
temp_path.replace(path)
PY
}

smarthub_vm_stage_rank() {
  case "$1" in
    "")
      printf '0\n'
      ;;
    vm-created)
      printf '1\n'
      ;;
    vm-started)
      printf '2\n'
      ;;
    ha-bootstrapped)
      printf '3\n'
      ;;
    *)
      printf '0\n'
      ;;
  esac
}

smarthub_vm_stage_reached() {
  [ "$(smarthub_vm_stage_rank "$1")" -ge "$(smarthub_vm_stage_rank "$2")" ]
}

smarthub_vm_require_virtualbox() {
  if command -v VBoxManage >/dev/null 2>&1; then
    return
  fi

  if command -v brew >/dev/null 2>&1; then
    echo "Installing VirtualBox with Homebrew..."
    brew install --cask virtualbox
  else
    fail_install \
      "VirtualBox is required for the macOS SmartHub path." \
      "Install VirtualBox first, or install Homebrew so SmartHub can install VirtualBox for you on the next run."
  fi

  if ! command -v VBoxManage >/dev/null 2>&1; then
    fail_install \
      "VirtualBox installation did not finish cleanly." \
      "Approve any macOS permission prompts for VirtualBox, then rerun SmartHub."
  fi
}

smarthub_vm_haos_release_metadata_file() {
  printf '%s\n' "$(smarthub_vm_cache_dir)/haos-release.json"
}

smarthub_vm_fetch_haos_release_metadata() {
  local metadata_file
  metadata_file="$(smarthub_vm_haos_release_metadata_file)"
  if [ -f "$metadata_file" ]; then
    printf '%s\n' "$metadata_file"
    return
  fi

  if ! command -v curl >/dev/null 2>&1; then
    fail_install \
      "curl is required to download the Home Assistant OS release metadata." \
      "Install curl on the macOS host, then rerun SmartHub."
  fi

  smarthub_vm_ensure_state_dir
  curl -fsSL "https://api.github.com/repos/home-assistant/operating-system/releases/latest" -o "$metadata_file"
  printf '%s\n' "$metadata_file"
}

smarthub_vm_resolve_haos_asset_name() {
  local asset_name
  if [ -n "${SMARTHUB_VM_HAOS_ASSET_NAME:-}" ]; then
    printf '%s\n' "$SMARTHUB_VM_HAOS_ASSET_NAME"
    return
  fi

  if smarthub_vm_dry_run_enabled; then
    printf '%s.%s.zip\n' "$(smarthub_vm_haos_asset_basename)" "$(smarthub_vm_disk_extension)"
    return
  fi

  asset_name="$(
    python3 - "$(smarthub_vm_fetch_haos_release_metadata)" "$(smarthub_vm_arch)" <<'PY'
import json
import sys

metadata_path = sys.argv[1]
arch = sys.argv[2]
with open(metadata_path, "r", encoding="utf-8") as handle:
    payload = json.load(handle)

if arch == "amd64":
    prefix = "haos_ova-"
    suffix = ".vdi.zip"
else:
    prefix = "haos_generic-aarch64-"
    suffix = ".vmdk.zip"

for asset in payload.get("assets", []):
    name = asset.get("name", "")
    if name.startswith(prefix) and name.endswith(suffix):
        print(name)
        raise SystemExit(0)

raise SystemExit(1)
PY
  )" || true

  if [ -n "$asset_name" ]; then
    printf '%s\n' "$asset_name"
    return
  fi

  fail_install \
    "Unable to find the matching Home Assistant OS disk image for macOS host architecture $(smarthub_vm_arch)." \
    "Set SMARTHUB_VM_HAOS_ASSET_NAME to a valid Home Assistant OS VirtualBox archive name and rerun SmartHub."
}

smarthub_vm_resolve_haos_asset_url() {
  local asset_url
  if [ -n "${SMARTHUB_VM_HAOS_ASSET_URL:-}" ]; then
    printf '%s\n' "$SMARTHUB_VM_HAOS_ASSET_URL"
    return
  fi

  asset_url="$(
    python3 - "$(smarthub_vm_fetch_haos_release_metadata)" "$(smarthub_vm_resolve_haos_asset_name)" <<'PY'
import json
import sys

metadata_path = sys.argv[1]
asset_name = sys.argv[2]
with open(metadata_path, "r", encoding="utf-8") as handle:
    payload = json.load(handle)

for asset in payload.get("assets", []):
    if asset.get("name") == asset_name:
        print(asset["browser_download_url"])
        raise SystemExit(0)

raise SystemExit(1)
PY
  )" || true

  if [ -n "$asset_url" ]; then
    printf '%s\n' "$asset_url"
    return
  fi

  fail_install \
    "Unable to resolve the download URL for $(smarthub_vm_resolve_haos_asset_name)." \
    "Set SMARTHUB_VM_HAOS_ASSET_URL to the correct Home Assistant OS download URL and rerun SmartHub."
}

smarthub_vm_disk_archive_path() {
  printf '%s/%s\n' "$(smarthub_vm_cache_dir)" "$(smarthub_vm_resolve_haos_asset_name)"
}

smarthub_vm_disk_path() {
  local archive_name
  archive_name="$(smarthub_vm_resolve_haos_asset_name)"
  printf '%s/%s\n' "$(smarthub_vm_cache_dir)" "${archive_name%.zip}"
}

smarthub_vm_prepare_disk_image() {
  local archive_path archive_url disk_path
  archive_path="$(smarthub_vm_disk_archive_path)"
  disk_path="$(smarthub_vm_disk_path)"
  if [ -f "$disk_path" ]; then
    return
  fi

  smarthub_vm_ensure_state_dir
  if smarthub_vm_dry_run_enabled; then
    : > "$disk_path"
    return
  fi

  if ! command -v curl >/dev/null 2>&1; then
    fail_install \
      "curl is required to download the Home Assistant OS disk image." \
      "Install curl on the macOS host, then rerun SmartHub."
  fi

  if [ ! -f "$archive_path" ]; then
    archive_url="$(smarthub_vm_resolve_haos_asset_url)"
    echo "Downloading Home Assistant OS disk image from $archive_url..."
    curl -fsSL "$archive_url" -o "$archive_path"
  fi

  echo "Extracting Home Assistant OS disk image..."
  rm -f "$disk_path"
  ditto -x -k "$archive_path" "$(smarthub_vm_cache_dir)"

  if [ ! -f "$disk_path" ]; then
    fail_install \
      "Home Assistant OS disk image extraction failed." \
      "Expected $disk_path after extracting $archive_path."
  fi
}

smarthub_vm_read_bootstrap_result_field() {
  local field="$1"
  python3 - "$(smarthub_vm_bootstrap_result_file)" "$field" <<'PY'
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

smarthub_vm_sync_env() {
  local ha_url="$1"
  local token="$2"
  local env_file env_example
  env_file="$(smarthub_vm_env_file)"
  env_example="$(smarthub_vm_env_example_file)"
  if [ ! -f "$env_file" ]; then
    if [ ! -f "$env_example" ]; then
      fail_install \
        "Missing .env.example for macOS Home Assistant bootstrap." \
        "Restore $env_example before rerunning SmartHub."
    fi
    cp "$env_example" "$env_file"
  fi

  python3 - "$env_file" "$ha_url" "$token" <<'PY'
import stat
import sys
import tempfile
from pathlib import Path

path = Path(sys.argv[1])
ha_url = sys.argv[2]
token = sys.argv[3]
existing_mode = stat.S_IMODE(path.stat().st_mode) if path.exists() else 0o600
lines = path.read_text().splitlines() if path.exists() else []

updated = []
seen_url = False
seen_token = False
for line in lines:
    if line.startswith("HA_URL="):
        updated.append("HA_URL=" + ha_url)
        seen_url = True
    elif line.startswith("HA_TOKEN="):
        updated.append("HA_TOKEN=" + token)
        seen_token = True
    else:
        updated.append(line)

if not seen_url:
    updated.append("HA_URL=" + ha_url)
if not seen_token:
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

smarthub_vm_configure_virtualbox_vm() {
  local vm_name bridge_adapter disk_path current_stage existing_machine_info existing_platform_arch attached_disk_path
  vm_name="$(smarthub_vm_name)"
  bridge_adapter="$(smarthub_vm_bridged_adapter)"
  disk_path="$(smarthub_vm_disk_path)"
  current_stage="$(smarthub_vm_read_stage)"

  if smarthub_vm_stage_reached "$current_stage" "vm-created"; then
    existing_machine_info="$(VBoxManage showvminfo "$vm_name" --machinereadable 2>/dev/null || true)"
    existing_platform_arch="$(
      printf '%s\n' "$existing_machine_info" | awk -F= '/^platformArchitecture=/{gsub(/"/, "", $2); print $2; exit}'
    )"
    attached_disk_path="$(
      printf '%s\n' "$existing_machine_info" | awk -F= '/^"SATA-0-0"=/{gsub(/"/, "", $2); print $2; exit}'
    )"
    if [ -n "$existing_platform_arch" ] && [ "$existing_platform_arch" != "$(smarthub_vm_virtualbox_platform_arch)" ]; then
      VBoxManage unregistervm "$vm_name" --delete
      current_stage=""
    elif [ -n "$attached_disk_path" ] && [ "$attached_disk_path" != "$disk_path" ]; then
      VBoxManage unregistervm "$vm_name" --delete
      current_stage=""
    fi
  fi

  if smarthub_vm_stage_reached "$current_stage" "vm-created"; then
    VBoxManage modifyvm "$vm_name" --ostype "$(smarthub_vm_virtualbox_ostype)"
    VBoxManage modifyvm "$vm_name" --firmware efi --memory "$(smarthub_vm_ram_mb)" --cpus "$(smarthub_vm_cpus)"
    VBoxManage modifyvm "$vm_name" --graphicscontroller "$(smarthub_vm_virtualbox_graphics_controller)"
    VBoxManage modifyvm "$vm_name" --nic1 bridged --bridgeadapter1 "$bridge_adapter"
    return
  fi

  VBoxManage createvm --name "$vm_name" --platform-architecture "$(smarthub_vm_virtualbox_platform_arch)" --ostype "$(smarthub_vm_virtualbox_ostype)" --register
  VBoxManage modifyvm "$vm_name" --firmware efi --memory "$(smarthub_vm_ram_mb)" --cpus "$(smarthub_vm_cpus)"
  VBoxManage modifyvm "$vm_name" --graphicscontroller "$(smarthub_vm_virtualbox_graphics_controller)"
  VBoxManage modifyvm "$vm_name" --nic1 bridged --bridgeadapter1 "$bridge_adapter"
  VBoxManage storagectl "$vm_name" --name "SATA" --add sata --controller IntelAhci
  VBoxManage storageattach "$vm_name" --storagectl "SATA" --port 0 --device 0 --type hdd --medium "$disk_path"
  smarthub_vm_write_state "vm-created" "$vm_name"
}

smarthub_vm_start_vm() {
  local vm_name current_stage current_vm_state
  vm_name="$(smarthub_vm_name)"
  current_stage="$(smarthub_vm_read_stage)"
  if smarthub_vm_stage_reached "$current_stage" "vm-started"; then
    return
  fi

  current_vm_state="$(
    VBoxManage showvminfo "$vm_name" --machinereadable 2>/dev/null | awk -F= '/^VMState=/{gsub(/"/, "", $2); print $2; exit}'
  )"
  if [ "$current_vm_state" != "running" ]; then
    VBoxManage startvm "$vm_name" --type headless
  fi
  smarthub_vm_write_state "vm-started" "$vm_name"
}

smarthub_vm_bootstrap_home_assistant() {
  local current_stage helper result_file result_tmp ha_url token created name username password
  current_stage="$(smarthub_vm_read_stage)"
  result_file="$(smarthub_vm_bootstrap_result_file)"

  if smarthub_vm_stage_reached "$current_stage" "ha-bootstrapped"; then
    if [ ! -f "$result_file" ]; then
      fail_install \
        "Home Assistant bootstrap state is missing from $(smarthub_vm_bootstrap_result_file)." \
        "Delete ~/.smarthub-vm and rerun SmartHub for a clean macOS bootstrap."
    fi
    ha_url="$(smarthub_vm_read_bootstrap_result_field base_url)"
    token="$(smarthub_vm_read_bootstrap_result_field token)"
    if [ -n "$ha_url" ] && [ -n "$token" ]; then
      smarthub_vm_sync_env "$ha_url" "$token"
    fi
    echo "Existing Home Assistant bootstrap credentials detected; leaving them unchanged."
    return
  fi

  helper="$MACOS_VM_SCRIPT_DIR/bootstrap-ha-onboarding.py"
  if [ ! -f "$helper" ]; then
    fail_install \
      "Home Assistant onboarding bootstrap helper missing at $helper." \
      "Restore scripts/bootstrap-ha-onboarding.py before rerunning SmartHub."
  fi

  smarthub_vm_ensure_state_dir
  result_tmp="$(mktemp)"
  if ! python3 "$helper" \
    --base-url "$(smarthub_vm_ha_base_url)" \
    --name "$(smarthub_vm_ha_admin_name)" \
    --username "$(smarthub_vm_ha_admin_username)" \
    --wait-timeout "$(smarthub_vm_ha_bootstrap_timeout_seconds)" \
    --wait-interval "$(smarthub_vm_ha_bootstrap_poll_interval_seconds)" \
    $(smarthub_vm_dry_run_enabled && printf '%s' '--dry-run') \
    > "$result_tmp"; then
    rm -f "$result_tmp"
    fail_install \
      "Automatic Home Assistant onboarding bootstrap failed on macOS." \
      "Delete the VM and rerun SmartHub for a clean bootstrap, or finish onboarding manually and create a long-lived token in the Home Assistant UI."
  fi

  chmod 600 "$result_tmp"
  mv "$result_tmp" "$result_file"

  ha_url="$(smarthub_vm_read_bootstrap_result_field base_url)"
  token="$(smarthub_vm_read_bootstrap_result_field token)"
  created="$(smarthub_vm_read_bootstrap_result_field created)"
  name="$(smarthub_vm_read_bootstrap_result_field name)"
  username="$(smarthub_vm_read_bootstrap_result_field username)"
  password="$(smarthub_vm_read_bootstrap_result_field password)"

  if [ -z "$ha_url" ] || [ -z "$token" ]; then
    fail_install \
      "Home Assistant onboarding bootstrap did not return a usable token." \
      "Delete the VM and rerun SmartHub for a clean bootstrap, or create a long-lived token manually in the Home Assistant UI."
  fi

  smarthub_vm_sync_env "$ha_url" "$token"
  smarthub_vm_write_state "ha-bootstrapped" "$(smarthub_vm_name)"

  if [ "$created" = "True" ] || [ "$created" = "true" ] || [ "$created" = "1" ]; then
    echo "Home Assistant admin name: ${name}"
    echo "Home Assistant admin username: ${username}"
    echo "Home Assistant admin password: ${password}"
    echo "Save this, it's the only time you'll see it."
  else
    echo "Existing Home Assistant bootstrap credentials detected; leaving them unchanged."
  fi
}

smarthub_vm_print_access_instructions() {
  local base_url resolved_ip
  base_url="$(smarthub_vm_read_bootstrap_result_field base_url)"
  resolved_ip="$(smarthub_vm_read_bootstrap_result_field resolved_ip)"
  echo "Home Assistant OS VM started."
  if [ -n "$base_url" ]; then
    echo "Open ${base_url} in your browser."
  else
    echo "Open http://homeassistant.local:8123 in your browser."
  fi
  if [ -n "$resolved_ip" ]; then
    echo "Home Assistant VM IP: ${resolved_ip}"
  else
    echo "If that hostname does not resolve on your network, use the VM IP from your router or DHCP lease table."
  fi
}

run_macos_host_bootstrap() {
  smarthub_vm_arch >/dev/null
  smarthub_vm_require_virtualbox
  smarthub_vm_prepare_disk_image
  smarthub_vm_configure_virtualbox_vm
  smarthub_vm_start_vm
  smarthub_vm_bootstrap_home_assistant
  smarthub_vm_print_access_instructions
}
