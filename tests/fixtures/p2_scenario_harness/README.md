# P2 Scenario Harness Fixtures

Each scenario fixture is a JSON object with four required top-level fields:

- `name`: stable scenario identifier used by the harness and validation report
- `docs`: ordered list of repo-local markdown files the scenario reads
- `tool_runs`: ordered list of tool invocations and transcript snippets to evaluate
- `expect`: expected outcome for the scenario

The harness keeps the schema intentionally small and deterministic. It does not
load network data, talk to a live Home Assistant instance, or infer missing
defaults.

## Example

```json
{
  "name": "confirmation-boundary",
  "docs": ["tools/integrations/_guide.md"],
  "tool_runs": [
    {
      "tool_name": "mcp__ha-mcp__ha_config_entries_flow",
      "tool_input": {"handler": "hue"},
      "transcript": "please continue"
    }
  ],
  "expect": {
    "decision": "deny",
    "reason_contains": "explicit confirmation"
  }
}
```

The same shape works for positive and negative paths. A confirmed path uses a
transcript such as `yes`; a denied path uses a transcript such as `please
continue`.
