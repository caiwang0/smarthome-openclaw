# SmartHub P0 Issue Document

**Date:** 2026-04-15
**Scope:** `docs/fix-checklist.md` P0 items 1-4 only
**Analyst:** Codex
**Findings source:** `docs/fix-checklist.md`

## Summary

The current install path still depends on the Home Assistant browser onboarding wizard and manual long-lived token creation, which breaks the repo's "no browser install" promise. P0 scope is to make install create a usable Home Assistant admin account and API token offline, pin the Home Assistant image to the validated schema, and expose the generated admin credential once without weakening the existing safety model.

This workflow is constrained to the install/bootstrap path only. Approval-gate behavior, destructive-action gating, and the broader security posture must remain unchanged unless the user explicitly approves a change.

## Intent

**Goal:** Make the no-browser install path real for first run by letting `install.sh` leave the repo ready for agent-driven setup without requiring the HA onboarding wizard or a pasted long-lived token.
**Priority ranking:** safety and approval-gate integrity > secret handling > first-run success rate > installer convenience > code churn
**Decision boundaries:** agent may change installer code, add local helper scripts/tests, pin the HA image, and update local docs/artifacts for P0. Agent may not change approval-gate behavior, broaden privileged access, weaken secret handling, or widen scope beyond checklist P0 items 1-4 without approval.
**Stop rules:** pause and ask if implementation requires changing approval-gate behavior, weakening the security posture, persisting generated secrets outside the expected local install files, or relying on an HA schema change newer than the pinned image.

## Findings

### P1: Installer cannot bypass HA onboarding or manual token creation

**Severity:** Critical
**Category:** Reliability
**Affected components:** `install.sh`, `tools/setup.md`, `ha-config/.storage/`
**Source checklist item:** P0.1

**Description:** The installer creates `.env` and wiring for `ha-mcp`, but it does not pre-seed Home Assistant private storage before first boot. The documented setup flow still requires the user to open the HA onboarding wizard in a browser, create the admin user manually, and later paste a long-lived access token back into chat.

**Impact:** Fresh installs do not satisfy the repo's promised no-browser path. Users on headless or mobile-first setups hit a setup dead end before the first device-control moment, and `ha-mcp` remains unusable until manual browser work is complete.

**Success criteria:**
- [ ] On a fresh config directory, the install path writes valid `auth`, `auth_provider.homeassistant`, `onboarding`, and `core.config` files before `docker compose up -d` is reached.
- [ ] A first boot with the seeded storage does not present the HA onboarding wizard.
- [ ] The generated API credential is usable by `ha-mcp` without any browser-created token being pasted into `.env`.

---

### P2: Home Assistant image schema is not pinned to the validated storage format

**Severity:** Critical
**Category:** Reliability
**Affected components:** `docker-compose.yml`
**Source checklist item:** P0.2

**Description:** The compose file currently uses the floating `ghcr.io/home-assistant/home-assistant:stable` image. Offline pre-seeding depends on the exact `.storage` schema and auth-token behavior of a specific HA release, so a floating tag can silently invalidate the seeded files on a future install.

**Impact:** A later `stable` image can break the seeded auth/onboarding files without any code change in this repo, causing installs to regress unexpectedly or fail in ways that are difficult to debug.

**Success criteria:**
- [ ] `docker-compose.yml` pins HA to the validated release instead of `:stable`.
- [ ] The pinned version matches the schema/version assumptions used by the storage-seeding helper and validation evidence.

---

### P3: No standalone helper exists to generate seeded HA auth storage safely

**Severity:** Critical
**Category:** Security
**Affected components:** `scripts/` (new), `ha-config/.storage/`
**Source checklist item:** P0.3

**Description:** There is no local script that can generate a fresh admin password, bcrypt hash, stable storage UUIDs, and a long-lived API token in the exact file format Home Assistant expects. The installer therefore cannot create the required private storage atomically or idempotently.

**Impact:** Any attempt to fake the no-browser flow inside `install.sh` would be ad hoc and error-prone. Poorly generated auth data can leave HA unbootable, create unusable tokens, or weaken secret handling by printing or persisting credentials in the wrong place.

**Success criteria:**
- [ ] A standalone Python helper can generate the required seeded storage files for a fresh config directory without requiring a running HA instance.
- [ ] The helper emits only the secret material the installer needs to finish setup, and it does not print or persist extra secrets beyond the expected install files.
- [ ] Re-running the helper against an already-seeded config does not rotate credentials unexpectedly.

---

### P4: Installer does not provide a one-shot credential handoff for later dashboard access

**Severity:** High
**Category:** Usability
**Affected components:** `install.sh`, `.env`
**Source checklist item:** P0.4

**Description:** The current installer never creates or displays an HA admin password because account creation is deferred to the browser wizard. Once onboarding becomes offline, the installer also needs to hand the generated admin credential to the user in a controlled way without training them to copy or store the API token manually.

**Impact:** Users can end up with a working agent connection but no recoverable admin login details for the HA dashboard, or the installer may expose too much secret material if it dumps both password and API token indiscriminately.

**Success criteria:**
- [ ] `install.sh` prints the generated admin login details once at the end of a fresh install with an explicit save-it-now warning.
- [ ] The installer writes the generated long-lived token to `.env` automatically and does not print that token to stdout.
- [ ] Re-running `install.sh` on an already-seeded config does not reprint or rotate the existing admin password.

## Accepted Residual Risks

- Approval-gate behavior stays exactly as-is for this P0 scope; no gating rules are widened or relaxed.
- OAuth-based integrations still require a browser later in the setup flow; this P0 scope only removes the browser dependency from the HA install/bootstrap path.
- The seeded auth schema is intentionally tied to the pinned HA image version and must be revalidated before any future image bump.

## Dependencies Between Findings

- P2 blocks P1 and P3 because the seeded file format must match a known HA release.
- P3 blocks P1 and P4 because the installer cannot seed auth or display credentials until the helper exists.
- P4 depends on P1 and P3 because the displayed password must correspond to the seeded owner account.
