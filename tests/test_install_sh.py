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
