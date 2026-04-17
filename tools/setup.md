# SmartHub Setup Guide

You are walking a new user through setting up SmartHub from scratch. They already have OpenClaw running and connected to their messaging platform — otherwise they wouldn't be talking to you.

This workflow has two entrypoints:
- the user explicitly asks for help setting up Home Assistant / SmartHub
- `install.sh` just finished, so this doc is the automatic continuation target after `install.sh`

When this doc is entered from `install.sh`, continue immediately from the first relevant step without waiting for another user nudge. Follow each step in order. **Do not skip ahead.** Only wait when a step explicitly tells you to wait for the user's confirmation.

Before telling the user setup is stuck, follow the recovery ladder in `tools/_errors.md`.

When `install.sh` hands off here, use setup.md to decide which steps are already satisfied. The installer may already have created `.env`, selected `HA_PORT`, and pre-seeded Home Assistant auth.

---

## Step 1: Get the Repo

First, check if the repo is already cloned:

```bash
ls docker-compose.yml 2>/dev/null && echo "REPO_EXISTS"
```

- If `REPO_EXISTS` → tell the user "I can see the SmartHub repo is already cloned. Let's continue with setup." Skip to Step 2.
- If not found → ask the user:

> I need the SmartHub repo to set up your smart home. Do you have a GitHub link?
> You can use the original: `https://github.com/caiwang0/smarthome-openclaw`
> Or if you've forked it, send me your fork URL.

Once you have the URL:

```bash
git clone <repo_url>
cd <repo_name>
```

---

## Step 2: Check Docker / Docker Desktop

```bash
. ./scripts/platform-env.sh
PLATFORM=$(smarthub_detect_platform)
docker --version
docker info >/dev/null && echo "DOCKER_READY"
```

- If Docker is installed and `DOCKER_READY` prints → move to Step 3
- If the current platform is `linux` and Docker is missing or not running → tell the user:

> Docker is not installed. Run this to install it:
> ```
> curl -fsSL https://get.docker.com | sh
> sudo usermod -aG docker $USER
> ```
> Then log out and back in (or restart your terminal) so the group change takes effect.
> Let me know when Docker is ready.

- If the current platform is `macos` and Docker is missing or `docker info` fails → tell the user:

> Docker Desktop is required for the native macOS path. Install it, open it, and wait until `docker info` succeeds.
>
> Native macOS support covers the mainstream SmartHub flow only. If you need USB radios, Bluetooth, or Linux-style low-level networking, use `Linux VM + SmartHub` or `Home Assistant OS in a VM` instead.
>
> OpenClaw can guide parts of that VM setup, but the hypervisor GUI steps still require user action. If you guide the official macOS VM fallback, match the Home Assistant docs: VirtualBox image for the correct Mac architecture (`Intel` vs `Apple Silicon`), at least `2 GB RAM`, `2 vCPUs`, `EFI` enabled, and the NIC switched from `NAT` to `Bridged Adapter`. Mention `UTM` only when VirtualBox is unsupported and the user is already comfortable with VMs.

Wait for confirmation, then verify again with the Step 2 command block.

---

## Step 3: Configure .env

Check if `.env` exists:

```bash
cat .env 2>/dev/null
```

If `.env` doesn't exist, create it from the example:

```bash
cp .env.example .env
```

The token will be filled in later (Step 6). If `install.sh` already ran, `.env` may already contain a real `HA_TOKEN` from the seeded bootstrap — keep it.

---

## Step 4: Start Home Assistant

```bash
. ./scripts/platform-env.sh

compose_args=()
for compose_file in $(smarthub_compose_files); do
  compose_args+=(-f "$compose_file")
done

docker compose "${compose_args[@]}" up -d
```

Wait for HA to boot (usually 30-60 seconds on first run):

```bash
. ./scripts/platform-env.sh

# Read the actual HA port and token from .env
HA_PORT=$(grep '^HA_PORT=' .env 2>/dev/null | cut -d= -f2)
HA_PORT=${HA_PORT:-8123}
HA_URL=$(grep HA_URL .env | cut -d= -f2)
HA_URL=${HA_URL:-http://localhost:${HA_PORT}}
HA_ORIGIN=$(smarthub_default_ha_origin)
HA_TOKEN=$(grep HA_TOKEN .env 2>/dev/null | cut -d= -f2)

# Poll until HA responds on its actual port.
# Seeded install path: auth is already enabled, so use /api/config with the token.
# Manual/onboarding path: token is still placeholder, so use unauthenticated /api.
for i in $(seq 1 30); do
  if [ -n "${HA_TOKEN}" ] && [ "${HA_TOKEN}" != "your_long_lived_access_token_here" ]; then
    curl -fsS ${HA_URL}/api/config \
      -H "Authorization: Bearer ${HA_TOKEN}" >/dev/null && break
  else
    curl -s ${HA_URL}/api/ 2>/dev/null | grep -q "API running" && break
  fi
  sleep 2
done
```

- If `.env` already contains a real token and `/api/config` returns `200` → run Step 4b, then skip to Step 8
- If HA responds with `{"message": "API running."}` in onboarding mode → run Step 4b, then move to Step 5
- If it doesn't respond after 60 seconds → check logs:
  ```bash
  docker compose logs homeassistant --tail 50
  ```
  Help the user troubleshoot based on the log output.

---

## Step 4b: Linux only — Set Up mDNS for homeassistant.local

> **Only run this after HA is confirmed running (Step 4 polling succeeded).** Run this on Linux/Raspberry Pi installs. Skip it on macOS Docker Desktop, where the supported native path uses the local browser origin from `smarthub_default_ha_origin`.

```bash
# Install avahi-utils if not already installed
which avahi-publish >/dev/null 2>&1 || sudo apt-get install -y avahi-utils
```

Create a systemd user service to broadcast `homeassistant.local`:

```bash
PI_IP=$(hostname -I | awk '{print $1}')

mkdir -p ~/.config/systemd/user

cat > ~/.config/systemd/user/homeassistant-mdns.service << EOF
[Unit]
Description=Broadcast homeassistant.local via mDNS
After=network.target avahi-daemon.service

[Service]
ExecStart=/usr/bin/avahi-publish-address -R homeassistant.local ${PI_IP}
Restart=on-failure
RestartSec=5

[Install]
WantedBy=default.target
EOF

systemctl --user daemon-reload
systemctl --user enable homeassistant-mdns
systemctl --user start homeassistant-mdns
```

Verify it's working:

```bash
avahi-resolve -n homeassistant.local
```

Should show the Pi's IP.

```bash
# Get the HA port for user-facing messages
HA_PORT=$(grep '^HA_PORT=' .env 2>/dev/null | cut -d= -f2)
HA_PORT=${HA_PORT:-8123}
```

Any device on the same network can now reach Home Assistant at `http://homeassistant.local:${HA_PORT}`.

> Do NOT tell the user about this step — just run it silently. It's infrastructure setup.

---

## Step 5: HA Onboarding (User Does This in Browser)

> **If `.env` already has a real `HA_TOKEN`, onboarding was pre-seeded by `install.sh`. Skip Steps 5, 6, and 7 and continue with Step 8.**

First, get the platform-aware HA origin and port:

```bash
. ./scripts/platform-env.sh
HA_PORT=$(grep '^HA_PORT=' .env 2>/dev/null | cut -d= -f2)
HA_PORT=${HA_PORT:-8123}
HA_ORIGIN=$(smarthub_default_ha_origin)
```

Tell the user, using the values you just obtained:

> Home Assistant is running! Open this in your browser:
> **<HA_ORIGIN>**
>
> You'll see the onboarding wizard. Follow these steps:
> 1. **Create your admin account** — pick a name, username, and password
> 2. **Set your home location** — you can skip this or set it roughly
> 3. **Select your country and timezone**
> 4. **Analytics** — you can opt out of everything
> 5. **Finish** — you'll land on the HA dashboard
>
> Let me know when you're done and tell me the **username** you chose.

Wait for the user to confirm. Note the username they give you — you'll need it for verification later.

---

## Step 6: Get Long-Lived Access Token (User Does This in Browser)

Tell the user:

> Now I need an access token so I can control your devices. In your browser:
>
> 1. Click your **user initial** (bottom-left corner of the HA dashboard)
> 2. Click the **Security** tab
> 3. Scroll all the way down to **Long-Lived Access Tokens**
> 4. Click **Create Token**
> 5. Name it **openclaw**
> 6. **Copy the token** — it only shows once!
> 7. **Paste it here** in the chat

Wait for the user to paste the token. It will look like: `eyJhbGciOiJIUzI1NiIs...`

---

## Step 7: Save Token to .env

Once you receive the token, write it to `.env`:

```bash
python3 - ".env" "<PASTE_TOKEN_HERE>" <<'PY'
import stat
import sys
import tempfile
from pathlib import Path

path = Path(sys.argv[1])
token = sys.argv[2]
existing_mode = stat.S_IMODE(path.stat().st_mode) if path.exists() else 0o600
lines = path.read_text().splitlines() if path.exists() else []

updated = []
replaced = False
for line in lines:
    if line.startswith("HA_TOKEN="):
        updated.append("HA_TOKEN=" + token)
        replaced = True
    else:
        updated.append(line)

if not replaced:
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
```

Replace `<PASTE_TOKEN_HERE>` with the actual token the user provided.

---

## Step 8: Verify ha-mcp Can Reach HA

ha-mcp is spawned on demand (no persistent service to restart). Verify it can connect:

```bash
. ./scripts/platform-env.sh
HA_PORT=$(grep '^HA_PORT=' .env 2>/dev/null | cut -d= -f2)
HA_PORT=${HA_PORT:-8123}
HOMEASSISTANT_TOKEN=$(grep HA_TOKEN .env | cut -d= -f2)
HOMEASSISTANT_URL=$(grep HA_URL .env | cut -d= -f2)
HOMEASSISTANT_URL=${HOMEASSISTANT_URL:-http://localhost:${HA_PORT}}
HOMEASSISTANT_TOKEN="$HOMEASSISTANT_TOKEN" \
HOMEASSISTANT_URL="$HOMEASSISTANT_URL" \
uvx ha-mcp@7.2.0 --smoke-test
```

Expected success: "Connected to Home Assistant at <URL>."
Expected failure: error message indicating which component failed.

**Smoke-test fallback:** If `--smoke-test` does not exist in v7.2.0, use:
```bash
uvx ha-mcp@7.2.0 --help >/dev/null 2>&1 && echo "MCP_INSTALLED" || echo "MCP_MISSING"
```
This only verifies ha-mcp is installed (not HA connectivity). HA connectivity is confirmed by Step 4 (HA API poll in Step 4 of setup.md).

---

## Step 9: Verify the first verified win

Capture a pre-connection baseline before you count any success. Use `ha_search_entities` to list the current device-backed, non-system entities, and record those entity IDs as the baseline:

```
Tool: ha_search_entities
  query: ""
```

Tell the user what you find:

- If there are zero device-backed, non-system entities → "Connected, but zero device-backed, non-system entities yet. hand off into discovery via `tools/integrations/_discovery.md`."
  Use the passive-first discovery entrypoint in `tools/integrations/_discovery.md`.
- The newly added entity must be a device-backed, non-system entity that was not in the baseline.
- Setup is only complete after discovery or integration setup adds one new non-system entity that is device-backed, and that device-backed, non-system entity was not in the baseline, and you can perform one verified read or control action on that newly added entity.
- If discovery or integration setup adds one new non-system entity that is device-backed, and that device-backed, non-system entity was not in the baseline, and you can perform one verified read or control action on that newly added entity → "First verified win: one new non-system entity connected and verified. Stop here."
- If the only entities you found were already in the baseline → do not count that as success. Hand off into discovery and wait for a newly added entity.
- If an error → check `tools/_errors.md` for troubleshooting.

Do not offer a generic next-steps menu here. The flow stops after the first verified win.

---

## Troubleshooting

### HA won't start
```bash
docker compose logs homeassistant --tail 100
```
Common issues:
- Port 8123 already in use → another HA instance or service is running
- Permission errors on ha-config/ → `sudo chown -R $USER:$USER ha-config/`

### API can't connect to HA
- Check `.env` has the correct token (no quotes, no extra spaces)
- Check HA is running: `docker ps`
- Check HA is accessible: `HA_URL=$(grep HA_URL .env | cut -d= -f2); curl -s ${HA_URL:-http://localhost:8123}/api/config -H "Authorization: Bearer <token>"`

### Token rejected (401)
- The token was copied incorrectly — have the user create a new one
- The token might have expired — create a new long-lived token in HA

### Docker Compose fails
- Check Docker is running: `docker info`
- Check docker-compose.yml exists in the current directory
- Try: `docker compose down && docker compose up -d`
- On macOS, make sure Docker Desktop is still open. If the user actually needs USB radios, Bluetooth, or Linux-style low-level networking, redirect them to `Linux VM + SmartHub` or `Home Assistant OS in a VM` instead. OpenClaw can guide parts of that VM setup, but the hypervisor GUI steps still require user action.
- A Mac-hosted VM only has local discovery and control while the Mac remains on the home LAN.
