# Home Assistant Best Practices Snapshot

- Upstream repository: <https://github.com/homeassistant-ai/skills>
- Vendored skill path: `skills/home-assistant-best-practices`
- Pinned commit: `e503410aa2c412dd27579562f194ee6614314dd8`
- Vendored on: `2026-04-20`
- Included files: upstream `SKILL.md` plus the `references/` directory used by that skill

This directory is a committed offline snapshot of the upstream `home-assistant-best-practices` pack.

Local routing rules for this repo:

- Load this pack only when `tools/automations/_guide.md` reaches Step 4, "Draft the automation JSON".
- Treat the pack as advisory Home Assistant guidance for automation structure, helpers, refactoring safety, and domain-specific gotchas.
- `CLAUDE.md` remains authoritative for SmartHub-specific user interaction rules such as confirmation boundaries, language matching, and markdown-link requirements.

Use `scripts/update-ha-best-practices.sh` to refresh this snapshot deliberately.
