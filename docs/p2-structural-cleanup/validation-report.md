# P2 Structural Cleanup Validation Report

**Date:** 2026-04-20
**Scope:** P2 items 10-12 and 13a from `docs/fix-checklist.md`
**Result:** PASS

## Scope Check

- `docs/fix-checklist.md` now records: `Status: completed in repo on 2026-04-20 for items 10-12 and 13a. Item 13 was removed from scope on 2026-04-20.`
- Validation covered the four findings in `docs/p2-structural-cleanup/issue-doc.md`.

## Commands Run

```bash
grep -n "Before adding an integration" CLAUDE.md
grep -n "tools/integrations/_discovery.md\|tools/integrations/_lifecycle.md" \
  CLAUDE.md TOOLS.md README.md tools/integrations/_guide.md \
  tools/integrations/_discovery.md tools/integrations/_lifecycle.md

grep -n "arp-scan --localnet\|nmap -sn\|ip neigh show" \
  tools/integrations/_discovery.md tests/test_integrations_docs.py

grep -n "tools/ha-best-practices/\|home-assistant-best-practices\|Pinned commit" \
  TOOLS.md tools/automations/_guide.md tools/ha-best-practices/README.md \
  scripts/update-ha-best-practices.sh tests/test_automation_docs.py

./scripts/update-ha-best-practices.sh

python3 -m unittest \
  tests.test_integrations_docs \
  tests.test_automation_docs \
  tests.test_setup_docs \
  tests.test_recovery_docs -v

grep -n "DISCOVERED → IDENTIFIED → INTEGRATION_SELECTED → CONNECTING → CONNECTED → VERIFIED → SKILL_GENERATED" \
  tools/integrations/_lifecycle.md
grep -n "failure handling" tools/integrations/_lifecycle.md

test -f tools/integrations/_lifecycle.md && echo LIFECYCLE_OK
test -d tools/ha-best-practices && echo PACK_OK
test -f scripts/update-ha-best-practices.sh && echo SCRIPT_OK

grep -n "Status: completed in repo on 2026-04-20 for items 10-12 and 13a" docs/fix-checklist.md
grep -n "Item 13 was removed from scope" docs/fix-checklist.md
```

## Results by Finding

| Finding | Requirement | Evidence | Result |
|---|---|---|---|
| P1 | Add lifecycle orchestrator for the post-discovery path | `tools/integrations/_lifecycle.md` exists; the full lifecycle state sequence and failure-handling text were found by grep; integration routing in `CLAUDE.md`, `TOOLS.md`, and `README.md` now points through discovery → lifecycle → guide | PASS |
| P2 | Demote `_guide.md` to a sub-skill | `tools/integrations/_guide.md` now identifies itself as a sub-skill for `CONNECTING`; live routers no longer tell agents to enter integrations through `_guide.md` alone | PASS |
| P3 | Define the ordered active-scan fallback chain | `tools/integrations/_discovery.md` and `tests/test_integrations_docs.py` both show the ordered chain `arp-scan --localnet` → `nmap -sn` → `ip neigh show`; command-missing and permission failure modes are documented as tooling constraints, not “no devices found” | PASS |
| P4 | Vendor the best-practices pack and load it only during automation drafting | `tools/ha-best-practices/` exists with upstream provenance and pinned commit `e503410aa2c412dd27579562f194ee6614314dd8`; `tools/automations/_guide.md` loads it only at Step 4; `TOOLS.md` marks it advisory; `./scripts/update-ha-best-practices.sh` completed successfully | PASS |

## Test Suite Result

`python3 -m unittest tests.test_integrations_docs tests.test_automation_docs tests.test_setup_docs tests.test_recovery_docs -v`

- Ran 6 tests
- Result: `OK`

## Conclusion

The narrowed P2 scope is complete in the repo: items 10-12 and 13a are validated, and item 13 is removed from scope in the checklist.
