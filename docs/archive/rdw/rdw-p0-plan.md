# SmartHub P0 No-Browser Install Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make fresh SmartHub installs create a usable Home Assistant admin account and API token offline, with a pinned HA image and one-shot credential handoff, while keeping approval-gate behavior and secret handling intact.

**Architecture:** Add a focused Python seeding helper that writes the four private HA storage files only on a fresh config, generate the long-lived access token offline in the same auth format HA 2026.3.4 expects, and have `install.sh` capture the helper output to update `.env` without ever printing the token. Keep the runtime path safe by making reruns idempotent, failing on partial auth state, pinning the HA image, and updating the installer's handoff instructions so the agent skips the old browser/token steps. Because a fresh machine cannot be assumed to have `bcrypt` installed globally, the installer should invoke the helper via `uv run --with bcrypt` after `uv` is installed.

**Tech Stack:** Bash, Python 3.13, `uv`, `bcrypt`, stdlib JSON/base64/hmac/hashlib, Docker, `unittest`

---

## File Structure

- Create: `scripts/seed-ha-storage.py`
  Generates the seeded HA private storage files plus machine-readable installer output for fresh installs only.
- Create: `tests/test_seed_ha_storage.py`
  Unit tests for file contents, secret handling, JWT shape, file modes, and idempotency.
- Create: `tests/test_install_sh.py`
  End-to-end installer smoke test with stubbed external commands, verifying `.env` population and one-shot credential behavior.
- Modify: `install.sh`
  Runs the seeding helper before HA boot, writes the generated LLAT into `.env`, avoids printing the token, and skips the old browser/token setup steps on fresh installs.
- Modify: `docker-compose.yml`
  Pin HA to `ghcr.io/home-assistant/home-assistant:2026.3.4`.

## Phase 1: Build the HA Storage Seeder

### Task 1: Seed helper writes valid fresh-storage files

**Files:**
- Create: `tests/test_seed_ha_storage.py`
- Create: `scripts/seed-ha-storage.py`

- [ ] **Step 1: Write the failing fresh-seed test**

```python
import base64
import json
import os
import stat
import subprocess
import tempfile
import unittest
from pathlib import Path


SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "seed-ha-storage.py"


class SeedHaStorageTests(unittest.TestCase):
    def run_seed(self, config_dir: Path) -> dict:
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
            ],
            capture_output=True,
            text=True,
            check=True,
        )
        return json.loads(proc.stdout)

    def test_fresh_seed_writes_expected_files_and_secret_output(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            config_dir = Path(tmp)
            result = self.run_seed(config_dir)

            self.assertTrue(result["created"])
            self.assertEqual(result["username"], "openclaw")
            self.assertIn("password", result)
            self.assertIn("token", result)

            storage = config_dir / ".storage"
            auth = json.loads((storage / "auth").read_text())
            auth_provider = json.loads(
                (storage / "auth_provider.homeassistant").read_text()
            )
            onboarding = json.loads((storage / "onboarding").read_text())
            core_config = json.loads((storage / "core.config").read_text())

            self.assertEqual(auth["key"], "auth")
            self.assertEqual(onboarding["data"]["done"], ["user", "core_config", "analytics", "integration"])
            self.assertEqual(core_config["data"]["time_zone"], "Asia/Singapore")

            password_b64 = auth_provider["data"]["users"][0]["password"]
            hashed = base64.b64decode(password_b64)
            self.assertTrue(hashed.startswith(b"$2"))

            for name in ("auth", "auth_provider.homeassistant", "onboarding", "core.config"):
                mode = stat.S_IMODE(os.stat(storage / name).st_mode)
                self.assertEqual(mode, 0o600)
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python3 -m unittest tests.test_seed_ha_storage.SeedHaStorageTests.test_fresh_seed_writes_expected_files_and_secret_output -v`
Expected: FAIL because `scripts/seed-ha-storage.py` does not exist yet.

- [ ] **Step 3: Write minimal seeding implementation**

```python
#!/usr/bin/env python3
from __future__ import annotations

import argparse
import base64
import json
import secrets
import stat
from pathlib import Path

import bcrypt


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config-dir", required=True)
    parser.add_argument("--time-zone", default="UTC")
    parser.add_argument("--ha-version", default="2026.3.4")
    args = parser.parse_args()

    config_dir = Path(args.config_dir)
    storage_dir = config_dir / ".storage"
    storage_dir.mkdir(parents=True, exist_ok=True)

    password = secrets.token_urlsafe(18)
    password_hash = base64.b64encode(
        bcrypt.hashpw(password.encode(), bcrypt.gensalt(rounds=12))
    ).decode()

    storage_files = {
        "auth_provider.homeassistant": {
            "version": 1,
            "minor_version": 1,
            "key": "auth_provider.homeassistant",
            "data": {"users": [{"username": "openclaw", "password": password_hash}]},
        },
        "onboarding": {
            "version": 4,
            "minor_version": 1,
            "key": "onboarding",
            "data": {"done": ["user", "core_config", "analytics", "integration"]},
        },
        "core.config": {
            "version": 1,
            "minor_version": 4,
            "key": "core.config",
            "data": {
                "latitude": 0.0,
                "longitude": 0.0,
                "elevation": 0,
                "unit_system_v2": "metric",
                "location_name": "Home",
                "time_zone": args.time_zone,
                "external_url": None,
                "internal_url": None,
                "currency": "USD",
                "country": "US",
                "language": "en",
                "radius": 100,
            },
        },
    }

    for name, payload in storage_files.items():
        path = storage_dir / name
        path.write_text(json.dumps(payload, indent=2) + "\n")
        path.chmod(stat.S_IRUSR | stat.S_IWUSR)

    token = secrets.token_urlsafe(48)
    print(json.dumps({"created": True, "username": "openclaw", "password": password, "token": token}))


if __name__ == "__main__":
    main()
```

- [ ] **Step 4: Run test to verify it passes**

Run: `python3 -m unittest tests.test_seed_ha_storage.SeedHaStorageTests.test_fresh_seed_writes_expected_files_and_secret_output -v`
Expected: PASS

### Task 2: Seeder is idempotent and emits a valid long-lived token shape

**Files:**
- Modify: `tests/test_seed_ha_storage.py`
- Modify: `scripts/seed-ha-storage.py`

- [ ] **Step 1: Write the failing idempotency/JWT test**

```python
import base64
import json
import jwt

    def test_second_run_is_idempotent_and_token_matches_refresh_token(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            config_dir = Path(tmp)
            first = self.run_seed(config_dir)
            second = self.run_seed(config_dir)

            self.assertFalse(second["created"])
            self.assertNotIn("password", second)
            self.assertNotIn("token", second)

            auth = json.loads((config_dir / ".storage" / "auth").read_text())
            admin_refresh = next(
                token
                for token in auth["data"]["refresh_tokens"]
                if token["token_type"] == "long_lived_access_token"
            )

            payload = jwt.decode(
                first["token"],
                admin_refresh["jwt_key"],
                algorithms=["HS256"],
                options={"verify_aud": False},
            )
            self.assertEqual(payload["iss"], admin_refresh["id"])
            self.assertGreater(payload["exp"], payload["iat"])
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python3 -m unittest tests.test_seed_ha_storage.SeedHaStorageTests.test_second_run_is_idempotent_and_token_matches_refresh_token -v`
Expected: FAIL because the helper either rotates secrets or does not emit the expected JWT claims yet.

- [ ] **Step 3: Implement idempotency and JWT generation**

```python
import hmac
import hashlib
import time
from dataclasses import dataclass
from base64 import urlsafe_b64encode


def encode_jwt(refresh_token_id: str, jwt_key: str, issued_at: int, expires_at: int) -> str:
    header = urlsafe_b64encode(json.dumps({"alg": "HS256", "typ": "JWT"}).encode()).rstrip(b"=")
    payload = urlsafe_b64encode(
        json.dumps({"iss": refresh_token_id, "iat": issued_at, "exp": expires_at}).encode()
    ).rstrip(b"=")
    signing_input = header + b"." + payload
    signature = urlsafe_b64encode(
        hmac.new(jwt_key.encode(), signing_input, hashlib.sha256).digest()
    ).rstrip(b"=")
    return b".".join((header, payload, signature)).decode()


@dataclass
class SeedResult:
    created: bool
    username: str
    password: str | None = None
    token: str | None = None


def seed_auth_storage(config_dir: Path, time_zone: str, ha_version: str) -> SeedResult:
    required_files = [
        config_dir / ".storage" / name
        for name in ("auth", "auth_provider.homeassistant", "onboarding", "core.config")
    ]
    if all(path.exists() for path in required_files):
        return SeedResult(created=False, username="openclaw")
    if any(path.exists() for path in required_files):
        raise RuntimeError("refusing to seed partial Home Assistant auth state")

    issued_at = int(time.time())
    expires_at = issued_at + 315360000
    password = secrets.token_urlsafe(18)
    created_at_iso = time.strftime("%Y-%m-%dT%H:%M:%S+00:00", time.gmtime(issued_at))
    system_user_id = secrets.token_hex(16)
    admin_user_id = secrets.token_hex(16)
    credential_id = secrets.token_hex(16)
    system_refresh_id = secrets.token_hex(16)
    refresh_token_id = secrets.token_hex(16)
    jwt_key = secrets.token_hex(64)
    long_lived_token = encode_jwt(refresh_token_id, jwt_key, issued_at, expires_at)
    auth_payload = {
        "version": 1,
        "minor_version": 1,
        "key": "auth",
        "data": {
            "users": [
                {
                    "id": system_user_id,
                    "group_ids": ["system-read-only"],
                    "is_owner": False,
                    "is_active": True,
                    "name": "Home Assistant Content",
                    "system_generated": True,
                    "local_only": False,
                },
                {
                    "id": admin_user_id,
                    "group_ids": ["system-admin"],
                    "is_owner": True,
                    "is_active": True,
                    "name": "OpenClaw",
                    "system_generated": False,
                    "local_only": False,
                },
            ],
            "groups": [
                {"id": "system-admin", "name": "Administrators"},
                {"id": "system-users", "name": "Users"},
                {"id": "system-read-only", "name": "Read Only"},
            ],
            "credentials": [
                {
                    "id": credential_id,
                    "user_id": admin_user_id,
                    "auth_provider_type": "homeassistant",
                    "auth_provider_id": None,
                    "data": {"username": "openclaw"},
                }
            ],
            "refresh_tokens": [
                {
                    "id": system_refresh_id,
                    "user_id": system_user_id,
                    "client_id": None,
                    "client_name": None,
                    "client_icon": None,
                    "token_type": "system",
                    "created_at": created_at_iso,
                    "access_token_expiration": 1800.0,
                    "token": secrets.token_hex(64),
                    "jwt_key": secrets.token_hex(64),
                    "last_used_at": None,
                    "last_used_ip": None,
                    "expire_at": None,
                    "credential_id": None,
                    "version": ha_version,
                },
                {
                    "id": refresh_token_id,
                    "user_id": admin_user_id,
                    "client_id": None,
                    "client_name": "openclaw",
                    "client_icon": None,
                    "token_type": "long_lived_access_token",
                    "created_at": created_at_iso,
                    "access_token_expiration": 315360000.0,
                    "token": secrets.token_hex(64),
                    "jwt_key": jwt_key,
                    "last_used_at": None,
                    "last_used_ip": None,
                    "expire_at": None,
                    "credential_id": None,
                    "version": ha_version,
                }
            ],
        },
    }
    return SeedResult(created=True, username="openclaw", password=password, token=long_lived_token)
```

- [ ] **Step 4: Run the seed-helper test module**

Run: `python3 -m unittest tests.test_seed_ha_storage -v`
Expected: PASS

## Phase 2: Integrate the Seeder into the Installer

### Task 3: Pin the HA image and teach install.sh to seed `.env` safely

**Files:**
- Modify: `docker-compose.yml`
- Modify: `install.sh`

- [ ] **Step 1: Write the failing installer smoke test**

```python
import json
import os
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
INSTALL_SH = REPO_ROOT / "install.sh"


class InstallScriptTests(unittest.TestCase):
    def test_install_seeds_token_and_prints_password_once(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            home = Path(tmp) / "home"
            workspace = home / ".openclaw" / "workspace"
            config = home / ".openclaw" / "openclaw.json"
            stub_bin = Path(tmp) / "bin"
            repo_copy = Path(tmp) / "fixture-repo"

            workspace.mkdir(parents=True)
            config.parent.mkdir(parents=True)
            shutil.copytree(REPO_ROOT, repo_copy, dirs_exist_ok=True)
            config.write_text(json.dumps({"agents": {"defaults": {"workspace": str(workspace)}}}))

            stub_bin.mkdir()
            (stub_bin / "git").write_text(
                "#!/usr/bin/env bash\n"
                "if [ \"$1\" = clone ]; then cp -a \"$FIXTURE_REPO\" \"$3\"; exit 0; fi\n"
                "if [ \"$1\" = pull ]; then exit 0; fi\n"
                "exit 0\n"
            )
            (stub_bin / "curl").write_text("#!/usr/bin/env bash\nprintf '#!/bin/sh\\nexit 0\\n'\n")
            (stub_bin / "uv").write_text(
                "#!/usr/bin/env bash\n"
                "script=${@: -1}\n"
                "python3 \"$script\" \"${@:1:$#-1}\"\n"
            )
            (stub_bin / "uvx").write_text("#!/usr/bin/env bash\nexit 0\n")
            (stub_bin / "ss").write_text("#!/usr/bin/env bash\nexit 1\n")
            for name in ("git", "curl", "uv", "uvx", "ss"):
                os.chmod(stub_bin / name, 0o755)

            env = os.environ | {
                "HOME": str(home),
                "PATH": f"{stub_bin}:{os.environ['PATH']}",
                "OPENCLAW_WORKSPACE": str(workspace),
                "FIXTURE_REPO": str(repo_copy),
            }
            proc = subprocess.run(
                ["bash", str(INSTALL_SH)],
                capture_output=True,
                text=True,
                env=env,
            )

            self.assertEqual(proc.returncode, 0, proc.stderr)
            self.assertIn("save this, it's the only time you'll see it", proc.stdout.lower())
            self.assertNotIn("HA_TOKEN=", proc.stdout)
            seeded_env = (workspace / "smarthome-openclaw" / ".env").read_text()
            self.assertNotIn("your_long_lived_access_token_here", seeded_env)
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python3 -m unittest tests.test_install_sh.InstallScriptTests.test_install_seeds_token_and_prints_password_once -v`
Expected: FAIL because `install.sh` does not seed storage or `.env` yet.

- [ ] **Step 3: Implement the installer wiring**

```bash
HA_VERSION="2026.3.4"
SEED_JSON="$(uv run --with bcrypt "$TARGET/scripts/seed-ha-storage.py" \
  --config-dir "$TARGET/ha-config" \
  --time-zone "${TZ_VALUE}" \
  --ha-version "$HA_VERSION")"

SEED_JSON="$SEED_JSON" python3 - <<'PY'
import json
import os
from pathlib import Path

seed = json.loads(os.environ["SEED_JSON"])
env_path = Path(".env")
lines = env_path.read_text().splitlines()
if seed["created"]:
    env_path.write_text(
        "\n".join(
            f"HA_TOKEN={seed['token']}" if line.startswith("HA_TOKEN=") else line
            for line in lines
        )
        + "\n"
    )
PY

SEED_CREATED="$(SEED_JSON="$SEED_JSON" python3 - <<'PY'
import json, os
seed = json.loads(os.environ["SEED_JSON"])
print("1" if seed["created"] else "0")
PY
)"

if [ "$SEED_CREATED" = "1" ]; then
  SEED_USERNAME="$(SEED_JSON="$SEED_JSON" python3 - <<'PY'
import json, os
seed = json.loads(os.environ["SEED_JSON"])
print(seed["username"])
PY
)"
  SEED_PASSWORD="$(SEED_JSON="$SEED_JSON" python3 - <<'PY'
import json, os
seed = json.loads(os.environ["SEED_JSON"])
print(seed["password"])
PY
)"
  echo "Home Assistant admin username: $SEED_USERNAME"
  echo "Home Assistant admin password: $SEED_PASSWORD"
  echo "Save this, it's the only time you'll see it."
fi
```

- [ ] **Step 4: Pin the compose image**

```yaml
services:
  homeassistant:
    image: "ghcr.io/home-assistant/home-assistant:2026.3.4"
```

- [ ] **Step 5: Run installer/unit verification**

Run: `python3 -m unittest tests.test_install_sh -v`
Expected: PASS

Run: `bash -n install.sh`
Expected: exit 0

### Task 4: Ensure the installer skips the old browser/token steps after seeding

**Files:**
- Modify: `install.sh`
- Modify: `tests/test_install_sh.py`

- [ ] **Step 1: Write the failing instruction-path assertion**

```python
            self.assertIn("Start from Step 2.", proc.stdout)
            self.assertIn("skip Steps 3, 5, 6, and 7", proc.stdout)
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python3 -m unittest tests.test_install_sh.InstallScriptTests.test_install_seeds_token_and_prints_password_once -v`
Expected: FAIL because the installer still tells the agent to follow the old browser/token path.

- [ ] **Step 3: Update the handoff instructions**

```bash
echo "Then immediately read ${TARGET}/tools/setup.md and begin executing"
echo "the setup steps from that directory. Start from Step 2."
echo "Port conflicts and .env are already resolved — skip Steps 3, 5, 6, and 7."
```

- [ ] **Step 4: Re-run installer verification**

Run: `python3 -m unittest tests.test_install_sh -v`
Expected: PASS

## Phase 3: Validate Against a Real HA Container

### Task 5: Prove the seeded token works against HA 2026.3.4

**Files:**
- No new repo files required unless a small temp harness script becomes necessary

- [ ] **Step 1: Seed a fresh temp config and capture credentials**

Run:

```bash
tmpdir="$(mktemp -d)"
python3 scripts/seed-ha-storage.py --config-dir "$tmpdir" --time-zone Asia/Singapore --ha-version 2026.3.4 > "$tmpdir/seed.json"
```

Expected: `seed.json` contains `created: true`, `username`, `password`, and `token`.

- [ ] **Step 2: Boot pinned HA with the seeded config**

Run:

```bash
docker run -d --rm \
  --name rdw-p0-ha \
  -p 18123:8123 \
  -v "$tmpdir:/config" \
  -e TZ=Asia/Singapore \
  ghcr.io/home-assistant/home-assistant:2026.3.4
```

Expected: container starts and reaches healthy HTTP responses within a few minutes.

- [ ] **Step 3: Verify onboarding is skipped and the seeded token authenticates**

Run:

```bash
token="$(python3 - "$tmpdir/seed.json" <<'PY'
import json, sys
print(json.load(open(sys.argv[1]))["token"])
PY
)"

curl -s http://127.0.0.1:18123/api/
curl -s http://127.0.0.1:18123/api/config -H "Authorization: Bearer $token"
```

Expected:
- First command returns `{"message":"API running."}` (or equivalent API-ready response)
- Second command returns config JSON, not `401 Unauthorized`

- [ ] **Step 4: Tear down and record the evidence**

Run:

```bash
docker rm -f rdw-p0-ha
rm -rf "$tmpdir"
```

Expected: clean teardown

## Cross-Reference Review Checklist

- P1 maps to Phase 1 Task 1/2, Phase 2 Task 3/4, and Phase 3 Task 5.
- P2 maps to Phase 2 Task 3 Step 4 and Phase 3 Task 5.
- P3 maps to Phase 1 Task 1/2 and Phase 2 Task 3.
- P4 maps to Phase 2 Task 3/4 and installer smoke verification.

## Verification Commands

- `python3 -m unittest tests.test_seed_ha_storage -v`
- `python3 -m unittest tests.test_install_sh -v`
- `bash -n install.sh`
- Real-container validation commands from Phase 3 Task 5
