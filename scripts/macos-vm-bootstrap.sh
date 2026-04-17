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
  local ssh_port="$3"
  local username="$4"
  smarthub_vm_ensure_state_dir
  SMARTHUB_VM_STAGE="$stage" \
  SMARTHUB_VM_NAME_VALUE="$vm_name" \
  SMARTHUB_VM_SSH_PORT_VALUE="$ssh_port" \
  SMARTHUB_VM_BOOTSTRAP_USER_VALUE="$username" \
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
    "ssh_port": int(os.environ["SMARTHUB_VM_SSH_PORT_VALUE"]),
    "bootstrap_user": os.environ["SMARTHUB_VM_BOOTSTRAP_USER_VALUE"],
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
    install-started)
      printf '2\n'
      ;;
    ssh-ready)
      printf '3\n'
      ;;
    guest-install-triggered)
      printf '4\n'
      ;;
    *)
      printf '0\n'
      ;;
  esac
}

smarthub_vm_stage_reached() {
  [ "$(smarthub_vm_stage_rank "$1")" -ge "$(smarthub_vm_stage_rank "$2")" ]
}

smarthub_vm_ensure_bootstrap_password() {
  local password_file
  password_file="$(smarthub_vm_bootstrap_password_file)"
  if [ -f "$password_file" ]; then
    cat "$password_file"
    return
  fi

  smarthub_vm_ensure_state_dir
  python3 - "$password_file" <<'PY'
import secrets
import sys
from pathlib import Path

path = Path(sys.argv[1])
path.write_text(secrets.token_urlsafe(24))
path.chmod(0o600)
PY
  cat "$password_file"
}

smarthub_vm_write_askpass_script() {
  local askpass password_file
  askpass="$(smarthub_vm_askpass_script)"
  password_file="$(smarthub_vm_bootstrap_password_file)"
  cat > "$askpass" <<EOF
#!/usr/bin/env bash
cat "$password_file"
EOF
  chmod 700 "$askpass"
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

smarthub_vm_prepare_iso() {
  local iso_path iso_url
  iso_path="$(smarthub_vm_iso_path)"
  iso_url="$(smarthub_vm_iso_url)"
  if [ -f "$iso_path" ]; then
    return
  fi

  smarthub_vm_ensure_state_dir
  if smarthub_vm_dry_run_enabled; then
    : > "$iso_path"
    return
  fi

  if ! command -v curl >/dev/null 2>&1; then
    fail_install \
      "curl is required to download the Ubuntu Server ISO." \
      "Install curl on the macOS host, then rerun SmartHub."
  fi

  echo "Downloading Ubuntu Server ISO from $iso_url..."
  curl -fsSL "$iso_url" -o "$iso_path"
}

smarthub_vm_generate_autoinstall_seed() {
  smarthub_vm_ensure_state_dir
  python3 - \
    "$MACOS_VM_SCRIPT_DIR/ubuntu-autoinstall-user-data.yaml" \
    "$MACOS_VM_SCRIPT_DIR/ubuntu-autoinstall-meta-data.yaml" \
    "$(smarthub_vm_state_dir)/user-data" \
    "$(smarthub_vm_state_dir)/meta-data" \
    "$(smarthub_vm_bootstrap_user)" \
    "$(smarthub_vm_hostname)" <<'PY'
from pathlib import Path
import sys

user_template = Path(sys.argv[1]).read_text()
meta_template = Path(sys.argv[2]).read_text()
user_output = Path(sys.argv[3])
meta_output = Path(sys.argv[4])
bootstrap_user = sys.argv[5]
hostname = sys.argv[6]

user_output.write_text(
    user_template
    .replace("__SMARTHUB_BOOTSTRAP_USER__", bootstrap_user)
    .replace("__SMARTHUB_HOSTNAME__", hostname)
)
meta_output.write_text(meta_template.replace("__SMARTHUB_HOSTNAME__", hostname))
PY
}

smarthub_vm_configure_virtualbox_vm() {
  local vm_name bridge_adapter iso_path disk_path ssh_port current_stage
  current_stage="$(smarthub_vm_read_stage)"
  if smarthub_vm_stage_reached "$current_stage" "vm-created"; then
    return
  fi

  vm_name="$(smarthub_vm_name)"
  bridge_adapter="$(smarthub_vm_bridged_adapter)"
  iso_path="$(smarthub_vm_iso_path)"
  disk_path="$(smarthub_vm_disk_path)"
  ssh_port="$(smarthub_vm_ssh_port)"

  VBoxManage createvm --name "$vm_name" --ostype Linux_64 --register
  VBoxManage modifyvm "$vm_name" --firmware efi --memory "$(smarthub_vm_ram_mb)" --cpus "$(smarthub_vm_cpus)"
  VBoxManage modifyvm "$vm_name" --nic1 bridged --bridgeadapter1 "$bridge_adapter"
  VBoxManage modifyvm "$vm_name" --nic2 nat --natpf2 "guestssh,tcp,127.0.0.1,$ssh_port,,22"
  VBoxManage storagectl "$vm_name" --name "SATA Controller" --add sata --controller IntelAhci
  VBoxManage createmedium disk --filename "$disk_path" --size "$(smarthub_vm_disk_mb)" --format VDI
  VBoxManage storageattach "$vm_name" --storagectl "SATA Controller" --port 0 --device 0 --type hdd --medium "$disk_path"
  VBoxManage storagectl "$vm_name" --name "IDE Controller" --add ide
  VBoxManage storageattach "$vm_name" --storagectl "IDE Controller" --port 0 --device 0 --type dvddrive --medium "$iso_path"
  smarthub_vm_write_state "vm-created" "$vm_name" "$ssh_port" "$(smarthub_vm_bootstrap_user)"
}

smarthub_vm_start_unattended_install() {
  local current_stage vm_name iso_path password post_install
  current_stage="$(smarthub_vm_read_stage)"
  if smarthub_vm_stage_reached "$current_stage" "install-started"; then
    return
  fi

  vm_name="$(smarthub_vm_name)"
  iso_path="$(smarthub_vm_iso_path)"
  password="$(smarthub_vm_ensure_bootstrap_password)"
  post_install="sudo DEBIAN_FRONTEND=noninteractive apt-get update && sudo DEBIAN_FRONTEND=noninteractive apt-get install -y openssh-server git curl python3 && sudo systemctl enable ssh"

  VBoxManage unattended install "$vm_name" \
    "--iso=$iso_path" \
    "--user=$(smarthub_vm_bootstrap_user)" \
    "--full-user-name=SmartHub Bootstrap" \
    "--password=$password" \
    "--hostname=$(smarthub_vm_hostname)" \
    "--time-zone=${TZ:-UTC}" \
    "--post-install-command=$post_install" \
    --start-vm=headless
  smarthub_vm_write_state "install-started" "$vm_name" "$(smarthub_vm_ssh_port)" "$(smarthub_vm_bootstrap_user)"
}

smarthub_vm_run_ssh() {
  local user port askpass
  user="$(smarthub_vm_bootstrap_user)"
  port="$(smarthub_vm_ssh_port)"
  smarthub_vm_write_askpass_script
  askpass="$(smarthub_vm_askpass_script)"
  SSH_ASKPASS="$askpass" \
  SSH_ASKPASS_REQUIRE=force \
  DISPLAY="${DISPLAY:-:0}" \
  ssh \
    -o StrictHostKeyChecking=no \
    -o UserKnownHostsFile=/dev/null \
    -o ConnectTimeout=5 \
    -p "$port" \
    "$user@127.0.0.1" \
    "$@" < /dev/null
}

smarthub_vm_wait_for_ssh() {
  local current_stage attempt max_attempts retry_delay
  current_stage="$(smarthub_vm_read_stage)"
  if smarthub_vm_stage_reached "$current_stage" "ssh-ready"; then
    return
  fi

  max_attempts="$(smarthub_vm_ssh_max_attempts)"
  retry_delay="$(smarthub_vm_ssh_retry_delay)"
  attempt=1
  while [ "$attempt" -le "$max_attempts" ]; do
    if smarthub_vm_run_ssh true; then
      smarthub_vm_write_state "ssh-ready" "$(smarthub_vm_name)" "$(smarthub_vm_ssh_port)" "$(smarthub_vm_bootstrap_user)"
      return
    fi

    if [ "$attempt" -lt "$max_attempts" ] && [ "$retry_delay" != "0" ]; then
      sleep "$retry_delay"
    fi
    attempt=$((attempt + 1))
  done

  fail_install \
    "The Linux VM never exposed SSH on forwarded port $(smarthub_vm_ssh_port)." \
    "Check the VirtualBox VM boot log, then rerun SmartHub after the guest finishes installing."
}

smarthub_vm_trigger_guest_install() {
  local guest_repo remote_cmd
  guest_repo="$(smarthub_vm_guest_repo_dir)"
  remote_cmd="git clone '$REPO_URL' '$guest_repo' || (cd '$guest_repo' && git pull --ff-only origin main); cd '$guest_repo'; SMARTHUB_GUEST_INSTALL=1 bash install.sh"
  smarthub_vm_run_ssh "$remote_cmd"
  smarthub_vm_write_state "guest-install-triggered" "$(smarthub_vm_name)" "$(smarthub_vm_ssh_port)" "$(smarthub_vm_bootstrap_user)"
}

run_macos_host_bootstrap() {
  smarthub_vm_arch >/dev/null
  smarthub_vm_require_virtualbox
  smarthub_vm_prepare_iso
  smarthub_vm_generate_autoinstall_seed
  smarthub_vm_configure_virtualbox_vm
  smarthub_vm_start_unattended_install
  smarthub_vm_wait_for_ssh
  smarthub_vm_trigger_guest_install
}
