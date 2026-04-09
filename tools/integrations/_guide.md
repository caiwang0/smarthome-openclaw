# Integrations — Setup Guide

Every integration has its own setup flow with different steps and options. **Do NOT hardcode or assume what the options are.**

### Step 0 — Check if the integration is available (MANDATORY)

**Before doing ANYTHING else**, check whether the integration domain is already installed in HA:

Use `ha_config_entries_get` to check if the integration domain is already installed:

```
Tool: ha_config_entries_get
```

Check if the target domain appears in the results. If not, the integration likely needs HACS.

**If NOT_AVAILABLE:**
1. The integration is probably a **custom integration** that requires HACS
2. Check if HACS is installed: use `ha_hacs_search` — if the tool is not available, HACS is not installed.
3. If HACS is missing, install it first (see HACS setup below)
4. If HACS is installed, install the custom integration through HACS, then restart HA
5. After restart, re-check that the integration domain is now available before starting the config flow

**IMPORTANT: The entire HACS + custom integration installation process is INFRASTRUCTURE — handle it silently.** Do NOT show the user HACS installation steps, GitHub authorization, or custom integration download. Just do it. The user only needs to interact when the actual integration config flow starts (e.g., choosing a cloud region, authorizing OAuth). Tell the user something brief like "Setting up the integration, one moment..." while you work.

**Known integrations that need HACS (NOT built-in):**

| User says | Integration domain | Notes |
|---|---|---|
| "Xiaomi Home" | `xiaomi_home` | Custom integration, OAuth-based. NOT the same as `xiaomi_miio` |

**Known built-in integrations (no HACS needed):**

| User says | Integration domain | Notes |
|---|---|---|
| "Xiaomi Miio" | `xiaomi_miio` | Built-in, cloud-based with username/password |
| "Philips Hue" | `hue` | Built-in, local discovery |
| "Google Home" / "Google Cast" | `cast` | Built-in |

**CRITICAL:** Do NOT substitute a different integration when the one the user asked for is not available. If the user says "Xiaomi Home" and `xiaomi_home` is not installed, do NOT offer `xiaomi_miio` instead — install `xiaomi_home` via HACS. If genuinely unsure which integration the user wants, ask them to clarify.

**When encountering an integration you don't recognize:** Always run the Step 0 check first. If it's NOT_AVAILABLE, tell the user it may need HACS and ask if they want to proceed with installation. Don't guess or assume — different integrations have different names and domains.

### HACS Setup (if needed) — DO THIS SILENTLY

**The entire HACS setup is infrastructure. Do NOT involve the user.** Handle everything yourself:

**Step 1: Install HACS into HA**
```bash
# HA config is often owned by root (Docker). Install via docker exec:
docker compose exec homeassistant bash -c 'wget -O /tmp/hacs-install.sh https://get.hacs.xyz && bash /tmp/hacs-install.sh'

# Restart HA to load HACS
```
Restart HA:
```
Tool: ha_call_service
  domain: "homeassistant"
  service: "restart"
```
Then wait for HA API to come back: `for i in $(seq 1 30); do curl -s ${HA_URL}/api/ 2>/dev/null && break; sleep 2; done`

**Step 2: Activate HACS (GitHub authorization) — handle silently**
Start the HACS config flow:
```
Tool: ha_config_entries_flow
  handler: "hacs"
```
HACS activation requires a GitHub device code flow. The config flow will return a step with a GitHub URL and a user code. **Complete this yourself:**
- Extract the GitHub device code URL and the code from the response
- Use the GitHub device flow to authorize (you have shell access — use `curl` to POST to `https://github.com/login/device/code` and `https://github.com/login/oauth/access_token`)
- If you cannot complete the GitHub flow programmatically, only then ask the user to open the link and enter the code — but try to handle it yourself first
- After authorization, submit the flow step to complete HACS activation

**Step 3: Install the custom integration via HACS**
```bash
# Find the HA config directory
HA_CONFIG="$(pwd)/ha-config"

# Download the integration directly (faster than HACS API)
# Example for xiaomi_home:
cd "${HA_CONFIG}/custom_components" 2>/dev/null || mkdir -p "${HA_CONFIG}/custom_components" && cd "${HA_CONFIG}/custom_components"
# Use the integration's GitHub releases or HACS download endpoint

# Restart HA to load the new integration
```
Restart HA:
```
Tool: ha_call_service
  domain: "homeassistant"
  service: "restart"
```
Then wait for HA API to come back: `for i in $(seq 1 30); do curl -s ${HA_URL}/api/ 2>/dev/null && break; sleep 2; done`

**Step 4: Verify the integration is now available**
Verify the integration is now available:
```
Tool: ha_config_entries_get
```
Check that the target domain appears in the results.

**Only after the integration is confirmed READY**, proceed to the user-facing integration setup (show dashboard link + guided flow).

### MANDATORY — Show the dashboard link (DO NOT SKIP THIS)

**Every single time you start an integration setup, your FIRST message to the user MUST contain the HA dashboard link.** This is non-negotiable. No exceptions. Not after HACS. Not after restart. EVERY time.

Before responding, run:
```bash
HA_PORT=$(grep HA_URL .env 2>/dev/null | grep -oP ':\K[0-9]+' || echo "8123")
echo "http://homeassistant.local:${HA_PORT}/config/integrations/dashboard"
```

Then your response MUST start with EXACTLY this structure (fill in the actual IP, port, and integration name):

> **Option 1 — Do it yourself:** [Open HA Integrations](http://homeassistant.local:<HA_PORT>/config/integrations/dashboard) → click "Add Integration" → search for "<integration name>". Let me know when done and I'll check what devices were added.
>
> **Option 2 — I'll guide you step by step:** (details below)

**Only AFTER showing both options**, proceed with the guided setup details.

**This applies at EVERY stage:**
- First time the user asks to add an integration? Show the link.
- After HACS installs and HA restarts? Show the link AGAIN.
- Integration failed and you're retrying? Show the link AGAIN.
- The user already saw it before? Show it AGAIN anyway.

**Important:** If Step 0 showed the integration is NOT_AVAILABLE, handle HACS installation first. But once the integration is available and you're starting the config flow, you MUST show the link.

### Guided Setup Process

Each step returns a `data_schema` array describing the fields. Each integration has completely different steps. Handle them generically.

**1. Start the flow**
```
Tool: ha_config_entries_flow
  handler: "<integration_name>"
```
Replace `<integration_name>` with the integration domain (e.g., `xiaomi_home`, `lg_thinq`, `hue`, `broadlink`).

**2. For EVERY step, read `data_schema` and present ALL fields to the user**

The response looks like:
```json
{
  "type": "form",
  "flow_id": "...",
  "step_id": "some_step",
  "data_schema": [
    {"type": "select", "options": [["cn", "China"], ["sg", "Singapore"]], "name": "cloud_server", "required": true},
    {"type": "boolean", "name": "advanced_options", "required": true, "default": false},
    {"type": "multi_select", "options": {"id1": "Home 1 [3 devices]"}, "name": "home_infos", "required": true},
    {"type": "string", "name": "host", "required": true}
  ]
}
```

For each field in `data_schema`, present it to the user in plain language:
- **`select`** → show all options as a numbered list, ask user to pick one
- **`multi_select`** → show all options, ask user to pick one or more (options may be an object `{id: label}` or array `[[id, label]]`)
- **`boolean`** → ask yes/no, mention the default
- **`string`** → ask user to type a value, explain what it's for based on the field name
- **`integer`** / `float` → ask for a number

**Format example to show the user:**
```
Here are the options for this step:

1. **Cloud Server** (required): Pick one:
   - cn — China mainland
   - sg — Singapore
   - us — United States

2. **Advanced Options**: Yes or No? (default: No)

Which do you choose for each?
```

**NEVER fill in a field without asking the user**, even if there's a default. Show the default but let the user confirm or change it.

**3. Submit the user's choices**
```
Tool: ha_config_entries_flow
  flow_id: "<flow_id>"
  data: {"field_name": "user_choice", ...}
```

**4. Handle special step types**

| `type` in response | What it means | What to do |
|---|---|---|
| `form` | A step with fields to fill | Read `data_schema`, present to user, submit their answers |
| `progress` | Waiting for external action (e.g., OAuth login, device pairing) | Check `description_placeholders` for URLs or instructions. If there's an OAuth URL, extract it and send to user. Then poll until the step changes. |
| `abort` | Flow was cancelled or blocked | Tell user the reason (`response.reason`). If `already_in_progress`, offer to clear stale flows and retry. |
| `create_entry` | Setup complete | Confirm success. Use `ha_search_entities` to show what devices were found. |

**5. If a step has an OAuth URL** (common for Xiaomi, Google, etc.)
- **Before showing any OAuth link**, ensure mDNS is broadcasting `homeassistant.local`. Run this silently — do NOT ask the user:
  ```bash
  # Check if already broadcasting
  avahi-resolve -n homeassistant.local 2>/dev/null | grep -q "$(hostname -I | awk '{print $1}')" || {
    # Install avahi-utils if needed
    which avahi-publish >/dev/null 2>&1 || sudo apt-get install -y avahi-utils
    # Set up persistent mDNS broadcast
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
  }
  ```
- The URL is usually in `description_placeholders.link_left` or similar, wrapped in an HTML `<a>` tag
- Extract the raw URL from the `href="..."` attribute
- **NEVER paste the raw OAuth URL.** Always send it as a markdown hyperlink: `[Authorize <integration name>](extracted_url)`. See the "All URLs must be markdown hyperlinks" rule above.
- Tell the user: "Open the link, log in, and let me know when you're done."
- **If the OAuth redirect fails** (user says the page didn't load, or the flow doesn't advance), it means `homeassistant.local` isn't resolving to the Pi. Detect the Pi's IP with `hostname -I | awk '{print $1}'` and give the user the exact hosts file command with the IP already filled in:
  - **Windows**: Search `cmd` in Start menu, right-click Command Prompt, click "Run as administrator", then paste: `echo <PI_IP> homeassistant.local >> C:\Windows\System32\drivers\etc\hosts`
  - **Mac/Linux**: `echo "<PI_IP> homeassistant.local" | sudo tee -a /etc/hosts`
  - Then tell them to click the OAuth link again
- After user confirms OAuth login, poll the flow status until it advances to the next step

**6. Repeat steps 2-5 until the flow completes (`type` = `create_entry`)**

**7. After completion, verify**
Use `ha_search_entities` to discover new devices from the integration.
Show the user what new devices were found.

### Error Handling
- **`already_in_progress`**: A previous setup attempt is stuck. Ask the user if they want to clear it, then delete all pending flows for that integration and retry.
- **`no_devices`**: The account/region has no devices. Ask the user to verify their region and that devices are registered in their app (Mi Home, LG ThinQ, etc.).
- **Any error with `errors.base`**: Show the error to the user and ask how to proceed. Don't silently retry.

### Clearing Stale Flows
```
Tool: ha_config_entries_flow
  flow_id: "<flow_id>"
  action: "delete"
```

### Key Principle
**You are a guide, not an autopilot.** Each integration is different. Read the actual response, present every option to the user, and only proceed with their explicit choices. If you don't understand a field, show it to the user as-is and ask what they want.
