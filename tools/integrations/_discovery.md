# Integrations — Read-Only Discovery

Use this entrypoint when you need to identify what a user might be able to connect before starting any config flow or add-device action.

This workflow is **read-only** and passive-first. It collects signals, ranks candidates, and stops short of mutation until the user explicitly confirms what they want to connect.

## Discovery Order

1. Read existing HA signals first:
   - `ha_config_entries_get`
   - `ha_search_entities`
2. Probe mDNS with `avahi-browse -atr`.
3. Probe SSDP.
4. If passive evidence is still insufficient, fall back to active LAN evidence:
   - `arp-scan --localnet`
   - `nmap -sn <subnet>`
   - `ip neigh show`
5. Present the results as candidates, not as implied mutation requests.
6. Hand confirmed candidates into `tools/integrations/_lifecycle.md`.
7. Require explicit user confirmation before any config-flow start or add-device action.

## Operating Rules

- Treat every result as a candidate until the user confirms it.
- Selecting a discovered device candidate still requires explicit user confirmation before any add-device action.
- Do not start `ha_config_entries_flow` from this doc.
- Do not add devices from this doc.
- If a command is missing or the shell lacks permission, treat that as a tooling constraint, not as proof that no devices exist.
- Continue down the active fallback chain only when passive evidence is insufficient or inconclusive.
- Stop the discovery phase with "no candidate devices found" only after the passive sources and the ordered fallback chain have all been exhausted or ruled out.

## Active Fallback Chain

Use this exact order when passive evidence is insufficient:

1. `arp-scan --localnet`
   - Best first active step when available because it returns MAC addresses that match the fingerprint corpus cleanly.
   - If `arp-scan` is not installed or requires privileges you do not have, note that constraint and continue to `nmap -sn`.
2. `nmap -sn <subnet>`
   - Use this when `arp-scan --localnet` is unavailable or insufficient.
   - If `nmap` is missing, blocked, or returns too little evidence to fingerprint confidently, continue to `ip neigh show`.
3. `ip neigh show`
   - Final low-assumption fallback when active scanners are unavailable.
   - Use it to salvage local ARP/neighbor evidence before concluding that no strong candidates were found.

Do not reorder these steps at runtime. Report which rung of the chain produced the useful evidence, and distinguish "tool missing" / "permission denied" from "scan returned no candidates."

## Fingerprint Corpus

Load every `tools/integrations/fingerprints/*.md` record before you rank candidates.

Each fingerprint file uses the same field names:

- `vendor`
- `integration_domains`
- `mac_ouis`
- `mdns_service_types`
- `ssdp_signatures`

Match observed MAC prefixes, mDNS service types, and SSDP headers against those shared fields. Use the same matching rules for every vendor file instead of adding vendor-specific branches to this workflow. If a fingerprint file leaves one signal family empty, skip that field and keep matching on the remaining evidence.

## Output Shape

Summarize what you found in plain language:

- likely integrations
- likely devices
- confidence level from passive evidence
- what passive signals supported the guess
- what active fallback evidence was needed, if any

Keep the message framed as discovery, not action. The next step is always the user's explicit confirmation.

Once the user confirms a candidate, hand off into `tools/integrations/_lifecycle.md`.
