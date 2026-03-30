First, invoke the /review-driven-workflow skill before doing anything else. Then follow its full staged workflow (Document → Plan → Implement → Validate → Learn) to debug and fix the smart home device authentication process in this project.

## Context
The user reports issues with the authentication process when adding smart home devices. The project has:
- Backend API (Bun/Elysia) at api/src/ with HA WebSocket auth in ha-client.ts
- Xiaomi device onboarding OAuth flow at api/src/routes/xiaomi.ts
- Device aggregation at api/src/device-aggregator.ts
- E2E test harness (openclaw) using Claude Agent SDK at harness/index.ts
- Docker Compose orchestration (network_mode: host)

## Scope
- BACKEND AND HARNESS ONLY. Do NOT touch anything in dashboard/ — the frontend is not a priority.
- The primary goal is to make the openclaw automation (harness/index.ts) work end-to-end for the device authentication flow on the backend.
- All fixes, tests, and validation must target api/ and harness/ only.

## Investigation Targets
1. Read ALL auth-related files: api/src/ha-client.ts, api/src/routes/xiaomi.ts, api/src/routes/services.ts, api/src/index.ts, api/src/device-aggregator.ts
2. Read the openclaw harness: harness/index.ts — understand how it tests the backend
3. Check .env file for token configuration
4. Test backend endpoints: curl -s http://localhost:3001/api/devices
5. Test HA connectivity: curl -s -H 'Authorization: Bearer $HA_TOKEN' http://localhost:8123/api/
6. Test Xiaomi setup flow: curl -s -X POST http://localhost:3001/api/xiaomi/setup -H 'Content-Type: application/json' -d '{"cloud_server":"sg"}'
7. Check Docker health: docker compose ps && docker compose logs api --tail=50 && docker compose logs homeassistant --tail=50
8. Look for: token issues, WebSocket auth failures, OAuth redirect problems, config flow errors, race conditions, missing error handling

## Fix Areas
- WebSocket auth handshake reliability (ha-client.ts)
- Xiaomi OAuth config flow error handling (routes/xiaomi.ts)
- Connection retry/reconnect logic
- Token validation and refresh handling
- Race conditions in device discovery after auth
- Harness test reliability — make sure the openclaw automation can run the auth flow without manual intervention

## E2E Validation via Openclaw
After implementing fixes, validate using the openclaw harness:
1. Rebuild backend: docker compose up -d --build api
2. Wait and verify: sleep 5 && curl -s http://localhost:3001/api/devices
3. Run the harness: cd harness && bun run index.ts (or however it's invoked)
4. Also manually test endpoints as a sanity check:
   - GET /api/devices (HA connection)
   - GET /api/areas (registry fetch)
   - POST /api/xiaomi/setup (config flow start)
   - GET /api/xiaomi/status/:flow_id (flow polling)
   - POST /api/services/light/toggle (service calls)
5. Check logs: docker compose logs api --tail=100
6. If the openclaw harness or endpoint tests fail, go back and iterate on the fix

## Rules
- DO NOT modify any files in dashboard/ — frontend is off-limits
- Only modify files in api/ and harness/
- Always read files before editing
- Test after each fix, do not batch
- Document findings at harness/auth-findings.md
- Document test results at harness/auth-test-results.md

## Success Criteria
Output <promise>AUTH FIXED</promise> ONLY when ALL are true:
- All auth issues identified and documented in harness/auth-findings.md
- Fixes implemented for all critical/high severity issues
- Backend API responds successfully to device queries
- Xiaomi setup flow initiates without auth errors
- Service calls work or gracefully handle errors
- Docker logs show no auth failures
- Openclaw harness runs the backend auth flow successfully
- Test results documented in harness/auth-test-results.md
