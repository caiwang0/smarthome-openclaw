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
   - `ip neigh`
   - `arp-scan`
   - `nmap`
5. Present the results as candidates, not as implied mutation requests.
6. Require explicit user confirmation before any config-flow start or add-device action.

## Operating Rules

- Treat every result as a candidate until the user confirms it.
- Selecting a discovered device candidate still requires explicit user confirmation before any add-device action.
- Do not start `ha_config_entries_flow` from this doc.
- Do not add devices from this doc.

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
