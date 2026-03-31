# SmartHub Setup Guide

You are walking a new user through setting up SmartHub from scratch. They already have OpenClaw running and connected to their messaging platform — otherwise they wouldn't be talking to you.

**This skill is triggered when the user asks for help setting up Home Assistant / SmartHub.** Do NOT run this automatically — only when the user explicitly asks for setup help.

Follow each step in order. **Do not skip ahead.** Wait for the user's confirmation before moving to the next step.

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

## Step 2: Check Docker

```bash
docker --version
```

- If Docker is installed → move to Step 3
- If not installed → tell the user:

> Docker is not installed. Run this to install it:
> ```
> curl -fsSL https://get.docker.com | sh
> sudo usermod -aG docker $USER
> ```
> Then log out and back in (or restart your terminal) so the group change takes effect.
> Let me know when Docker is ready.

Wait for confirmation, then verify again with `docker --version`.

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

The token will be filled in later (Step 6). For now, `.env` just needs to exist so Docker Compose can read it.

---

## Step 3b: Check for Port Conflicts

Before starting Docker, check if the required ports are already in use:

```bash
# Check port 8123 (Home Assistant)
ss -tlnp | grep ':8123 ' && echo "PORT_8123_CONFLICT" || echo "PORT_8123_FREE"

# Check the API port from .env (default 3001)
API_PORT=$(grep API_PORT .env | cut -d= -f2)
API_PORT=${API_PORT:-3001}
ss -tlnp | grep ":${API_PORT} " && echo "PORT_${API_PORT}_CONFLICT" || echo "PORT_${API_PORT}_FREE"
```

**If port 8123 is in use:**
- Tell the user: "Port 8123 is already in use by another service. You'll need to stop it first."
- Help them identify what's using it: `ss -tlnp | grep ':8123 '`
- Do NOT proceed until 8123 is free — HA requires this port.

**If the API port is in use:**
- Pick the next available port automatically:
```bash
# Find a free port starting from 3001
for port in 3001 3002 3099 3100 3200; do
  ss -tlnp | grep -q ":${port} " || { echo "$port"; break; }
done
```
- Update `.env` with the free port:
```bash
sed -i "s|API_PORT=.*|API_PORT=<free_port>|" .env
```
- Tell the user: "Port <original> was in use, so I've set the API to run on port <free_port> instead."
- **Important:** If you assigned a non-default port, update all functional skill files that reference the API port. Run `grep -rn 'localhost:3001' tools/ CLAUDE.md TOOLS.md` and replace any remaining `localhost:3001` with `localhost:${API_PORT}` using the port you just assigned.

---

## Step 4: Start Home Assistant

```bash
docker compose up -d
```

Wait for HA to boot (usually 30-60 seconds on first run):

```bash
# Poll until HA responds
for i in $(seq 1 30); do
  curl -s http://localhost:8123/api/ 2>/dev/null && break
  sleep 2
done
```

- If HA responds with `{"message": "API running."}` → move to Step 5
- If it doesn't respond after 60 seconds → check logs:
  ```bash
  docker logs homeassistant --tail 50
  ```
  Help the user troubleshoot based on the log output.

---

## Step 5: HA Onboarding (User Does This in Browser)

First, get the Pi's IP address so the user can open HA in their browser:

```bash
hostname -I | awk '{print $1}'
```

Tell the user, using the IP you just obtained:

> Home Assistant is running! Open this in your browser:
> **http://<PI_IP>:8123**
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
# Read current .env, replace the HA_TOKEN line
sed -i "s|HA_TOKEN=.*|HA_TOKEN=<PASTE_TOKEN_HERE>|" .env
```

Replace `<PASTE_TOKEN_HERE>` with the actual token the user provided.

---

## Step 8: Restart the API

The API container needs to pick up the new token:

```bash
docker compose restart api
```

Wait a few seconds, then verify:

```bash
API_PORT=$(grep API_PORT .env | cut -d= -f2)
curl -s http://localhost:${API_PORT}/api/health
```

Should return `{"status":"ok","ha_connected":true}`.

---

## Step 9: Verify Connection

Test that the full pipeline works:

```bash
API_PORT=$(grep API_PORT .env | cut -d= -f2)
curl -s http://localhost:${API_PORT}/api/devices
```

Tell the user what you find:

- If devices are returned → "Connected! I found X devices."
- If `{"devices":[],"count":0}` → "Connected, but no devices yet. We can add integrations next."
- If an error → troubleshoot based on the error message.

---

## Step 10: Offer Next Steps

Setup is complete. Ask the user:

> SmartHub is ready! Here's what we can do next:
>
> 1. **Set up remote access** — I can create a public URL so you can access HA from anywhere
> 2. **Add device integrations** — connect your Xiaomi, Philips Hue, Broadlink, or other smart devices
> 3. **Just start using it** — ask me to control devices, check status, or create automations
>
> What would you like to do?

---

## Troubleshooting

### HA won't start
```bash
docker logs homeassistant --tail 100
```
Common issues:
- Port 8123 already in use → another HA instance or service is running
- Permission errors on ha-config/ → `sudo chown -R $USER:$USER ha-config/`

### API can't connect to HA
- Check `.env` has the correct token (no quotes, no extra spaces)
- Check HA is running: `docker ps`
- Check HA is accessible: `curl -s http://localhost:8123/api/ -H "Authorization: Bearer <token>"`

### Token rejected (401)
- The token was copied incorrectly — have the user create a new one
- The token might have expired — create a new long-lived token in HA

### Docker Compose fails
- Check Docker is running: `docker info`
- Check docker-compose.yml exists in the current directory
- Try: `docker compose down && docker compose up -d`
