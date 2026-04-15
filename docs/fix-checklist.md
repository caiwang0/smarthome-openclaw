# SmartHub Fix Checklist

Prioritized by impact on **time-to-first-device-control** — the AHA moment is the product; everything else serves it.

Companion to [`feedback.md`](feedback.md). Incorporates the pre-seed `.storage` approach discussed on 2026-04-15.

---

## P0 — Unblocks the "no browser" promise

| # | Item | Description | Touches |
|---|------|-------------|---------|
| 1 | Pre-seed HA `.storage` to skip onboarding | Generate `auth`, `auth_provider.homeassistant`, `onboarding`, `core.config` before `docker compose up -d`. Kills the browser wizard + long-lived-token paste in one move. | `install.sh`, `ha-config/.storage/` |
| 2 | Pin the HA Docker image | Currently `:stable`. Pre-seeding requires a schema you've validated; pin to e.g. `2026.3.4` and bump deliberately. | `docker-compose.yml` |
| 3 | Write `scripts/seed-ha-storage.py` | Standalone Python helper: take a config dir, generate random password + bcrypt hash + UUIDs + LLAT, write the four JSON files. Called by `install.sh` before HA boots. | `scripts/` (new) |
| 4 | One-shot credential display in `install.sh` | Print the generated admin password to stdout once at install end with "save this, it's the only time you'll see it." Same UX as SSH key gen. | `install.sh` |

## P1 — Closes the AHA-moment gap

| # | Item | Description | Touches |
|---|------|-------------|---------|
| 5 | Merge "connect first device" into core setup | Rewrite `tools/setup.md` Step 10 so it doesn't end in a menu — it ends with the user successfully controlling a device. Required, not optional. | `tools/setup.md` |
| 6 | Add `tools/integrations/_discovery.md` | New skill teaching the agent to scan the LAN with `arp-scan` / `avahi-browse` / SSDP *before* asking the user what devices they own. The agent has the network — use it. | `tools/integrations/` (new) |
| 7 | Add `tools/integrations/fingerprints/` database | Per-vendor MAC OUI prefixes, mDNS service types, SSDP signatures mapped to HA integration domains. Start with `xiaomi.md`, `hue.md`, `shelly.md`, `esphome.md`, `broadlink.md`. | `tools/integrations/fingerprints/` (new) |
| 8 | Add "no devices yet" check to first-run gate | Fourth check in `CLAUDE.md` alongside `.env` / HA / ha-mcp: if `ha_search_entities` returns zero non-default entities, proactively drive toward the first integration. | `CLAUDE.md` |
| 9 | Audit approval-gate matcher for autonomous paths | As the agent becomes more autonomous (scans network, adds integrations), gate `ha_config_entries_flow` creation too — otherwise a zealous agent silently adds integrations. | `.claude/settings.json`, `scripts/approval-gate.py` |
| 9a | Pre-install HACS during `install.sh` | Most integrations worth connecting (Xiaomi Home, Broadlink, custom cards) live in HACS. Requiring the user to install HACS manually before adding their first integration kills the AHA-moment. Drop `custom_components/hacs/` into `ha-config/` at install time so it's ready on first HA boot — user still clicks through HA UI + GitHub OAuth to activate, but the custom component is already on disk. Idempotent (skip if `ha-config/custom_components/hacs/manifest.json` exists), pin the HACS release version (don't chase `latest`), use `python3 -m zipfile` to avoid adding an `unzip` dep. Also update `tools/setup.md` and `tools/integrations/_guide.md` to assume HACS is pre-installed. | `install.sh`, `tools/setup.md`, `tools/integrations/_guide.md` |

## P2 — Structural cleanup around the new flow

| # | Item | Description | Touches |
|---|------|-------------|---------|
| 10 | Add `tools/integrations/_lifecycle.md` | State machine for the full integration lifecycle: `DISCOVERED → IDENTIFIED → INTEGRATION_SELECTED → CONNECTING → CONNECTED → VERIFIED → SKILL_GENERATED`. Defines failure handling at each phase. | `tools/integrations/` (new) |
| 11 | Demote `tools/integrations/_guide.md` to sub-skill | Keep the config-flow walker but make it callable from `_lifecycle.md`, not the primary entry point. New path: `_discovery.md` → `_lifecycle.md` → `_guide.md`. | `tools/integrations/_guide.md`, `TOOLS.md` |
| 12 | Add `arp-scan` permission fallback chain | `arp-scan --localnet` → `nmap -sn` → `ip neigh show`. Pre-decide in the skill rather than flail on a capability error at runtime. | `tools/integrations/_discovery.md` |
| 13 | Correct the "under 3 minutes" timing claim | Honest version: "30s on warm cache, 2–3 min on first image pull." Docker pull dominates cold start. | `README.md`, `docs/onepager.md`, marketing copy |
| 13a | Bundle `homeassistant-ai/skills` best-practices pack | The `home-assistant-best-practices` skill from [homeassistant-ai/skills](https://github.com/homeassistant-ai/skills) fills a real gap in our automation creation: anti-pattern table (`condition: template` → `condition: numeric_state`, `wait_template` → `wait_for_trigger`, `mode: single` → `mode: restart` for motion lights), helper decision matrix (`min_max` / `threshold` / `derivative` / `utility_meter` instead of template sensors), safe entity-rename refactoring (Config-Entry blind spots), version-current gotchas (`color_temp_kelvin` not `color_temp` in 2026.3+). Portability means **vendor it into the repo** (commit a snapshot under `tools/ha-best-practices/`), not `npx skills add` at install time — installs must work offline and survive the skills repo moving. Wire it in from `tools/automations/_guide.md` Step 4 ("Draft the automation JSON") so it loads *only* when drafting an automation, not always-on — our beta users already flagged latency, and the pack is ~10 reference files. `CLAUDE.md` rules (URL-as-markdown, confirm-before-destructive, match-user-language) stay authoritative; treat the pack as advisory. Update script to re-vendor: `scripts/update-ha-best-practices.sh` that pulls a pinned git SHA. | `tools/ha-best-practices/` (new), `tools/automations/_guide.md`, `TOOLS.md`, `scripts/` (new) |

## P3 — Repo hygiene that the rest of the work exposes

| # | Item | Description | Touches |
|---|------|-------------|---------|
| 14 | Decide the fate of `api/` | The Elysia/Bun HTTP server looks legacy (pre-MCP architecture). Either delete or document why it still exists. Currently confusing. | `api/` |
| 15 | Decide the fate of `harness/` | Has `bun.lock` + `dist/` but `prompts/` is empty. Same question: live or dead? | `harness/` |
| 16 | Fill in or remove `IDENTITY.md` / `USER.md` | Both are skeleton templates with empty fields. Either delete or populate with actual OpenClaw/user defaults. | `IDENTITY.md`, `USER.md` |
| 17 | Prune stale `docs/` artifacts | `docs/` has accumulated a lot (appendix, Issues, multiple rdw-* files). Separate live strategy docs from historical artifacts. | `docs/` |

---

## Sequencing

- **First PR — bundle P0 items 1–4.** Tightly coupled, not useful individually.
- **Second PR — P1 items 5–8.** Turns the "no browser" install into a product demo worth shipping.
- **Third PR — P1 item 9 + P2.** Safety audit + structural cleanup, now that the new flow exists.
- **P3 is ongoing cleanup.** Do during the other PRs when touching adjacent files.

## What this doesn't change

- Approval-gate safety model — keep it as-is.
- Skill-file routing architecture — keep it as-is.
- ha-mcp migration direction — keep it as-is.
- Per-device skill files (`tv.md`, `ma8-ac.md`, etc.) — the right pattern; the discovery system should *generate* more of them automatically.
- Integration OAuth (Xiaomi, Google) still needs one browser click — irreducible.
