# Auth Debug Findings

**Date:** 2026-03-27
**Scope:** Backend authentication and device onboarding flow
**Sources:** Code review of api/src/, live endpoint testing, Docker logs

## Summary

Six auth-related issues identified across the WebSocket client, Xiaomi OAuth flow, service call proxy, and token handling. Three are critical (block functionality), two are high (cause errors in logs or misleading behavior), one is medium.

---

### F1: Xiaomi Setup Flow Missing EULA Step Handler

**Severity:** Critical
**Category:** OAuth / Config Flow
**File:** `api/src/routes/xiaomi.ts:53`

**Description:** The `/api/xiaomi/setup` endpoint assumes the first step of the Xiaomi Home config flow is `auth_config`. However, the current Xiaomi Home integration now presents a `eula` step first (requiring EULA acceptance). The code returns a 400 error `"Expected auth_config, got eula"` and aborts.

**Evidence:**
```bash
curl -s -X POST http://localhost:3001/api/xiaomi/setup -H 'Content-Type: application/json' -d '{"cloud_server":"sg"}'
# Returns: {"error":"unexpected_step","message":"Expected auth_config, got eula",...}
```

The HA response shows `step_id: "eula"` with a boolean `eula` field that must be accepted before proceeding to `auth_config`.

**Fix:** Accept the EULA step automatically (submit `{eula: true}`) before proceeding to `auth_config`. The flow is: `eula` → `auth_config` → `oauth_progress` → `homes_select` → `create_entry`.

**Success criteria:**
- [ ] `/api/xiaomi/setup` handles `eula` step by auto-accepting
- [ ] Proceeds to `auth_config` and submits cloud server
- [ ] Returns `flow_id` and `oauth_url` successfully

---

### F2: reloadConfigEntry Crashes HA for Nonexistent Entities

**Severity:** Critical
**Category:** Service Call / Error Handling
**File:** `api/src/routes/services.ts:20-24`, `api/src/ha-client.ts:133-149`

**Description:** When a service call targets an unavailable entity, the code calls `reloadConfigEntry(entityId)` which makes a REST call to `homeassistant/reload_config_entry`. If the entity doesn't have a valid config entry (e.g., nonexistent entity, internal HA entity), HA throws `ValueError: There were no matching config entries to reload` — a 500 error that appears in HA logs.

**Evidence:** Docker logs show:
```
ValueError: There were no matching config entries to reload
```

The `reloadConfigEntry` function catches the error silently (`console.log`) but the HA error still pollutes logs and is an unnecessary API call.

**Fix:** Before calling `reloadConfigEntry`, verify the entity exists in the entity states. Skip the reload for nonexistent entities. Also wrap the reload call to handle 404/500 from HA gracefully without polluting HA logs — only attempt reload when the entity is known to exist and has a valid config entry.

**Success criteria:**
- [ ] Service calls to nonexistent entities return proper error without calling reloadConfigEntry
- [ ] No `ValueError` in HA Docker logs from reload attempts
- [ ] Reload still works for genuinely unavailable entities with valid config entries

---

### F3: No WebSocket Connection Readiness Guard

**Severity:** High
**Category:** Race Condition / Startup
**File:** `api/src/index.ts:33-38`, `api/src/ha-client.ts:53-95`

**Description:** The API server starts accepting requests (`app.listen()`) before the HA WebSocket connection is established (`connectToHA()` runs after). If a client hits `/api/devices` during the startup window, `getConnection()` throws `"Not connected to Home Assistant"` and the request returns a 502.

Additionally, `subscribeEntities()` may not have received the initial entity dump yet when early requests arrive, so `getEntities()` returns an empty object. The device aggregator does warn about this but still returns devices with `status: "unknown"` for all entities.

**Evidence:** `device-aggregator.ts:60` logs: `"WARNING: No live entity states — HA subscription may not be ready yet"` during the startup window.

**Fix:** Add a connection readiness flag. Return a clear "API is starting, please retry" (503 Service Unavailable) response when the HA connection isn't established yet, instead of letting it throw.

**Success criteria:**
- [ ] Requests during startup return 503 with clear message
- [ ] Once connected, requests work normally
- [ ] No uncaught exceptions from getConnection() during startup

---

### F4: Service Call Returns Raw Error for Invalid Services

**Severity:** High
**Category:** Error Handling
**File:** `api/src/routes/services.ts:30-35`

**Description:** When a service call fails (e.g., `light.toggle` doesn't exist — the correct service is `light.turn_on`/`light.turn_off`), the error message from HA is passed through directly: `"Service light.toggle not found."`. While technically correct, this provides no guidance to the caller. More importantly, the `reloadConfigEntry` workaround runs before the service call for any unavailable entity, adding a 2-second delay even for clearly invalid requests.

**Evidence:**
```bash
curl -s -X POST http://localhost:3001/api/services/light/toggle -H 'Content-Type: application/json' -d '{"entity_id":"light.nonexistent"}'
# Waits 2+ seconds (reload attempt), then: {"error":"Service call failed","message":"Service light.toggle not found."}
```

**Fix:** Validate the entity_id exists before attempting reload. Return a 404 for unknown entities. Keep the 502 for genuine HA communication failures.

**Success criteria:**
- [ ] Unknown entity returns 404 quickly (no 2s delay)
- [ ] Invalid service name returns 400 with helpful message
- [ ] Valid service calls to real entities still work

---

### F5: getHAToken() Returns Empty String Silently

**Severity:** Medium
**Category:** Token Handling
**File:** `api/src/ha-client.ts:155-157`

**Description:** `getHAToken()` returns `process.env.HA_TOKEN || ""`. Routes that use this (camera.ts, xiaomi.ts) will make HTTP requests to HA with `Authorization: Bearer ` (empty token), getting 401 errors that appear as generic "Camera snapshot failed" or "setup_failed" messages. The root cause (missing token) is hidden.

The `connectToHA()` function correctly validates the token and throws, but `getHAToken()` is used independently by REST-based routes without any validation.

**Fix:** Make `getHAToken()` throw if the token is empty, matching the behavior of `connectToHA()`. Or validate once at startup.

**Success criteria:**
- [ ] Missing HA_TOKEN causes a clear startup error
- [ ] REST routes don't silently use an empty Bearer token

---

### F6: Xiaomi OAuth Redirect URL Not Using HA External URL

**Severity:** Medium → **NOT FIXABLE (accepted residual risk)**
**Category:** OAuth Configuration
**File:** `api/src/routes/xiaomi.ts:72`

**Description:** The `oauth_redirect_url` is hardcoded to `http://homeassistant.local:8123`. Investigation revealed this is a constraint in the Xiaomi Home integration itself — it validates the URL against a whitelist that only accepts `http://homeassistant.local:8123`. Attempting to use `http://192.168.2.97:8123` returns: `"value must be one of ['http://homeassistant.local:8123']"`.

**Resolution:** Cannot be fixed on our side. Users must add `homeassistant.local` to their hosts file as documented in `docs/known-issues.md`. Added explanatory code comment.

---

## Accepted Residual Risks

1. **OAuth still requires browser interaction** — The user must complete the Xiaomi login in their browser. This is inherent to OAuth and cannot be automated.
2. **DLNA reconnect workaround adds latency** — The 2-second delay for unavailable entities is a known workaround for flaky Xiaomi TVs. The fix in F2/F4 only skips it for clearly invalid entities.

## Dependencies Between Findings

```
F5 (token validation) ← F1, F2, F4, F6 all depend on valid token
F3 (readiness guard) ← independent, foundational
F1 (Xiaomi EULA) ← depends on F6 (correct redirect URL)
F2 (reload crash) ← independent
F4 (service errors) ← related to F2 (same code path)
```

## Intent

**Goal:** Make all auth-related flows reliable and error-free.
**Priority:** F1 > F2 > F3 > F4 > F5 > F6
**Stop rule:** All critical and high severity issues fixed. Medium issues fixed if time allows.
**Decision boundary:** Fixes must be backend-only. No dashboard changes.
