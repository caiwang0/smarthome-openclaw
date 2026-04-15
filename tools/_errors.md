# Error Handling — Runtime Troubleshooting

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

## Recovery Steps

**Quick restart (fixes most transient issues):**
```bash
docker compose restart homeassistant
# Wait for HA to come back
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

**Reload a specific integration:**
Use `ha_config_entries_get` to list entries and find the entry ID for the integration, then reload it via `ha_call_service` with `domain: homeassistant, service: reload_config_entry` and `data: { "entry_id": "<entry_id>" }`.

For persistent issues, check `tools/setup.md` for port conflict resolution.
