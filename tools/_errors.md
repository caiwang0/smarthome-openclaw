# Error Handling — Runtime Troubleshooting

## SmartHub API Errors

| HTTP Status | Meaning | Action |
|-------------|---------|--------|
| **503** | HA not connected | Check `docker ps`. If homeassistant is not running: `docker compose up -d`. If running, check logs: `docker logs homeassistant --tail 20` |
| **404** | Entity not found | Entity ID is wrong. Look up correct ID via `/api/devices`. Never guess entity IDs. |
| **400** | Service not found | Check domain/service spelling. Common services: `turn_on`, `turn_off`, `toggle` (switch only). See `_services.md` for full list. |
| **502** | HA service call failed | Check `docker logs homeassistant --tail 20` for details. May be a transient error — retry once. |

## Entity States

| State | Meaning | Action |
|-------|---------|--------|
| `unavailable` | Device offline or connection dropped | **Try the command anyway** — many devices (especially Xiaomi TV via DLNA) show unavailable but still respond. If the command fails, tell the user the device may be powered off. |
| `unknown` | HA hasn't received state yet | Device may still be initializing after restart. Wait 30-60 seconds, then retry. |

## Home Assistant Issues

| Symptom | Likely Cause | Action |
|---------|-------------|--------|
| All devices unavailable | HA restarted or integration crashed | Check `docker logs homeassistant --tail 50`. Try reloading the integration: `HA_URL=$(grep HA_URL .env \| cut -d= -f2); HA_URL=${HA_URL:-http://localhost:8123}; curl -s -X POST ${HA_URL}/api/config/config_entries/entry/<entry_id>/reload -H "Authorization: Bearer $HA_TOKEN"` |
| API timeout | Network issue or HA overloaded | Verify HA is running: `HA_URL=$(grep HA_URL .env \| cut -d= -f2); curl -s ${HA_URL:-http://localhost:8123}/api/`. Check `.env` has correct `HA_URL`. |
| Token rejected (401) | Token expired or invalid | Have user create a new long-lived access token in HA UI and update `.env`. |
| Port conflict | Another service using the port | Run `ss -tlnp \| grep ':<port> '` to find the conflict. See `tools/setup.md` Step 3b for resolution. |

## Recovery Steps

**Quick restart (fixes most transient issues):**
```bash
docker compose restart
API_PORT=$(grep API_PORT .env | cut -d= -f2)
# Wait for API to come back
for i in $(seq 1 15); do curl -s http://localhost:${API_PORT}/api/health 2>/dev/null | grep -q "ok" && break; sleep 2; done
```

**Reload a specific integration:**
```bash
HA_URL=$(grep HA_URL .env | cut -d= -f2); HA_URL=${HA_URL:-http://localhost:8123}
HA_TOKEN=$(grep HA_TOKEN .env | cut -d= -f2)
# Find the config entry ID for the integration
curl -s ${HA_URL}/api/config/config_entries/entry \
  -H "Authorization: Bearer $HA_TOKEN" | python3 -c "
import json, sys
entries = json.load(sys.stdin)
for e in entries:
    if e['domain'] == '<integration_domain>':
        print(f\"Entry ID: {e['entry_id']} — {e['title']} (state: {e['state']})\")"

# Reload it
curl -s -X POST ${HA_URL}/api/config/config_entries/entry/<entry_id>/reload \
  -H "Authorization: Bearer $HA_TOKEN"
```
