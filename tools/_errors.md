# Error Handling — Runtime Troubleshooting

## macOS host bootstrap issues

| Symptom | Likely Cause | Action |
|---|---|---|
| VirtualBox install failed | macOS blocked the installer or system extension | Re-run `install.sh` on the macOS host, approve the VirtualBox prompts, then retry the Home Assistant OS VM bootstrap. |
| Home Assistant OS VM never appears on the LAN | VirtualBox boot failed or the wrong Intel/Apple Silicon disk image was attached | Open VirtualBox on the macOS host, confirm the VM architecture matches the Mac, inspect the VM console, and rerun `install.sh`. |
| Automatic account/token bootstrap failed | Home Assistant finished onboarding before the installer could seed the first user, or the local API bootstrap could not reach the VM | Delete the VM and `~/.smarthub-vm`, rerun `install.sh`, and avoid opening the UI until the installer prints the generated credentials. |
| Home Assistant disappears when the Mac leaves home | The Home Assistant OS VM still depends on the Mac host staying powered on and on the home LAN | Move Home Assistant / SmartHub to a dedicated Raspberry Pi if you need an always-on home hub. |

## ha-mcp Tool Errors

| ToolError message | Meaning | Action |
|---|---|---|
| `entity not found` | Entity ID is wrong | Look up correct ID via `ha_search_entities`. Never guess entity IDs. |
| `invalid service data` | Bad parameters for service call | Check the service's required fields via `ha_list_services` for that domain. |
| `connection refused` | ha-mcp cannot reach HA | Check `docker ps`. If homeassistant is not running: `docker compose up -d`. |
| `timeout` | HA took too long to respond | Check `docker compose logs homeassistant --tail 20`. May be a transient error — retry once. |

## Entity States

| State | Meaning | Action |
|---|---|---|
| `unavailable` | Device offline or connection dropped | **Try the command anyway** — many devices (especially Xiaomi TV via DLNA) show unavailable but still respond. WebSocket verification will confirm if the command actually worked. If the command fails, tell the user the device may be powered off. |
| `unknown` | HA hasn't received state yet | Device may still be initializing after restart. Wait 30-60 seconds, then retry. |

## Home Assistant Issues

| Symptom | Likely Cause | Action |
|---|---|---|
| All devices unavailable | HA restarted or integration crashed | Check `docker compose logs homeassistant --tail 50`. Reload the integration via `ha_config_entries_get` to find the entry, then `ha_call_service` with `domain: homeassistant, service: reload_config_entry`. |
| HA unreachable | Network issue or HA overloaded | Verify HA is running with the same token-aware probe as setup: `HA_TOKEN=$(grep HA_TOKEN .env 2>/dev/null | cut -d= -f2); if [ -n "$HA_TOKEN" ] && [ "$HA_TOKEN" != "your_long_lived_access_token_here" ]; then curl -fsS ${HA_URL:-http://localhost:8123}/api/config -H "Authorization: Bearer $HA_TOKEN" >/dev/null; else curl -s ${HA_URL:-http://localhost:8123}/api/ 2>/dev/null \| grep -q "API running"; fi` |
| Token rejected (401) | Token expired or invalid | Have user create a new long-lived access token in HA UI and update `.env`. |

**Note:** The old "Port conflict" row (referencing Step 3b) is intentionally removed — there is no API port to conflict. HA port conflicts are handled by `install.sh` and `tools/setup.md` Step 3.

## Recovery Ladder

Before telling the user the system is stuck, follow this recovery ladder for recoverable local failures:

1. **Probe** — rerun the non-destructive readiness check that matches the failure:
   - HA reachability: rerun the token-aware `/api/config` probe above
   - ha-mcp reachability: rerun the `uvx ha-mcp@7.2.0 --smoke-test` check or the documented fallback
   - integration visibility: rerun `ha_config_entries_get` and `ha_search_entities`
2. **Inspect** — read the nearest logs or state for the failing component:
   - `docker compose logs homeassistant --tail 50`
   - `ha_config_entries_get` for config-entry state
   - pending config-flow state before assuming a setup flow is stuck
3. **Retry once** — if the failure looks transient, repeat the exact probe or command one time after inspection.
4. **Restart transient services** — restart only the transient piece that failed, then probe again:
   - Home Assistant:
     ```bash
     docker compose restart homeassistant
     HA_URL=$(grep HA_URL .env | cut -d= -f2); HA_URL=${HA_URL:-http://localhost:8123}
     HA_TOKEN=$(grep HA_TOKEN .env 2>/dev/null | cut -d= -f2)
     for i in $(seq 1 15); do
       if [ -n "${HA_TOKEN}" ] && [ "${HA_TOKEN}" != "your_long_lived_access_token_here" ]; then
         curl -fsS ${HA_URL}/api/config -H "Authorization: Bearer ${HA_TOKEN}" >/dev/null && break
       else
         curl -s ${HA_URL}/api/ 2>/dev/null | grep -q "API running" && break
       fi
       sleep 2
     done
     ```
   - Specific integration reload: use `ha_config_entries_get` to find the entry ID, then reload it via `ha_call_service` with `domain: homeassistant`, `service: reload_config_entry`, and `data: { "entry_id": "<entry_id>" }`.
5. **Resume the checkpointed install** — if install bootstrap was interrupted, rerun `install.sh` from the repo root so it can restore `.env` from `.openclaw/install-state.json` or stop safely before HA is started with partial bootstrap state.
   - On a macOS host, rerun `install.sh` from the macOS host so it can continue the VirtualBox + Home Assistant OS VM checkpoint instead of creating a second VM blindly.
6. **Escalate** — stop and ask the user instead of guessing when the next step would cross a safety boundary:
   - ask before deleting `ha-config`
   - ask before replacing an existing token/account
   - ask before making a config flow or OAuth choice

If the ladder does not restore the system, summarize what you probed, what you inspected, and which rung failed before escalating.
