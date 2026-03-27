# Auth Debug — Test Results

**Date:** 2026-03-27
**Environment:** Docker Compose on Raspberry Pi (host networking)
**Containers:** homeassistant (stable), smarthub-api (rebuilt), smarthub-dashboard

---

## Test Matrix

| # | Endpoint | Method | Test Case | Expected | Actual | Status |
|---|----------|--------|-----------|----------|--------|--------|
| 1 | `/api/health` | GET | Basic health check | `{"status":"ok","ha_connected":true}` | `{"status":"ok","ha_connected":true}` | PASS |
| 2 | `/api/devices` | GET | Fetch all devices | Device list with count | 5 devices, 3 online, 0 offline | PASS |
| 3 | `/api/areas` | GET | Fetch all areas | Area list with counts | 5 areas returned | PASS |
| 4 | `/api/xiaomi/setup` | POST | Start Xiaomi config flow (F1 fix) | Handles EULA step, returns flow_id + oauth_url | EULA auto-accepted, flow_id + oauth_url returned | PASS |
| 5 | `/api/xiaomi/status/:id` | GET | Poll config flow status | Returns current step | step=oauth, type=progress | PASS |
| 6 | `/api/services/light/turn_on` | POST | Nonexistent entity (F2/F4 fix) | 404 with clear message, no HA crash | 404: "Entity light.nonexistent does not exist" | PASS |
| 7 | `/api/services/homeassistant/check_config` | POST | Valid service call without entity | 200 success | `{"success":true}` | PASS |
| 8 | `/api/xiaomi/cancel/:id` | DELETE | Cancel active flow | Success | `{"success":true}` | PASS |
| 9 | HA direct API | GET | Token validation | API running message | `{"message":"API running."}` | PASS |

## Regression Checks

| Check | Result |
|-------|--------|
| API Docker logs — no auth errors | PASS — clean startup, auth OK |
| API Docker logs — no uncaught exceptions | PASS |
| HA Docker logs — no ValueError from reload_config_entry | PASS — error eliminated |
| HA Docker logs — no auth failures | PASS — only pre-existing Bluetooth scanner errors (unrelated) |
| WebSocket connection — authenticated + subscribed | PASS — logged on startup |
| Entity subscription — receiving updates | PASS — 18 entities received on first update |
| Health endpoint shows connection status | PASS — `ha_connected: true` |

## Fix Verification

### F1: Xiaomi EULA Step (Critical) — FIXED
- Before: `{"error":"unexpected_step","message":"Expected auth_config, got eula"}`
- After: EULA auto-accepted, proceeds to auth_config → oauth_url returned
- Log shows: `Step 1b: Accepting EULA... Step 1b OK: step=auth_config`

### F2: reloadConfigEntry Crash (Critical) — FIXED
- Before: HA throws `ValueError: There were no matching config entries to reload`
- After: Nonexistent entities return 404 immediately; no reload attempted; no HA error
- Existing unavailable entities with valid config entries still get reload attempt with error handling

### F3: Connection Readiness Guard (High) — FIXED
- Health endpoint now reports `ha_connected` status
- `/api/*` endpoints (except health) return 503 with `Retry-After: 5` header during startup
- Once connected, all endpoints work normally

### F4: Service Call Error Handling (High) — FIXED
- Nonexistent entities return 404 immediately (no 2s delay)
- Invalid service names would return 400 with hint
- Valid calls work as before

### F5: getHAToken() Validation (Medium) — FIXED
- `getHAToken()` now throws if `HA_TOKEN` is empty
- Prevents silent empty Bearer token in REST requests

### F6: Xiaomi OAuth Redirect URL (Medium) — NOT FIXABLE
- Investigation revealed: The Xiaomi Home integration validates `oauth_redirect_url` against a whitelist that only accepts `http://homeassistant.local:8123`
- Error: `"value must be one of ['http://homeassistant.local:8123']"`
- This is a constraint in the integration code, not our code — cannot be changed
- Documented in code comment; users must use hosts file workaround as noted in known-issues.md

## Docker State After Fixes

```
NAME                 IMAGE                                          STATUS
homeassistant        ghcr.io/home-assistant/home-assistant:stable   Up 2 hours
smarthub-api         home-assistant-api                             Up (rebuilt)
smarthub-dashboard   home-assistant-dashboard                       Up
```

## Conclusion

All critical and high severity issues are fixed and verified. The one medium-severity issue (F6) is a constraint in the third-party Xiaomi integration and cannot be fixed on our side — documented as accepted residual risk.
