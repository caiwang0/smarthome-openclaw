# SmartHub Install And Recovery Issue Document

**Date:** 2026-04-16
**Scope:** `install.sh`, `scripts/seed-ha-storage.py`, `tools/setup.md`, `CLAUDE.md`, `tools/_errors.md`, `tests/test_install_sh.py`, and the April 16, 2026 runtime artifacts on `edgenesis-openclaw-003`
**Analyst:** Codex

## Summary

I investigated the April 16, 2026 SmartHub install flow that was run through OpenClaw and then had to be manually repaired. I found five distinct reliability issues. The highest-risk problem is that the Home Assistant bootstrap path is not recoverable once execution is interrupted between seeding auth state, writing `.env`, and starting Home Assistant. The current instructions also rely on a soft text handoff rather than an enforced recovery flow, so the agent can stop too early or take the wrong branch after install.

## Intent

**Goal:** Make the one-command OpenClaw install finish without manual token retrieval, and require the agent to attempt safe self-repair for recoverable setup/runtime failures before telling the user the flow is stuck.
**Priority ranking:** successful first-run setup > preserving a clean no-browser flow > non-destructive recovery > minimizing user prompts
**Decision boundaries:** the agent may retry probes, inspect logs, restart transient services, and rerun non-destructive checks autonomously; it must ask before deleting HA state, rotating credentials, clearing user-owned integrations, or making other persistent/destructive changes
**Stop rules:** pause and ask the user if recovery would require deleting `ha-config`, replacing an existing token/account, or making a choice inside an HA config flow/OAuth flow

## Findings

### P1: HA bootstrap is not transaction-safe across seed, token write, and first boot

**Severity:** Critical
**Category:** Reliability
**Affected components:** `install.sh`, `scripts/seed-ha-storage.py`, `tools/setup.md`

**Description:** The no-browser bootstrap spans multiple steps that must stay coherent: seed Home Assistant private storage, write the generated token into `.env`, and only then continue into the first HA boot path. In `install.sh`, the seed output is written to a temp JSON file and the token is copied into `.env` afterward ([install.sh](/home/edgenesis/Downloads/home-assistant/install.sh:193), [install.sh](/home/edgenesis/Downloads/home-assistant/install.sh:221)). The seed helper refuses any partial auth state instead of repairing it ([seed-ha-storage.py](/home/edgenesis/Downloads/home-assistant/scripts/seed-ha-storage.py:283), [seed-ha-storage.py](/home/edgenesis/Downloads/home-assistant/scripts/seed-ha-storage.py:291)). If Home Assistant gets started before that chain is coherent, the next rerun can no longer recover the generated token safely.

**Impact:** A mid-flow interruption breaks the "no browser" promise and forces a destructive reset of an otherwise fresh HA config directory. On `edgenesis-openclaw-003`, the preserved directory `ha-config.partial.20260416-020708` contained a partial `.storage` state, and later recovery required a reset into `ha-config.reset.20260416-020756`.

**Success criteria:**
- [ ] Re-running setup after an interrupted fresh install can recover automatically without asking the user for a browser-generated token.
- [ ] A fresh-but-partial `ha-config/.storage` state is detected and handled before HA is started again.
- [ ] `.env` and the seeded HA auth state are kept in sync, or the installer records enough recovery metadata to rebuild them safely.

---

### P2: Post-install continuation depends on a soft text handoff, and the instructions conflict

**Severity:** High
**Category:** Workflow
**Affected components:** `install.sh`, `CLAUDE.md`, `tools/setup.md`

**Description:** The installer ends by printing an `AI_INSTRUCTION` block telling the agent to continue into `tools/setup.md` immediately ([install.sh](/home/edgenesis/Downloads/home-assistant/install.sh:285)). `CLAUDE.md` also says any `install.sh` request must continue straight into setup without waiting for the user ([CLAUDE.md](/home/edgenesis/Downloads/home-assistant/CLAUDE.md:36)). But `tools/setup.md` simultaneously states that it should not run automatically and should only trigger when the user explicitly asks for setup help ([setup.md](/home/edgenesis/Downloads/home-assistant/tools/setup.md:5)). That is a direct instruction conflict at the exact handoff boundary.

**Impact:** The agent can legitimately stop after install, ask the wrong next question, or branch into the manual onboarding flow even though the installer was supposed to keep going. That is how a successful partial install can still feel incomplete or "stuck" to the user.

**Success criteria:**
- [ ] `install.sh`, `CLAUDE.md`, and `tools/setup.md` define one consistent post-install behavior.
- [ ] After the install command finishes, the agent always enters the intended setup/recovery flow in the repo directory without waiting for another user nudge.
- [ ] The expected install-to-setup transition is covered by automated tests or doc assertions.

---

### P3: The installer has long silent phases that look stuck in OpenClaw

**Severity:** High
**Category:** Operability
**Affected components:** `install.sh`

**Description:** Several installer phases can run for a while with little or no visible progress. `git clone` can be quiet depending on how stdout/stderr are captured ([install.sh](/home/edgenesis/Downloads/home-assistant/install.sh:47)). The uv install suppresses stderr by piping into `sh 2>/dev/null` ([install.sh](/home/edgenesis/Downloads/home-assistant/install.sh:189)). The seed phase redirects its only structured output into a temp file instead of the terminal ([install.sh](/home/edgenesis/Downloads/home-assistant/install.sh:203), [install.sh](/home/edgenesis/Downloads/home-assistant/install.sh:212)).

**Impact:** In OpenClaw, a quiet command is easy to interpret as hung. That increases the chance that the run will be interrupted, manually monitored in the wrong place, or resumed out of order. Based on the observed transcript, this was at least a contributing factor to the April 16, 2026 failure sequence.

**Success criteria:**
- [ ] Every long-running installer phase emits a visible start message and a visible completion message.
- [ ] A slow clone, uv bootstrap, or seed run does not leave the user/agent without progress context for an extended period.
- [ ] If a phase fails, the failing phase name is printed before exit.

---

### P4: Error handling is advisory today; there is no mandatory safe auto-recovery ladder

**Severity:** High
**Category:** Recoverability
**Affected components:** `CLAUDE.md`, `tools/_errors.md`, `tools/integrations/_guide.md`

**Description:** The current docs tell the agent where to look after a failure, but they do not enforce a shared "try safe fixes first" workflow. `CLAUDE.md` says to check `tools/_errors.md` if a command fails ([CLAUDE.md](/home/edgenesis/Downloads/home-assistant/CLAUDE.md:47)). `tools/_errors.md` lists point fixes such as restart/retry ([tools/_errors.md](/home/edgenesis/Downloads/home-assistant/tools/_errors.md:29)). `tools/integrations/_guide.md` still routes many config-flow failures straight to the user rather than through a recovery ladder ([tools/integrations/_guide.md](/home/edgenesis/Downloads/home-assistant/tools/integrations/_guide.md:247)).

**Impact:** The agent can report "stuck" too early even when the failure is locally recoverable, and behavior varies by model/session because the recovery policy is scattered across multiple files instead of being mandatory and ordered.

**Success criteria:**
- [ ] A single recovery skill or recovery protocol defines the ordered steps for setup, runtime, and integration failures.
- [ ] For recoverable local failures, the agent attempts the allowed repair steps before telling the user the system is stuck.
- [ ] The recovery protocol clearly separates safe autonomous actions from actions that require user approval.

---

### P5: Test coverage misses the interrupted-install and recovery scenarios that actually failed

**Severity:** Medium
**Category:** Test Coverage
**Affected components:** `tests/test_install_sh.py`, `tests/test_seed_ha_storage.py`

**Description:** Current installer tests cover a clean first install and a clean rerun ([test_install_sh.py](/home/edgenesis/Downloads/home-assistant/tests/test_install_sh.py:126), [test_install_sh.py](/home/edgenesis/Downloads/home-assistant/tests/test_install_sh.py:150)). The seed helper test covers the helper's refusal to touch partial state ([test_seed_ha_storage.py](/home/edgenesis/Downloads/home-assistant/tests/test_seed_ha_storage.py:132)). What is not covered is the failure path that actually happened: interrupted install after seed-related work begins, placeholder token plus existing seeded auth, install-to-setup handoff behavior, and auto-recovery expectations.

**Impact:** The repo can pass its current tests while still failing on the exact OpenClaw-run workflow that matters most to users.

**Success criteria:**
- [ ] Automated tests cover interrupted installs and verify the expected recovery path.
- [ ] Tests cover the case where `.storage` exists but `.env` is still placeholder or missing a usable token.
- [ ] Tests cover the documented post-install auto-continue behavior and the new recovery ladder.

## Accepted Residual Risks

None documented for this investigation.

## Dependencies Between Findings

- P1 is the core failure. P3 makes P1 more likely by increasing the odds of interruption.
- P2 makes the system harder to recover correctly after P1 because the next action is not consistently defined.
- P4 is the policy gap that should absorb P1 and P2 at runtime.
- P5 should lock in the fixes for P1-P4 once the implementation plan is written.

## Follow-Up Checklist

- [ ] Define one canonical post-install transition and remove the `install.sh` / `CLAUDE.md` / `tools/setup.md` conflict.
- [ ] Add an install-state or recovery-state mechanism so interrupted fresh installs can resume safely.
- [ ] Add explicit progress output around clone, uv install, HA seed, token write, and HA verification.
- [ ] Define the auto-recovery ladder for OpenClaw: probe, inspect, retry, restart, resume, then escalate.
- [ ] Document which recovery actions are autonomous and which require user approval.
- [ ] Add tests for interrupted install, partial auth state, missing token recovery, and post-install continuation.
