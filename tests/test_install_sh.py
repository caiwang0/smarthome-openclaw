import http.server
import json
import os
import re
import shutil
import socketserver
import subprocess
import tempfile
import threading
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
INSTALL_SH = REPO_ROOT / "install.sh"
TOKEN_PATTERN = re.compile(r"\beyJ[a-zA-Z0-9_-]+\.[a-zA-Z0-9_-]+\.[a-zA-Z0-9_-]+\b")


class InstallScriptTests(unittest.TestCase):
    maxDiff = None

    def write_stub_commands(self, stub_bin: Path) -> None:
        stub_bin.mkdir(parents=True, exist_ok=True)

        scripts = {
            "git": """#!/usr/bin/env bash
set -euo pipefail
if [ -n "${STUB_LOG:-}" ]; then
  printf 'git %s\\n' "$*" >> "$STUB_LOG"
fi
if [ "${1:-}" = "clone" ]; then
  cp -a "$FIXTURE_REPO" "$3"
  mkdir -p "$3/.git"
  exit 0
fi
if [ "${1:-}" = "pull" ]; then
  exit 0
fi
exit 0
""",
            "curl": """#!/usr/bin/env bash
set -euo pipefail
output=""
while [ "$#" -gt 0 ]; do
  case "$1" in
    -o)
      output="$2"
      shift 2
      ;;
    *)
      shift
      ;;
  esac
done
if [ -n "$output" ]; then
  : > "$output"
  exit 0
fi
if [ "${STUB_FAIL_UV_INSTALL:-0}" = "1" ]; then
  echo "simulated uv install failure" >&2
  exit 1
fi
printf '#!/bin/sh\\nexit 0\\n'
""",
            "uv": """#!/usr/bin/env bash
set -euo pipefail
args=()
skip_next=0
for arg in "$@"; do
  if [ "$skip_next" = 1 ]; then
    skip_next=0
    continue
  fi
  case "$arg" in
    run)
      ;;
    --with)
      skip_next=1
      ;;
    *)
      args+=("$arg")
      ;;
  esac
done
exec python3 "${args[@]}"
""",
            "uvx": """#!/usr/bin/env bash
exit 0
""",
            "docker": """#!/usr/bin/env bash
set -euo pipefail
if [ -n "${STUB_LOG:-}" ]; then
  printf 'docker %s\\n' "$*" >> "$STUB_LOG"
fi
if [ "${1:-}" = "--version" ]; then
  echo "Docker version 27.0.0, build stub"
  exit 0
fi
if [ "${1:-}" = "compose" ] && [ "${2:-}" = "up" ] && [ "${3:-}" = "-d" ]; then
  exit 0
fi
exit 0
""",
            "ss": """#!/usr/bin/env bash
exit 1
""",
        }

        for name, contents in scripts.items():
            path = stub_bin / name
            path.write_text(contents)
            path.chmod(0o755)

    def prepare_env(self, tmp: str) -> tuple[dict[str, str], Path, Path]:
        root = Path(tmp)
        home = root / "home"
        workspace = home / ".openclaw" / "workspace"
        config_path = home / ".openclaw" / "openclaw.json"
        stub_bin = root / "bin"
        stub_py = root / "python-stubs"
        repo_copy = root / "fixture-repo"

        workspace.mkdir(parents=True)
        config_path.parent.mkdir(parents=True, exist_ok=True)
        stub_py.mkdir(parents=True, exist_ok=True)
        shutil.copytree(
            REPO_ROOT,
            repo_copy,
            dirs_exist_ok=True,
            ignore=shutil.ignore_patterns(
                ".git",
                ".codex",
                ".superpowers",
                "memory",
                ".storage",
                ".HA_VERSION",
                ".ha_run.lock",
                "home-assistant.log",
                "home-assistant.log.1",
                "home-assistant.log.fault",
                "home-assistant_v2.db",
                "home-assistant_v2.db-shm",
                "home-assistant_v2.db-wal",
            ),
        )
        config_path.write_text(
            json.dumps({"agents": {"defaults": {"workspace": str(workspace)}}})
        )
        (stub_py / "bcrypt.py").write_text(
            "import hashlib\n"
            "\n"
            "def gensalt(rounds=12):\n"
            "    return b'stub-salt'\n"
            "\n"
            "def hashpw(password, salt):\n"
            "    return b'stub-' + hashlib.sha256(password + salt).hexdigest().encode()\n"
        )
        self.write_stub_commands(stub_bin)

        env = os.environ.copy()
        env.update(
            {
                "HOME": str(home),
                "PATH": f"{stub_bin}:{env['PATH']}",
                "PYTHONPATH": f"{stub_py}:{env.get('PYTHONPATH', '')}".rstrip(":"),
                "OPENCLAW_WORKSPACE": str(workspace),
                "FIXTURE_REPO": str(repo_copy),
                "SMARTHUB_TEST_UNAME": "Linux",
                "SMARTHUB_VM_ENV_FILE": str(root / ".env"),
                "SMARTHUB_VM_ENV_EXAMPLE_FILE": str(REPO_ROOT / ".env.example"),
            }
        )
        return env, workspace / "smarthome-openclaw", repo_copy

    def make_existing_target(self, repo_copy: Path, target: Path) -> None:
        shutil.copytree(
            repo_copy,
            target,
            dirs_exist_ok=True,
            ignore=shutil.ignore_patterns(
                ".codex",
                ".superpowers",
                "memory",
                ".storage",
                ".HA_VERSION",
                ".ha_run.lock",
                "home-assistant.log",
                "home-assistant.log.1",
                "home-assistant.log.fault",
                "home-assistant_v2.db",
                "home-assistant_v2.db-shm",
                "home-assistant_v2.db-wal",
            ),
        )
        (target / ".git").mkdir(parents=True, exist_ok=True)

    def write_resume_checkpoint(self, target: Path, token: str) -> None:
        checkpoint = target / ".openclaw" / "install-state.json"
        checkpoint.parent.mkdir(parents=True, exist_ok=True)
        checkpoint.write_text(
            json.dumps(
                {
                    "phase": "seed-complete",
                    "token": token,
                    "username": "openclaw",
                    "name": "OpenClaw",
                }
            )
            + "\n"
        )
        checkpoint.chmod(0o600)

    def run_install(
        self,
        env: dict[str, str],
        script_path: Path | None = None,
    ) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            ["bash", str(script_path or INSTALL_SH)],
            capture_output=True,
            text=True,
            env=env,
        )

    def stub_bin_path(self, env: dict[str, str]) -> Path:
        return Path(env["PATH"].split(":", 1)[0])

    def write_stub_script(self, env: dict[str, str], name: str, contents: str) -> None:
        path = self.stub_bin_path(env) / name
        path.write_text(contents)
        path.chmod(0o755)

    def constrain_path_to_stubs(self, env: dict[str, str]) -> None:
        env["PATH"] = f"{self.stub_bin_path(env)}:/usr/bin:/bin:/usr/sbin:/sbin"

    def test_macos_host_path_stops_before_workspace_lookup_without_virtualbox(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            env, _, _ = self.prepare_env(tmp)
            shutil.rmtree(Path(env["OPENCLAW_WORKSPACE"]))
            env.pop("OPENCLAW_WORKSPACE", None)
            env["SMARTHUB_TEST_UNAME"] = "Darwin"
            self.constrain_path_to_stubs(env)

            proc = self.run_install(env)

            self.assertNotEqual(proc.returncode, 0)
            combined = (proc.stdout + proc.stderr).lower()
            self.assertIn("virtualbox", combined)
            self.assertNotIn("workspace not found", combined)

    def test_install_bootstraps_repo_when_run_from_standalone_script(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            env, target, _ = self.prepare_env(tmp)
            env["STUB_LOG"] = str(Path(tmp) / "stub.log")
            standalone = Path(tmp) / "install.sh"
            standalone.write_text(INSTALL_SH.read_text())
            standalone.chmod(0o755)

            proc = self.run_install(env, standalone)

            self.assertEqual(proc.returncode, 0, proc.stderr)
            self.assertTrue((target / "scripts" / "linux-guest-install.sh").exists())
            combined = (proc.stdout + proc.stderr).lower()
            self.assertNotIn("installer helper missing", combined)

            git_ops = Path(env["STUB_LOG"]).read_text().splitlines()
            self.assertEqual(
                git_ops,
                [
                    "git clone https://github.com/caiwang0/smarthome-openclaw.git " + str(target),
                    "docker compose up -d",
                ],
            )

    def test_linux_guest_install_helper_exposes_entrypoint(self) -> None:
        helper = REPO_ROOT / "scripts" / "linux-guest-install.sh"
        proc = subprocess.run(
            [
                "bash",
                "-lc",
                f". '{helper}'; declare -F run_linux_guest_install",
            ],
            capture_output=True,
            text=True,
        )

        self.assertEqual(proc.returncode, 0, proc.stderr or proc.stdout)
        self.assertIn("run_linux_guest_install", proc.stdout)

    def test_linux_host_path_allows_generic_linux_hosts(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            env, _, _ = self.prepare_env(tmp)
            env["SMARTHUB_TEST_ARCH"] = "x86_64"

            proc = self.run_install(env)

            self.assertEqual(proc.returncode, 0, proc.stderr)
            combined = (proc.stdout + proc.stderr).lower()
            self.assertNotIn("unsupported linux host", combined)

    def test_linux_host_path_starts_home_assistant_container(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            env, _, _ = self.prepare_env(tmp)
            env["STUB_LOG"] = str(Path(tmp) / "stub.log")

            proc = self.run_install(env)

            self.assertEqual(proc.returncode, 0, proc.stderr)
            log_text = Path(env["STUB_LOG"]).read_text()
            self.assertIn("docker compose up -d", log_text)

    def test_macos_host_path_installs_virtualbox_with_brew_when_missing(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            env, _, _ = self.prepare_env(tmp)
            env["SMARTHUB_TEST_UNAME"] = "Darwin"
            env["SMARTHUB_TEST_ARCH"] = "arm64"
            env["SMARTHUB_VM_DRY_RUN"] = "1"
            env["STUB_LOG"] = str(Path(tmp) / "stub.log")
            env["STUB_BIN"] = str(self.stub_bin_path(env))
            self.constrain_path_to_stubs(env)

            self.write_stub_script(
                env,
                "brew",
                """#!/usr/bin/env bash
set -euo pipefail
printf 'brew %s\\n' "$*" >> "$STUB_LOG"
cat > "$STUB_BIN/VBoxManage" <<'EOF'
#!/usr/bin/env bash
set -euo pipefail
printf 'VBoxManage %s\\n' "$*" >> "$STUB_LOG"
exit 0
EOF
chmod +x "$STUB_BIN/VBoxManage"
""",
            )

            proc = self.run_install(env)

            self.assertEqual(proc.returncode, 0, proc.stderr)
            log_text = Path(env["STUB_LOG"]).read_text()
            self.assertIn("brew install --cask virtualbox", log_text)
            self.assertIn("VBoxManage createvm", log_text)
            self.assertIn("home assistant admin username: openclaw", proc.stdout.lower())
            self.assertIn("save this, it's the only time you'll see it.", proc.stdout.lower())

    def test_macos_host_path_rejects_unknown_arch(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            env, _, _ = self.prepare_env(tmp)
            env["SMARTHUB_TEST_UNAME"] = "Darwin"
            env["SMARTHUB_TEST_ARCH"] = "ppc64"
            env["STUB_LOG"] = str(Path(tmp) / "stub.log")
            self.constrain_path_to_stubs(env)
            self.write_stub_script(
                env,
                "VBoxManage",
                """#!/usr/bin/env bash
set -euo pipefail
printf 'VBoxManage %s\\n' "$*" >> "$STUB_LOG"
exit 0
""",
            )
            proc = self.run_install(env)

            self.assertNotEqual(proc.returncode, 0)
            combined = (proc.stdout + proc.stderr).lower()
            self.assertIn("unsupported mac architecture", combined)

    def test_macos_host_path_selects_apple_silicon_haos_disk_image(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            env, _, _ = self.prepare_env(tmp)
            env["SMARTHUB_TEST_UNAME"] = "Darwin"
            env["SMARTHUB_TEST_ARCH"] = "arm64"
            env["SMARTHUB_VM_DRY_RUN"] = "1"
            env["STUB_LOG"] = str(Path(tmp) / "stub.log")
            env["SMARTHUB_VM_BRIDGE_ADAPTER"] = "en0"
            self.constrain_path_to_stubs(env)
            self.write_stub_script(
                env,
                "VBoxManage",
                """#!/usr/bin/env bash
set -euo pipefail
printf 'VBoxManage %s\\n' "$*" >> "$STUB_LOG"
exit 0
""",
            )

            proc = self.run_install(env)

            self.assertEqual(proc.returncode, 0, proc.stderr)
            log_text = Path(env["STUB_LOG"]).read_text()
            disk_path = Path(env["HOME"]) / ".smarthub-vm" / "cache" / "haos_generic-aarch64.vmdk"
            self.assertIn(
                "VBoxManage createvm --name smarthub-vm --platform-architecture arm --ostype Oracle_arm64 --register",
                log_text,
            )
            self.assertIn("VBoxManage modifyvm smarthub-vm --firmware efi --memory 2048 --cpus 2", log_text)
            self.assertIn("VBoxManage modifyvm smarthub-vm --graphicscontroller qemuramfb", log_text)
            self.assertIn("VBoxManage modifyvm smarthub-vm --nic1 bridged --bridgeadapter1 en0", log_text)
            self.assertIn(
                f'VBoxManage storageattach smarthub-vm --storagectl SATA --port 0 --device 0 --type hdd --medium {disk_path}',
                log_text,
            )
            self.assertIn("VBoxManage startvm smarthub-vm --type headless", log_text)
            self.assertIn("home assistant os vm started.", proc.stdout.lower())
            self.assertIn("home assistant admin username: openclaw", proc.stdout.lower())
            self.assertIn("home assistant admin password: dry-run-password", proc.stdout.lower())
            env_text = Path(env["SMARTHUB_VM_ENV_FILE"]).read_text()
            self.assertIn("HA_URL=http://192.168.2.142:8123", env_text)
            self.assertIn("HA_TOKEN=dry-run-token", env_text)

    def test_macos_host_path_selects_intel_haos_disk_image(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            env, _, _ = self.prepare_env(tmp)
            env["SMARTHUB_TEST_UNAME"] = "Darwin"
            env["SMARTHUB_TEST_ARCH"] = "x86_64"
            env["SMARTHUB_VM_DRY_RUN"] = "1"
            env["SMARTHUB_VM_BRIDGE_ADAPTER"] = "en0"
            env["STUB_LOG"] = str(Path(tmp) / "stub.log")
            self.constrain_path_to_stubs(env)
            self.write_stub_script(
                env,
                "VBoxManage",
                """#!/usr/bin/env bash
set -euo pipefail
printf 'VBoxManage %s\\n' "$*" >> "$STUB_LOG"
exit 0
""",
            )

            proc = self.run_install(env)

            self.assertEqual(proc.returncode, 0, proc.stderr)
            log_text = Path(env["STUB_LOG"]).read_text()
            disk_path = Path(env["HOME"]) / ".smarthub-vm" / "cache" / "haos_ova.vdi"
            self.assertIn(
                "VBoxManage createvm --name smarthub-vm --platform-architecture x86 --ostype Oracle_64 --register",
                log_text,
            )
            self.assertIn("VBoxManage modifyvm smarthub-vm --graphicscontroller vmsvga", log_text)
            self.assertIn(
                f'VBoxManage storageattach smarthub-vm --storagectl SATA --port 0 --device 0 --type hdd --medium {disk_path}',
                log_text,
            )
            self.assertIn("open http://192.168.2.142:8123 in your browser.", proc.stdout.lower())
            self.assertIn("home assistant vm ip: 192.168.2.142", proc.stdout.lower())
            self.assertNotIn("unattended install", log_text.lower())

    def test_macos_host_path_resume_skips_vm_creation_when_bootstrap_already_complete(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            env, _, _ = self.prepare_env(tmp)
            env["SMARTHUB_TEST_UNAME"] = "Darwin"
            env["SMARTHUB_TEST_ARCH"] = "arm64"
            env["SMARTHUB_VM_DRY_RUN"] = "1"
            env["SMARTHUB_VM_BRIDGE_ADAPTER"] = "en0"
            env["STUB_LOG"] = str(Path(tmp) / "stub.log")
            self.constrain_path_to_stubs(env)
            disk_path = Path(env["HOME"]) / ".smarthub-vm" / "cache" / "haos_generic-aarch64.vmdk"
            self.write_stub_script(
                env,
                "VBoxManage",
                f"""#!/usr/bin/env bash
set -euo pipefail
printf 'VBoxManage %s\\n' "$*" >> "$STUB_LOG"
if [ "${{1:-}}" = "showvminfo" ]; then
  cat <<'EOF'
platformArchitecture="ARM"
"SATA-0-0"="{disk_path}"
VMState="running"
EOF
  exit 0
fi
exit 0
""",
            )

            first = self.run_install(env)
            self.assertEqual(first.returncode, 0, first.stderr)
            checkpoint = Path(env["HOME"]) / ".smarthub-vm" / "bootstrap-state.json"
            self.assertTrue(checkpoint.exists())
            payload = json.loads(checkpoint.read_text())
            self.assertEqual(payload["stage"], "ha-bootstrapped")

            Path(env["STUB_LOG"]).write_text("")
            second = self.run_install(env)

            self.assertEqual(second.returncode, 0, second.stderr)
            second_log = Path(env["STUB_LOG"]).read_text()
            self.assertNotIn("VBoxManage createvm", second_log)
            self.assertNotIn("VBoxManage startvm", second_log)
            self.assertNotIn("VBoxManage modifyvm", second_log)
            self.assertIn(
                "existing home assistant bootstrap credentials detected; leaving them unchanged.",
                second.stdout.lower(),
            )

    def test_macos_host_path_resume_reuses_existing_vm_when_virtualbox_reports_uppercase_arm_arch(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            env, _, _ = self.prepare_env(tmp)
            env["SMARTHUB_TEST_UNAME"] = "Darwin"
            env["SMARTHUB_TEST_ARCH"] = "arm64"
            env["SMARTHUB_VM_DRY_RUN"] = "1"
            env["SMARTHUB_VM_BRIDGE_ADAPTER"] = "en0"
            env["STUB_LOG"] = str(Path(tmp) / "stub.log")
            self.constrain_path_to_stubs(env)

            state_dir = Path(env["HOME"]) / ".smarthub-vm"
            cache_dir = state_dir / "cache"
            cache_dir.mkdir(parents=True, exist_ok=True)
            disk_path = cache_dir / "haos_generic-aarch64.vmdk"
            disk_path.write_text("")
            (state_dir / "bootstrap-state.json").write_text(
                json.dumps({"stage": "ha-bootstrapped", "vm_name": "smarthub-vm"}) + "\n"
            )
            (state_dir / "ha-bootstrap.json").write_text(
                json.dumps(
                    {
                        "base_url": "http://homeassistant.local:8123",
                        "resolved_ip": "192.168.2.142",
                        "created": False,
                        "token": "existing-token",
                    }
                )
                + "\n"
            )

            self.write_stub_script(
                env,
                "VBoxManage",
                f"""#!/usr/bin/env bash
set -euo pipefail
printf 'VBoxManage %s\\n' "$*" >> "$STUB_LOG"
if [ "${{1:-}}" = "showvminfo" ]; then
  cat <<'EOF'
platformArchitecture="ARM"
"SATA-0-0"="{disk_path}"
VMState="poweroff"
EOF
  exit 0
fi
exit 0
""",
            )

            proc = self.run_install(env)

            self.assertEqual(proc.returncode, 0, proc.stderr)
            log_text = Path(env["STUB_LOG"]).read_text()
            self.assertNotIn("VBoxManage unregistervm", log_text)
            self.assertNotIn("VBoxManage createvm", log_text)
            self.assertIn("VBoxManage modifyvm smarthub-vm --ostype Oracle_arm64", log_text)
            self.assertIn(
                "existing home assistant bootstrap credentials detected; leaving them unchanged.",
                proc.stdout.lower(),
            )

    def test_macos_host_path_resume_skips_modify_and_start_when_vm_checkpoint_is_running(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            env, _, _ = self.prepare_env(tmp)
            env["SMARTHUB_TEST_UNAME"] = "Darwin"
            env["SMARTHUB_TEST_ARCH"] = "arm64"
            env["SMARTHUB_VM_DRY_RUN"] = "1"
            env["SMARTHUB_VM_BRIDGE_ADAPTER"] = "en0"
            env["STUB_LOG"] = str(Path(tmp) / "stub.log")
            self.constrain_path_to_stubs(env)

            state_dir = Path(env["HOME"]) / ".smarthub-vm"
            cache_dir = state_dir / "cache"
            cache_dir.mkdir(parents=True, exist_ok=True)
            disk_path = cache_dir / "haos_generic-aarch64.vmdk"
            disk_path.write_text("")
            (state_dir / "bootstrap-state.json").write_text(
                json.dumps({"stage": "vm-started", "vm_name": "smarthub-vm"}) + "\n"
            )

            self.write_stub_script(
                env,
                "VBoxManage",
                f"""#!/usr/bin/env bash
set -euo pipefail
printf 'VBoxManage %s\\n' "$*" >> "$STUB_LOG"
if [ "${{1:-}}" = "showvminfo" ]; then
  cat <<'EOF'
platformArchitecture="ARM"
"SATA-0-0"="{disk_path}"
VMState="running"
EOF
  exit 0
fi
exit 0
""",
            )

            proc = self.run_install(env)

            self.assertEqual(proc.returncode, 0, proc.stderr)
            log_text = Path(env["STUB_LOG"]).read_text()
            self.assertNotIn("VBoxManage createvm", log_text)
            self.assertNotIn("VBoxManage modifyvm", log_text)
            self.assertNotIn("VBoxManage startvm", log_text)

    def test_macos_host_path_vm_started_checkpoint_restarts_powered_off_vm(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            env, _, _ = self.prepare_env(tmp)
            env["SMARTHUB_TEST_UNAME"] = "Darwin"
            env["SMARTHUB_TEST_ARCH"] = "arm64"
            env["SMARTHUB_VM_DRY_RUN"] = "1"
            env["SMARTHUB_VM_BRIDGE_ADAPTER"] = "en0"
            env["STUB_LOG"] = str(Path(tmp) / "stub.log")
            self.constrain_path_to_stubs(env)

            state_dir = Path(env["HOME"]) / ".smarthub-vm"
            cache_dir = state_dir / "cache"
            cache_dir.mkdir(parents=True, exist_ok=True)
            disk_path = cache_dir / "haos_generic-aarch64.vmdk"
            disk_path.write_text("")
            (state_dir / "bootstrap-state.json").write_text(
                json.dumps({"stage": "vm-started", "vm_name": "smarthub-vm"}) + "\n"
            )

            self.write_stub_script(
                env,
                "VBoxManage",
                f"""#!/usr/bin/env bash
set -euo pipefail
printf 'VBoxManage %s\\n' "$*" >> "$STUB_LOG"
if [ "${{1:-}}" = "showvminfo" ]; then
  cat <<'EOF'
platformArchitecture="ARM"
"SATA-0-0"="{disk_path}"
VMState="poweroff"
EOF
  exit 0
fi
exit 0
""",
            )

            proc = self.run_install(env)

            self.assertEqual(proc.returncode, 0, proc.stderr)
            log_text = Path(env["STUB_LOG"]).read_text()
            self.assertIn("VBoxManage modifyvm smarthub-vm --ostype Oracle_arm64", log_text)
            self.assertIn("VBoxManage startvm smarthub-vm --type headless", log_text)

    def test_macos_host_path_recreates_vm_when_checkpoint_exists_but_virtualbox_vm_is_missing(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            env, _, _ = self.prepare_env(tmp)
            env["SMARTHUB_TEST_UNAME"] = "Darwin"
            env["SMARTHUB_TEST_ARCH"] = "arm64"
            env["SMARTHUB_VM_DRY_RUN"] = "1"
            env["SMARTHUB_VM_BRIDGE_ADAPTER"] = "en0"
            env["STUB_LOG"] = str(Path(tmp) / "stub.log")
            self.constrain_path_to_stubs(env)

            state_dir = Path(env["HOME"]) / ".smarthub-vm"
            state_dir.mkdir(parents=True, exist_ok=True)
            (state_dir / "bootstrap-state.json").write_text(
                json.dumps({"stage": "vm-started", "vm_name": "smarthub-vm"}) + "\n"
            )

            showvminfo_state = Path(tmp) / "showvminfo-state"
            disk_path = state_dir / "cache" / "haos_generic-aarch64.vmdk"

            self.write_stub_script(
                env,
                "VBoxManage",
                f"""#!/usr/bin/env bash
set -euo pipefail
printf 'VBoxManage %s\\n' "$*" >> "$STUB_LOG"
if [ "${{1:-}}" = "showvminfo" ]; then
  if [ ! -f "{showvminfo_state}" ]; then
    : > "{showvminfo_state}"
    exit 1
  fi
  cat <<'EOF'
platformArchitecture="ARM"
"SATA-0-0"="{disk_path}"
VMState="poweroff"
EOF
  exit 0
fi
exit 0
""",
            )

            proc = self.run_install(env)

            self.assertEqual(proc.returncode, 0, proc.stderr)
            log_text = Path(env["STUB_LOG"]).read_text()
            self.assertIn("VBoxManage createvm --name smarthub-vm --platform-architecture arm --ostype Oracle_arm64 --register", log_text)
            self.assertIn("VBoxManage startvm smarthub-vm --type headless", log_text)
            self.assertNotIn("VBoxManage unregistervm", log_text)

    def test_macos_host_path_requires_manual_recreate_for_existing_vm_mismatch(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            env, _, _ = self.prepare_env(tmp)
            env["SMARTHUB_TEST_UNAME"] = "Darwin"
            env["SMARTHUB_TEST_ARCH"] = "arm64"
            env["SMARTHUB_VM_DRY_RUN"] = "1"
            env["SMARTHUB_VM_BRIDGE_ADAPTER"] = "en0"
            env["STUB_LOG"] = str(Path(tmp) / "stub.log")
            self.constrain_path_to_stubs(env)

            state_dir = Path(env["HOME"]) / ".smarthub-vm"
            cache_dir = state_dir / "cache"
            cache_dir.mkdir(parents=True, exist_ok=True)
            disk_path = cache_dir / "haos_generic-aarch64.vmdk"
            disk_path.write_text("")
            (state_dir / "bootstrap-state.json").write_text(
                json.dumps({"stage": "vm-created", "vm_name": "smarthub-vm"}) + "\n"
            )

            self.write_stub_script(
                env,
                "VBoxManage",
                f"""#!/usr/bin/env bash
set -euo pipefail
printf 'VBoxManage %s\\n' "$*" >> "$STUB_LOG"
if [ "${{1:-}}" = "showvminfo" ]; then
  cat <<'EOF'
platformArchitecture="x86"
"SATA-0-0"="{disk_path}"
VMState="poweroff"
EOF
  exit 0
fi
exit 0
""",
            )

            proc = self.run_install(env)

            self.assertNotEqual(proc.returncode, 0)
            combined = (proc.stdout + proc.stderr).lower()
            self.assertIn("does not match the expected smarthub configuration", combined)
            self.assertIn("delete ~/.smarthub-vm", combined)
            log_text = Path(env["STUB_LOG"]).read_text()
            self.assertNotIn("VBoxManage unregistervm", log_text)
            self.assertNotIn("VBoxManage createvm", log_text)

    def test_macos_vm_detect_ha_port_finds_responsive_candidate_port(self) -> None:
        class Handler(http.server.BaseHTTPRequestHandler):
            def do_GET(self) -> None:  # noqa: N802
                if self.path != "/api/onboarding":
                    self.send_error(404)
                    return
                body = b"[]"
                self.send_response(200)
                self.send_header("Content-Type", "application/json")
                self.send_header("Content-Length", str(len(body)))
                self.end_headers()
                self.wfile.write(body)

            def log_message(self, format: str, *args: object) -> None:
                return

        with socketserver.TCPServer(("127.0.0.1", 0), Handler) as server:
            port = server.server_address[1]
            thread = threading.Thread(target=server.serve_forever, daemon=True)
            thread.start()
            try:
                helper = REPO_ROOT / "scripts" / "macos-vm-bootstrap.sh"
                proc = subprocess.run(
                    [
                        "bash",
                        "-lc",
                        "\n".join(
                            [
                                "set -euo pipefail",
                                "fail_install() { echo \"$1\" >&2; exit 1; }",
                                f"SCRIPT_DIR='{REPO_ROOT}'",
                                f". '{helper}'",
                                "export SMARTHUB_VM_HA_BOOTSTRAP_TIMEOUT_SECONDS=5",
                                "export SMARTHUB_VM_HA_BOOTSTRAP_POLL_INTERVAL_SECONDS=1",
                                f"export SMARTHUB_VM_HA_PORT_CANDIDATES='1 {port}'",
                                "smarthub_vm_detect_ha_port 127.0.0.1",
                            ]
                        ),
                    ],
                    capture_output=True,
                    text=True,
                )
            finally:
                server.shutdown()
                thread.join()

        self.assertEqual(proc.returncode, 0, proc.stderr)
        self.assertEqual(proc.stdout.strip(), str(port))

    def test_macos_vm_detect_ip_matches_zero_padded_virtualbox_mac_to_arp_entry(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            helper = REPO_ROOT / "scripts" / "macos-vm-bootstrap.sh"
            stub_bin = Path(tmp) / "bin"
            stub_bin.mkdir(parents=True, exist_ok=True)

            (stub_bin / "VBoxManage").write_text(
                """#!/usr/bin/env bash
set -euo pipefail
cat <<'EOF'
macaddress1="08002743E955"
EOF
"""
            )
            (stub_bin / "VBoxManage").chmod(0o755)

            (stub_bin / "ifconfig").write_text(
                """#!/usr/bin/env bash
set -euo pipefail
cat <<'EOF'
en0: flags=8863<UP,BROADCAST,RUNNING,SIMPLEX,MULTICAST> mtu 1500
\tinet 192.168.2.10 netmask 0xffffff00 broadcast 192.168.2.255
EOF
"""
            )
            (stub_bin / "ifconfig").chmod(0o755)

            (stub_bin / "arp").write_text(
                """#!/usr/bin/env bash
set -euo pipefail
cat <<'EOF'
? (192.168.2.144) at 8:0:27:43:e9:55 on en0 ifscope [ethernet]
EOF
"""
            )
            (stub_bin / "arp").chmod(0o755)

            proc = subprocess.run(
                [
                    "bash",
                    "-lc",
                    "\n".join(
                        [
                            "set -euo pipefail",
                            "fail_install() { echo \"$1\" >&2; exit 1; }",
                            f"export PATH='{stub_bin}:/usr/bin:/bin:/usr/sbin:/sbin'",
                            f"SCRIPT_DIR='{REPO_ROOT}'",
                            f". '{helper}'",
                            "export SMARTHUB_VM_BRIDGE_ADAPTER='en0'",
                            "export SMARTHUB_VM_HA_BOOTSTRAP_TIMEOUT_SECONDS=2",
                            "export SMARTHUB_VM_HA_BOOTSTRAP_POLL_INTERVAL_SECONDS=1",
                            "smarthub_vm_detect_ip",
                        ]
                    ),
                ],
                capture_output=True,
                text=True,
            )

        self.assertEqual(proc.returncode, 0, proc.stderr)
        self.assertEqual(proc.stdout.strip(), "192.168.2.144")

    def test_install_seeds_token_and_prints_password_once_on_fresh_install(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            env, target, _ = self.prepare_env(tmp)

            proc = self.run_install(env)

            self.assertEqual(proc.returncode, 0, proc.stderr)
            self.assertIn("save this, it's the only time you'll see it.", proc.stdout.lower())
            self.assertIn("home assistant admin username: openclaw", proc.stdout.lower())
            self.assertIn("skip steps 3, 5, 6, and 7", proc.stdout.lower())
            self.assertIsNone(TOKEN_PATTERN.search(proc.stdout))

            env_text = (target / ".env").read_text()
            self.assertNotIn("your_long_lived_access_token_here", env_text)

            storage_dir = target / "ha-config" / ".storage"
            for filename in (
                "auth",
                "auth_provider.homeassistant",
                "onboarding",
                "core.config",
            ):
                self.assertTrue((storage_dir / filename).exists(), filename)

    def test_second_install_keeps_existing_credentials_hidden(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            env, target, _ = self.prepare_env(tmp)

            first = self.run_install(env)
            self.assertEqual(first.returncode, 0, first.stderr)
            env_after_first = (target / ".env").read_text()

            second = self.run_install(env)

            self.assertEqual(second.returncode, 0, second.stderr)
            self.assertNotIn("home assistant admin password:", second.stdout.lower())
            self.assertNotIn("save this, it's the only time you'll see it.", second.stdout.lower())
            self.assertEqual(env_after_first, (target / ".env").read_text())

    def test_install_restores_token_from_checkpoint_after_seed_interruption(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            env, target, repo_copy = self.prepare_env(tmp)
            self.make_existing_target(repo_copy, target)
            storage = target / "ha-config" / ".storage"
            storage.mkdir(parents=True, exist_ok=True)
            for name in ("auth", "auth_provider.homeassistant", "onboarding", "core.config"):
                (storage / name).write_text("{}\n")
                (storage / name).chmod(0o600)

            (target / ".env").write_text(
                "\n".join(
                    [
                        "HA_URL=http://localhost:8123",
                        "HA_TOKEN=your_long_lived_access_token_here",
                    ]
                )
                + "\n"
            )
            self.write_resume_checkpoint(target, "resume-token-123")

            proc = self.run_install(env)

            self.assertEqual(proc.returncode, 0, proc.stderr)
            env_text = (target / ".env").read_text()
            self.assertIn("HA_TOKEN=resume-token-123", env_text)
            self.assertNotIn("your_long_lived_access_token_here", env_text)
            self.assertFalse((target / ".openclaw" / "install-state.json").exists())
            self.assertNotIn("Home Assistant admin password:", proc.stdout)
            self.assertNotIn("browser", proc.stdout.lower())

    def test_install_stops_when_seeded_storage_has_no_checkpoint(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            env, target, repo_copy = self.prepare_env(tmp)
            self.make_existing_target(repo_copy, target)
            storage = target / "ha-config" / ".storage"
            storage.mkdir(parents=True, exist_ok=True)
            for name in ("auth", "auth_provider.homeassistant", "onboarding", "core.config"):
                (storage / name).write_text("{}\n")
                (storage / name).chmod(0o600)

            (target / ".env").write_text(
                "\n".join(
                    [
                        "HA_URL=http://localhost:8123",
                        "HA_TOKEN=your_long_lived_access_token_here",
                    ]
                )
                + "\n"
            )

            proc = self.run_install(env)

            self.assertNotEqual(proc.returncode, 0)
            combined = (proc.stdout + proc.stderr).lower()
            self.assertIn("checkpoint", combined)
            self.assertIn("partial bootstrap", combined)

    def test_install_prints_phase_labels_for_slow_steps(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            env, _, _ = self.prepare_env(tmp)

            proc = self.run_install(env)

            self.assertEqual(proc.returncode, 0, proc.stderr)
            output = proc.stdout.lower()
            for phase in (
                "repo sync",
                "patch openclaw config",
                "install uv",
                "bootstrap home assistant auth",
                "sync ha token",
                "verify ha-mcp",
                "handoff",
            ):
                self.assertIn(f"[install] start: {phase}", output)
                self.assertIn(f"[install] done: {phase}", output)

    def test_install_reports_failing_phase_name(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            env, _, _ = self.prepare_env(tmp)
            env["STUB_FAIL_UV_INSTALL"] = "1"

            proc = self.run_install(env)

            self.assertNotEqual(proc.returncode, 0)
            combined = (proc.stdout + proc.stderr).lower()
            self.assertIn("[install] failed: install uv", combined)


if __name__ == "__main__":
    unittest.main()
