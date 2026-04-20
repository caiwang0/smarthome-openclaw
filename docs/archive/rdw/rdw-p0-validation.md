# Validation Report

**Date:** 2026-04-15
**Issue document:** `docs/rdw-p0-issue-doc.md`
**Plan document:** `docs/rdw-p0-plan.md`
**Total findings:** 4
**Passed:** 4 | **Failed:** 0 | **Skipped:** 0

## Results

### P1: Installer cannot bypass HA onboarding or manual token creation - PASS

- [x] The install path now seeds `auth`, `auth_provider.homeassistant`, `onboarding`, and `core.config` before HA boot.
  Evidence: `python3 -m unittest tests.test_seed_ha_storage tests.test_install_sh -v`
  Output summary: `Ran 5 tests in 4.341s` and `OK`.
  Relevant checks:
  `test_fresh_seed_writes_expected_files_and_secret_output`
  `test_install_seeds_token_and_prints_password_once_on_fresh_install`

- [x] A first boot with seeded storage behaves like completed onboarding instead of first-run setup.
  Evidence: seeded a fresh temp config with `python3 scripts/seed-ha-storage.py --config-dir <tmp> --time-zone Asia/Singapore --ha-version 2026.3.4`, then booted `ghcr.io/home-assistant/home-assistant:2026.3.4` on a throwaway port as the local UID.
  Output:
  `CONFIG_CODE=200`
  `PROVIDERS_CODE=200`
  `CONFIG_BODY` included `"config_source":"storage"`, `"state":"RUNNING"`, `"version":"2026.3.4"`.
  `PROVIDERS_BODY` was `{"providers":[{"name":"Home Assistant Local","id":null,"type":"homeassistant"}],"preselect_remember_me":true}`.
  Inference: the frontend is in normal local-auth login mode, not the onboarding wizard.

- [x] The generated API credential works without any browser-created token being pasted into `.env`.
  Evidence: the same fresh-container validation returned `200` from `GET /api/config` using only the generated bearer token.
  Supporting evidence: `uvx ha-mcp@7.2.0 --smoke-test` under an isolated temp `HOME` with the same `HOMEASSISTANT_URL` and `HOMEASSISTANT_TOKEN` environment booted successfully and reported `SMOKE TEST PASSED` with `86 tools discovered`.
  Inference: the seeded `.env` values are acceptable for the configured `ha-mcp` runtime path; the direct HA `200` response proves the token itself is valid.

### P2: Home Assistant image schema is not pinned to the validated storage format - PASS

- [x] The compose file is pinned to the validated release.
  Evidence: `sed -n '1,4p' docker-compose.yml`
  Output:
  `services:`
  `  homeassistant:`
  `    image: "ghcr.io/home-assistant/home-assistant:2026.3.4"`

- [x] The pinned version matches the helper and live validation evidence.
  Evidence: the helper was invoked with `--ha-version 2026.3.4`, the validation container used `ghcr.io/home-assistant/home-assistant:2026.3.4`, and `CONFIG_BODY` reported `"version":"2026.3.4"`.

### P3: No standalone helper exists to generate seeded HA auth storage safely - PASS

- [x] A standalone Python helper now generates the four required private storage files on a fresh config directory.
  Evidence: `scripts/seed-ha-storage.py` exists and is exercised directly by `python3 -m unittest tests.test_seed_ha_storage -v`.
  Output summary: the module passed `3` tests covering fresh generation, JWT shape, and partial-state refusal.

- [x] The helper limits secret output and refuses unsafe partial-state writes.
  Evidence: `test_second_run_is_idempotent_and_token_matches_refresh_token` verified reruns do not emit password/token, and `test_partial_existing_state_fails_without_touching_existing_file` verified the helper exits on partial auth state without overwriting existing files.

- [x] The helper does not rotate credentials on rerun.
  Evidence: the same idempotency test asserted `created: false` on the second run, with no `password` or `token` in stdout.

### P4: Installer does not provide a one-shot credential handoff for later dashboard access - PASS

- [x] `install.sh` prints the generated admin login details once on a fresh install.
  Evidence: `test_install_seeds_token_and_prints_password_once_on_fresh_install` asserted stdout contains the one-shot warning and the generated username while omitting the token.

- [x] The installer writes the long-lived token to `.env` automatically and does not print it.
  Evidence: the same test asserted the cloned target `.env` no longer contains `your_long_lived_access_token_here`, and stdout did not match a JWT-shaped token regex.

- [x] Re-running the installer does not reprint or rotate credentials.
  Evidence: `test_second_install_keeps_existing_credentials_hidden` passed and verified the second run omitted the password warning while keeping `.env` unchanged.

## Accepted Residual Risks

- Approval-gate behavior was not changed.
- OAuth-based integrations still require a browser later in setup.
- The seeding format is intentionally coupled to Home Assistant `2026.3.4`; future bumps require revalidation.

## New Issues Discovered

None.

## Verdict

All 4 P0 findings validated. The no-browser HA install/bootstrap path is real for fresh installs, and the changes preserve the existing approval-gate behavior and security posture.
