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
if [ "${1:-}" = "clone" ]; then
  cp -a "$FIXTURE_REPO" "$3"
  exit 0
fi
if [ "${1:-}" = "pull" ]; then
  exit 0
fi
exit 0
""",
            "curl": """#!/usr/bin/env bash
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
            "docker": """#!/usr/bin/env bash
set -euo pipefail
case "${1:-}" in
  --version|version)
    if [ "${STUB_DOCKER_VERSION_FAIL:-0}" = "1" ]; then
      echo "docker cli unavailable" >&2
      exit 1
    fi
    echo "Docker version 27.5.1"
    ;;
  info)
    if [ "${STUB_DOCKER_INFO_FAIL:-0}" = "1" ]; then
      echo "docker daemon unavailable" >&2
      exit 1
    fi
    echo "Docker info OK"
    ;;
  compose)
    shift
    if [ "${1:-}" = "version" ]; then
      if [ "${STUB_DOCKER_COMPOSE_FAIL:-0}" = "1" ]; then
        echo "docker compose unavailable" >&2
        exit 1
      fi
      echo "Docker Compose version v2.33.0"
      exit 0
    fi
    exit 0
    ;;
  *)
    exit 0
    ;;
esac
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
        repo_copy = root / "fixture-repo"

        workspace.mkdir(parents=True)
        config_path.parent.mkdir(parents=True, exist_ok=True)
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
        self.write_stub_commands(stub_bin)

        env = os.environ.copy()
        env.update(
            {
                "HOME": str(home),
                "PATH": f"{stub_bin}:{env['PATH']}",
                "OPENCLAW_WORKSPACE": str(workspace),
                "FIXTURE_REPO": str(repo_copy),
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

    def run_install(self, env: dict[str, str]) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            ["bash", str(INSTALL_SH)],
            capture_output=True,
            text=True,
            env=env,
        )

    def test_install_seeds_token_and_prints_password_once_on_fresh_install(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            env, target, _ = self.prepare_env(tmp)

            proc = self.run_install(env)

            self.assertEqual(proc.returncode, 0, proc.stderr)
            self.assertIn("save this, it's the only time you'll see it.", proc.stdout.lower())
            self.assertIn("home assistant admin username: openclaw", proc.stdout.lower())
            self.assertIn("use setup.md to decide which steps are already satisfied", proc.stdout.lower())
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

    def test_install_reports_platform_branch_before_repo_sync(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            env, _, _ = self.prepare_env(tmp)
            env["SMARTHUB_TEST_UNAME"] = "Darwin"

            proc = self.run_install(env)

            self.assertEqual(proc.returncode, 0, proc.stderr)
            output = proc.stdout.lower()
            self.assertIn("platform path: macos docker desktop", output)
            self.assertLess(
                output.index("platform path: macos docker desktop"),
                output.index("[install] start: repo sync"),
            )

    def test_install_stops_before_clone_when_docker_is_unavailable(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            env, target, _ = self.prepare_env(tmp)
            env["STUB_DOCKER_VERSION_FAIL"] = "1"

            proc = self.run_install(env)

            self.assertNotEqual(proc.returncode, 0)
            combined = (proc.stdout + proc.stderr).lower()
            self.assertIn("docker cli is unavailable", combined)
            self.assertNotIn("[install] start: repo sync", combined)
            self.assertFalse(target.exists())

    def test_install_stops_before_clone_when_compose_is_missing(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            env, target, _ = self.prepare_env(tmp)
            env["STUB_DOCKER_COMPOSE_FAIL"] = "1"

            proc = self.run_install(env)

            self.assertNotEqual(proc.returncode, 0)
            combined = (proc.stdout + proc.stderr).lower()
            self.assertIn("docker compose is required", combined)
            self.assertNotIn("[install] start: repo sync", combined)
            self.assertFalse(target.exists())

    def test_install_stops_before_clone_when_docker_desktop_is_not_running(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            env, target, _ = self.prepare_env(tmp)
            env["SMARTHUB_TEST_UNAME"] = "Darwin"
            env["STUB_DOCKER_INFO_FAIL"] = "1"

            proc = self.run_install(env)

            self.assertNotEqual(proc.returncode, 0)
            combined = (proc.stdout + proc.stderr).lower()
            self.assertIn("docker desktop is not running", combined)
            self.assertNotIn("[install] start: repo sync", combined)
            self.assertFalse(target.exists())

    def test_install_uses_cross_platform_env_update_helpers(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            env, target, _ = self.prepare_env(tmp)
            env["SMARTHUB_TEST_UNAME"] = "Darwin"
            env["SMARTHUB_TEST_BUSY_PORTS"] = "8123"

            proc = self.run_install(env)

            self.assertEqual(proc.returncode, 0, proc.stderr)
            env_text = (target / ".env").read_text()
            self.assertIn("HA_PORT=8124", env_text)
            self.assertIn("HA_URL=http://localhost:8124", env_text)

    def test_install_selects_macos_host_port_without_linux_only_tools(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            env, target, _ = self.prepare_env(tmp)
            env["SMARTHUB_TEST_UNAME"] = "Darwin"
            env["SMARTHUB_TEST_BUSY_PORTS"] = "8123"

            proc = self.run_install(env)

            self.assertEqual(proc.returncode, 0, proc.stderr)
            config_path = target / "ha-config" / "configuration.yaml"
            if config_path.exists():
                self.assertNotIn("server_port: 8124", config_path.read_text())
            self.assertIn("using published host port 8124", proc.stdout.lower())

    def test_install_keeps_linux_port_recovery_path_intact(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            env, target, _ = self.prepare_env(tmp)
            env["SMARTHUB_TEST_UNAME"] = "Linux"
            env["SMARTHUB_TEST_BUSY_PORTS"] = "8123"

            proc = self.run_install(env)

            self.assertEqual(proc.returncode, 0, proc.stderr)
            env_text = (target / ".env").read_text()
            self.assertIn("HA_PORT=8124", env_text)
            self.assertIn("HA_URL=http://localhost:8124", env_text)
            config_text = (target / "ha-config" / "configuration.yaml").read_text()
            self.assertIn("server_port: 8124", config_text)

    def test_install_emits_macos_fallback_guidance_for_out_of_scope_requirements(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            env, _, _ = self.prepare_env(tmp)
            env["SMARTHUB_TEST_UNAME"] = "Darwin"

            proc = self.run_install(env)

            self.assertEqual(proc.returncode, 0, proc.stderr)
            output = proc.stdout.lower()
            self.assertIn("linux vm + smarthub", output)
            self.assertIn("home assistant os in a vm", output)
            self.assertIn("gui steps still require user action", output)

    def test_standalone_install_skips_openclaw_requirements_and_targets_downloads(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            env, workspace_target, _ = self.prepare_env(tmp)
            env["SMARTHUB_STANDALONE"] = "1"
            config_path = Path(env["HOME"]) / ".openclaw" / "openclaw.json"
            config_path.unlink()
            standalone_target = Path(env["HOME"]) / "Downloads" / "smarthome-openclaw"

            proc = self.run_install(env)

            self.assertEqual(proc.returncode, 0, proc.stderr)
            self.assertFalse(workspace_target.exists())
            self.assertTrue(standalone_target.exists())
            self.assertTrue((standalone_target / ".env").exists())
            output = proc.stdout.lower()
            self.assertNotIn("openclaw config not found", output)
            self.assertNotIn("[install] start: patch openclaw config", output)
            self.assertNotIn("patching openclaw.json", output)

    def test_default_install_still_requires_openclaw_config(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            env, target, _ = self.prepare_env(tmp)
            config_path = Path(env["HOME"]) / ".openclaw" / "openclaw.json"
            config_path.unlink()

            proc = self.run_install(env)

            self.assertNotEqual(proc.returncode, 0)
            combined = (proc.stdout + proc.stderr).lower()
            self.assertIn("openclaw config not found", combined)
            self.assertFalse(target.exists())


if __name__ == "__main__":
    unittest.main()
