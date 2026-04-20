# SmartHub Fix Checklist

Prioritized by impact on **time-to-first-device-control** — the AHA moment is the product; everything else serves it.

Companion to [`feedback.md`](feedback.md). Incorporates the pre-seed `.storage` approach discussed on 2026-04-15.

---

## P0 — Done: unblocks the "no browser" promise

Status: completed in repo on 2026-04-15. Items 1-4 are implemented and should now be treated as done.

| # | Item | Description | Touches |
|---|------|-------------|---------|
| 1 | Pre-seed HA `.storage` to skip onboarding | Generate `auth`, `auth_provider.homeassistant`, `onboarding`, `core.config` before `docker compose up -d`. Kills the browser wizard + long-lived-token paste in one move. | `install.sh`, `ha-config/.storage/` |
| 2 | Pin the HA Docker image | Currently `:stable`. Pre-seeding requires a schema you've validated; pin to e.g. `2026.3.4` and bump deliberately. | `docker-compose.yml` |
| 3 | Write `scripts/seed-ha-storage.py` | Standalone Python helper: take a config dir, generate random password + bcrypt hash + UUIDs + LLAT, write the four JSON files. Called by `install.sh` before HA boots. | `scripts/` (new) |
| 4 | One-shot credential display in `install.sh` | Print the generated admin password to stdout once at install end with "save this, it's the only time you'll see it." Same UX as SSH key gen. | `install.sh` |

## P1 — Done: closes the AHA-moment gap

Status: completed in repo on 2026-04-15 for items 5-9. Item 9a remains paused and is not part of the completed set.

| # | Item | Description | Touches |
|---|------|-------------|---------|
| 5 | Merge "connect first device" into core setup | Rewrite `tools/setup.md` so setup does not end at a menu. It must end after exactly one first-win path succeeds: either (a) one integration is added, or (b) one device is added/discovered and connected. Success means Home Assistant exposes at least one new non-system entity and the agent verifies one read or control action against it. Required, not optional. | `tools/setup.md` |
| 6 | Add `tools/integrations/_discovery.md` | New skill teaching the agent to discover device candidates before asking the user for an inventory. Use passive-first discovery (`avahi-browse`, SSDP, existing HA/discovery signals) and only fall back to active LAN scans (`arp-scan`, `nmap`, `ip neigh`) when needed. After discovery, present the findings to the user as candidate devices/integrations instead of asking a blind "what devices do you own?" question. | `tools/integrations/` (new) |
| 7 | Add `tools/integrations/fingerprints/` database | Create per-vendor fingerprint files that `_discovery.md` can actually consume: MAC OUI prefixes, mDNS service types, SSDP signatures, and likely HA integration domains in a consistent format. Start with `xiaomi.md`, `hue.md`, `shelly.md`, `esphome.md`, `broadlink.md`. | `tools/integrations/fingerprints/` (new) |
| 8 | Add "no devices yet" check to first-run gate | Fourth check in `CLAUDE.md` alongside `.env` / HA / ha-mcp: if `ha_search_entities` returns zero device-backed, non-system entities, proactively route into the first-device discovery/integration flow instead of stopping at "connected, but no devices yet." | `CLAUDE.md` |
| 9 | Audit approval-gate matcher for autonomous paths | After discovery, the agent should show the user the devices/services it found and let them choose whether to add one of those devices or start an integration flow. Passive discovery is allowed without approval. Starting a new integration/config flow or adding a device requires explicit user confirmation; audit the approval-gate matcher to enforce that boundary. | `.claude/settings.json`, `scripts/approval-gate.py`, `tools/integrations/_guide.md` |
| 9a | Add explicit HACS choice branch | When the chosen integration is not available in HA and likely needs HACS, do not silently install HACS and do not make it mandatory by default. The agent should present a short decision message explaining the HACS path versus the manual-install path, then let the user choose. If the user opts into HACS, the agent may download/install HACS and guide the user through linking it; if the user declines, stay on the manual `custom_components/<domain>` path for that specific integration. | `tools/setup.md`, `tools/integrations/_guide.md` |

### Item 9a — Implementation notes

- Present the HACS choice only after discovery/selection identifies an integration that is not available in stock HA and is likely HACS-backed.
- The user-facing choice should summarize both paths clearly:
  - `HACS`: pros = easier installs, update visibility, broader ecosystem, works with `ha_hacs_*` MCP tools. cons = requires a GitHub account/linking step, extra setup friction, one more moving part.
  - `Manual install`: pros = no GitHub/HACS requirement, better for one curated integration, more deterministic. cons = no `ha_hacs_*` workflow, manual updates/rollback, narrower ecosystem.
- The user must explicitly choose before any HACS install/download work starts. Do not silently install HACS.
- If the user chooses HACS, implement the download/install path as:
  1. Run inside the HA container: `docker compose exec homeassistant bash -c 'wget -O - https://get.hacs.xyz | bash -'`
  2. Restart Home Assistant
  3. Guide the user through the HACS setup/linking step in the HA UI (GitHub device authorization stays user-facing)
  4. After HACS is active, use HACS to download the target custom integration
- If the user declines HACS, stay on the manual `config/custom_components/<domain>` route for that integration instead of blocking the flow.
- `install.sh` should not pre-install HACS. This is a user decision in the first-device/integration flow, not part of base bootstrap.

## P2 — Structural cleanup around the new flow

| # | Item | Description | Touches |
|---|------|-------------|---------|
| 10 | Add `tools/integrations/_lifecycle.md` | State machine for the full integration lifecycle: `DISCOVERED → IDENTIFIED → INTEGRATION_SELECTED → CONNECTING → CONNECTED → VERIFIED → SKILL_GENERATED`. Defines failure handling at each phase. | `tools/integrations/` (new) |
| 11 | Demote `tools/integrations/_guide.md` to sub-skill | Keep the config-flow walker but make it callable from `_lifecycle.md`, not the primary entry point. New path: `_discovery.md` → `_lifecycle.md` → `_guide.md`. | `tools/integrations/_guide.md`, `TOOLS.md` |
| 12 | Add `arp-scan` permission fallback chain | `arp-scan --localnet` → `nmap -sn` → `ip neigh show`. Pre-decide in the skill rather than flail on a capability error at runtime. | `tools/integrations/_discovery.md` |
| 13 | Correct the "under 3 minutes" timing claim | Honest version: "30s on warm cache, 2–3 min on first image pull." Docker pull dominates cold start. | `README.md`, `docs/onepager.md`, marketing copy |
| 13a | Bundle `homeassistant-ai/skills` best-practices pack | The `home-assistant-best-practices` skill from [homeassistant-ai/skills](https://github.com/homeassistant-ai/skills) fills a real gap in our automation creation: anti-pattern table (`condition: template` → `condition: numeric_state`, `wait_template` → `wait_for_trigger`, `mode: single` → `mode: restart` for motion lights), helper decision matrix (`min_max` / `threshold` / `derivative` / `utility_meter` instead of template sensors), safe entity-rename refactoring (Config-Entry blind spots), version-current gotchas (`color_temp_kelvin` not `color_temp` in 2026.3+). Portability means **vendor it into the repo** (commit a snapshot under `tools/ha-best-practices/`), not `npx skills add` at install time — installs must work offline and survive the skills repo moving. Wire it in from `tools/automations/_guide.md` Step 4 ("Draft the automation JSON") so it loads *only* when drafting an automation, not always-on — our beta users already flagged latency, and the pack is ~10 reference files. `CLAUDE.md` rules (URL-as-markdown, confirm-before-destructive, match-user-language) stay authoritative; treat the pack as advisory. Update script to re-vendor: `scripts/update-ha-best-practices.sh` that pulls a pinned git SHA. | `tools/ha-best-practices/` (new), `tools/automations/_guide.md`, `TOOLS.md`, `scripts/` (new) |

## P3 — Repo hygiene that the rest of the work exposes

Status: completed in repo on 2026-04-20 for items 14-17.

| # | Item | Description | Touches |
|---|------|-------------|---------|
| 14 | Decide the fate of `api/` | Verified the Elysia/Bun backend had no active runtime/config/install wiring, then removed `api/` from the workspace. | `api/` |
| 15 | Decide the fate of `harness/` | Confirmed `harness/` was only local residue (`bun.lock` + built output) and removed it from the workspace. | `harness/` |
| 16 | Fill in or remove `IDENTITY.md` / `USER.md` | Removed `IDENTITY.md`. Kept `USER.md` intentionally generic because this repo is being published for others to copy and fill in. | `IDENTITY.md`, `USER.md` |
| 17 | Prune stale `docs/` artifacts | Moved incident, RDW, and strategy/history files under `docs/archive/` so top-level `docs/` only carries live materials and assets. | `docs/` |

---

## Sequencing

- **Completed — P0 items 1–4.** Tightly coupled bundle is already landed in the repo.
- **Completed — P1 items 5–9.** The first-win setup path, passive-first discovery flow, fingerprint corpus, empty-instance guardrail, and approval-boundary audit are landed in the repo.
- **Later PR — P1 item 9a + P2.** Explicit HACS choice branch + structural cleanup, now that the new flow exists.
- **Completed — P3 items 14–17.** Legacy backend residue is gone, reusable templates are clarified, and historical docs are archived under `docs/archive/`.

## What this doesn't change

- Approval-gate safety model — keep it as-is.
- Skill-file routing architecture — keep it as-is.
- ha-mcp migration direction — keep it as-is.
- Per-device skill files (`tv.md`, `ma8-ac.md`, etc.) — the right pattern; the discovery system should *generate* more of them automatically.
- Integration OAuth (Xiaomi, Google) still needs one browser click — irreducible.
