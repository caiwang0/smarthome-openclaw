import json
import os
import re
import shutil
import subprocess
import tempfile
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
                "SMARTHUB_TEST_RPI_MODEL": "Raspberry Pi 5 Model B Rev 1.0",
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
            self.assertEqual(git_ops, ["git clone https://github.com/caiwang0/smarthome-openclaw.git " + str(target)])

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

    def test_linux_host_path_rejects_non_raspberry_pi_hosts(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            env, _, _ = self.prepare_env(tmp)
            env["SMARTHUB_TEST_ARCH"] = "x86_64"
            env["SMARTHUB_TEST_RPI_MODEL"] = "Generic Linux Host"

            proc = self.run_install(env)

            self.assertNotEqual(proc.returncode, 0)
            combined = (proc.stdout + proc.stderr).lower()
            self.assertIn("unsupported linux host", combined)
            self.assertIn("raspberry pi hosts and macos hosts only", combined)

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
            self.assertIn("HA_URL=http://homeassistant.local:8123", env_text)
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
            self.assertIn("open http://homeassistant.local:8123 in your browser.", proc.stdout.lower())
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
            self.write_stub_script(
                env,
                "VBoxManage",
                """#!/usr/bin/env bash
set -euo pipefail
printf 'VBoxManage %s\\n' "$*" >> "$STUB_LOG"
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
            self.assertIn("VBoxManage modifyvm smarthub-vm --ostype Oracle_arm64", second_log)
            self.assertIn(
                "existing home assistant bootstrap credentials detected; leaving them unchanged.",
                second.stdout.lower(),
            )

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
