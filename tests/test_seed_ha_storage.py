import base64
import json
import os
import stat
import subprocess
import tempfile
import unittest
from pathlib import Path

import bcrypt
import jwt


REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPT = REPO_ROOT / "scripts" / "seed-ha-storage.py"
REQUIRED_STORAGE_FILES = (
    "auth",
    "auth_provider.homeassistant",
    "onboarding",
    "core.config",
)


class SeedHaStorageTests(unittest.TestCase):
    maxDiff = None

    def run_seed(
        self,
        config_dir: Path,
        *extra_args: str,
        expect_success: bool = True,
    ) -> subprocess.CompletedProcess[str]:
        proc = subprocess.run(
            [
                "python3",
                str(SCRIPT),
                "--config-dir",
                str(config_dir),
                "--time-zone",
                "Asia/Singapore",
                "--ha-version",
                "2026.3.4",
                *extra_args,
            ],
            capture_output=True,
            text=True,
        )
        if expect_success and proc.returncode != 0:
            self.fail(proc.stderr or proc.stdout)
        if not expect_success and proc.returncode == 0:
            self.fail(f"expected failure but got success: {proc.stdout}")
        return proc

    def test_fresh_seed_writes_expected_files_and_secret_output(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            config_dir = Path(tmp)
            proc = self.run_seed(config_dir)
            result = json.loads(proc.stdout)

            self.assertTrue(result["created"])
            self.assertEqual(result["username"], "openclaw")
            self.assertEqual(result["name"], "OpenClaw")
            self.assertIn("password", result)
            self.assertIn("token", result)
            self.assertEqual(sorted(result["storage_files"]), sorted(REQUIRED_STORAGE_FILES))

            storage = config_dir / ".storage"
            for name in REQUIRED_STORAGE_FILES:
                path = storage / name
                self.assertTrue(path.exists(), name)
                mode = stat.S_IMODE(os.stat(path).st_mode)
                self.assertEqual(mode, 0o600, name)

            auth = json.loads((storage / "auth").read_text())
            auth_provider = json.loads((storage / "auth_provider.homeassistant").read_text())
            onboarding = json.loads((storage / "onboarding").read_text())
            core_config = json.loads((storage / "core.config").read_text())

            self.assertEqual(auth["key"], "auth")
            self.assertEqual(auth["version"], 1)
            self.assertEqual(auth["minor_version"], 1)

            self.assertEqual(
                onboarding["data"]["done"],
                ["user", "core_config", "analytics", "integration"],
            )

            self.assertEqual(core_config["key"], "core.config")
            self.assertEqual(core_config["data"]["time_zone"], "Asia/Singapore")
            self.assertEqual(core_config["data"]["location_name"], "Home")
            self.assertEqual(core_config["data"]["unit_system_v2"], "metric")

            auth_user = auth_provider["data"]["users"][0]
            self.assertEqual(auth_user["username"], "openclaw")
            password_hash = base64.b64decode(auth_user["password"])
            self.assertTrue(bcrypt.checkpw(result["password"].encode(), password_hash))

            users = {user["name"]: user for user in auth["data"]["users"]}
            self.assertIn("Home Assistant Content", users)
            self.assertIn("OpenClaw", users)
            self.assertTrue(users["OpenClaw"]["is_owner"])
            self.assertEqual(users["OpenClaw"]["group_ids"], ["system-admin"])

            credentials = auth["data"]["credentials"]
            self.assertEqual(len(credentials), 1)
            self.assertEqual(credentials[0]["data"]["username"], "openclaw")

            refresh_tokens = auth["data"]["refresh_tokens"]
            long_lived = [
                token
                for token in refresh_tokens
                if token["token_type"] == "long_lived_access_token"
            ]
            self.assertEqual(len(long_lived), 1)
            self.assertEqual(long_lived[0]["client_name"], "openclaw")
            self.assertEqual(long_lived[0]["version"], "2026.3.4")

    def test_second_run_is_idempotent_and_token_matches_refresh_token(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            config_dir = Path(tmp)
            first = json.loads(self.run_seed(config_dir).stdout)
            second = json.loads(self.run_seed(config_dir).stdout)

            self.assertFalse(second["created"])
            self.assertEqual(second["username"], "openclaw")
            self.assertNotIn("password", second)
            self.assertNotIn("token", second)

            auth = json.loads((config_dir / ".storage" / "auth").read_text())
            refresh_token = next(
                token
                for token in auth["data"]["refresh_tokens"]
                if token["token_type"] == "long_lived_access_token"
            )

            payload = jwt.decode(
                first["token"],
                refresh_token["jwt_key"],
                algorithms=["HS256"],
                options={"verify_aud": False},
            )
            self.assertEqual(payload["iss"], refresh_token["id"])
            self.assertGreater(payload["exp"], payload["iat"])
            self.assertGreaterEqual(payload["exp"] - payload["iat"], 315360000 - 5)

    def test_partial_existing_state_fails_without_touching_existing_file(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            config_dir = Path(tmp)
            storage = config_dir / ".storage"
            storage.mkdir(parents=True)
            auth_path = storage / "auth"
            auth_path.write_text('{"existing": true}\n')
            auth_path.chmod(0o600)

            proc = self.run_seed(config_dir, expect_success=False)

            payload_text = proc.stderr or proc.stdout
            try:
                payload = json.loads(payload_text)
            except json.JSONDecodeError as exc:  # noqa: PERF203
                self.fail(f"expected machine-readable JSON failure output, got: {payload_text!r}")
            self.assertEqual(payload["status"], "partial")
            self.assertEqual(payload["storage_files"], ["auth"])
            self.assertIn("partial Home Assistant auth state", payload["message"])
            self.assertEqual(auth_path.read_text(), '{"existing": true}\n')


if __name__ == "__main__":
    unittest.main()
