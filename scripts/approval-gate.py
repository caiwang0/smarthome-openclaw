#!/usr/bin/env python3
"""
PreToolUse approval gate for persistent ha-mcp tools.

Runs as a Claude Code PreToolUse hook. Blocks persistent ha-mcp tool calls
unless the most recent user message is an explicit affirmative confirmation.

Reads hook payload from stdin, writes a permissionDecision JSON to stdout.

Why this exists:
  The LLM-based rules in CLAUDE.md ("always confirm before persistent actions")
  are inconsistent — the bot sometimes skips confirmation. ACPX runs Claude Code
  with permissionMode=approve-all, which bypasses Claude Code's built-in
  permission dialogs. This hook is a deterministic gate that fires regardless
  of permission mode.

Scope:
  Gates tools that create/modify/delete persistent configuration
  (automations, scripts, integrations, config flows, devices, backups,
  restarts). Does NOT gate device control (ha_call_service, ha_bulk_control)
  — turning on a light or setting AC temperature executes immediately.
"""

import json
import sys
from approval_gate_policy import evaluate_payload


def emit_decision(decision: str, reason: str) -> None:
    """Emit a structured PreToolUse decision and exit 0."""
    output = {
        "hookSpecificOutput": {
            "hookEventName": "PreToolUse",
            "permissionDecision": decision,
            "permissionDecisionReason": reason,
        }
    }
    print(json.dumps(output))
    sys.exit(0)


def main() -> None:
    try:
        payload = json.load(sys.stdin)
    except json.JSONDecodeError:
        # Malformed input — fail open (allow), since blocking everything breaks
        # the bot for non-destructive calls if the harness changes format.
        sys.exit(0)

    decision = evaluate_payload(payload)
    if decision is None:
        sys.exit(0)
    emit_decision(decision.decision, decision.reason)


if __name__ == "__main__":
    main()
