#!/usr/bin/env python3
"""
PreToolUse approval gate for destructive ha-mcp tools.

Runs as a Claude Code PreToolUse hook. Blocks destructive ha-mcp tool calls
unless the most recent user message is an explicit affirmative confirmation.

Reads hook payload from stdin, writes a permissionDecision JSON to stdout.

Why this exists:
  The LLM-based rules in CLAUDE.md ("always confirm before destructive actions")
  are inconsistent — the bot sometimes skips confirmation. ACPX runs Claude Code
  with permissionMode=approve-all, which bypasses Claude Code's built-in
  permission dialogs. This hook is a deterministic gate that fires regardless
  of permission mode.

Scope:
  Only gates tools that create/modify/delete persistent configuration
  (automations, scripts, integrations, devices, backups, restarts). Does NOT
  gate device control (ha_call_service, ha_bulk_control) — turning on a
  light or setting AC temperature executes immediately.
"""

import json
import re
import sys
from pathlib import Path

# Tools that require explicit user confirmation before executing.
# Keep this list aligned with the "Confirmation required" rules in CLAUDE.md.
GATED_TOOLS = frozenset({
    # Automations
    "mcp__ha-mcp__ha_config_set_automation",
    "mcp__ha-mcp__ha_config_remove_automation",
    # Scripts
    "mcp__ha-mcp__ha_config_set_script",
    "mcp__ha-mcp__ha_config_remove_script",
    # Integrations
    "mcp__ha-mcp__ha_delete_config_entry",
    "mcp__ha-mcp__ha_set_integration_enabled",
    # Devices
    "mcp__ha-mcp__ha_remove_device",
    "mcp__ha-mcp__ha_update_device",
    "mcp__ha-mcp__ha_rename_entity",
    # System operations
    "mcp__ha-mcp__ha_restart",
    "mcp__ha-mcp__ha_reload_core",
    "mcp__ha-mcp__ha_backup_restore",
    # HACS (installs third-party code)
    "mcp__ha-mcp__ha_hacs_download",
    "mcp__ha-mcp__ha_hacs_add_repository",
})

# Affirmative patterns — the last user message must match one of these
# for the gated tool call to proceed. Case-insensitive, anchored to start.
CONFIRMATION_PATTERNS = [
    # English
    r"^\s*(yes|yeah|yep|yup|y|ok|okay|sure|confirm|confirmed|proceed|do it|go ahead|alright|approved?)\b",
    # Chinese (simplified + traditional)
    r"^\s*(是|是的|好|好的|确认|確認|继续|繼續|可以|行|同意|批准)",
    # Spanish
    r"^\s*(sí|si|claro|adelante|confirmo|de acuerdo)\b",
    # French
    r"^\s*(oui|d'accord|continuez|confirmé|allez-y)\b",
    # German
    r"^\s*(ja|bestätigt|weiter|mach)\b",
    # Japanese
    r"^\s*(はい|承認|進めて|了解)",
    # Malay/Indonesian
    r"^\s*(ya|boleh|setuju|teruskan)\b",
]


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


def extract_last_user_text(transcript_path: str) -> str | None:
    """Return the text of the most recent user message in the transcript, or None."""
    try:
        path = Path(transcript_path)
        if not path.is_file():
            return None
        with path.open("r", encoding="utf-8") as f:
            lines = f.readlines()
    except Exception:
        return None

    for line in reversed(lines):
        line = line.strip()
        if not line:
            continue
        try:
            entry = json.loads(line)
        except json.JSONDecodeError:
            continue

        if entry.get("type") != "user":
            continue

        message = entry.get("message", {})
        content = message.get("content")

        if isinstance(content, str):
            return content
        if isinstance(content, list):
            texts = []
            for part in content:
                if not isinstance(part, dict):
                    continue
                # Skip tool_result parts — those are not real user messages
                if part.get("type") == "tool_result":
                    return None
                if part.get("type") == "text":
                    texts.append(part.get("text", ""))
            if texts:
                return " ".join(texts)
        return None

    return None


def is_confirmation(text: str) -> bool:
    normalized = text.strip().lower()
    # Reject overly long messages — a real confirmation is short
    if len(normalized) > 80:
        return False
    return any(re.search(pat, normalized, re.IGNORECASE) for pat in CONFIRMATION_PATTERNS)


def main() -> None:
    try:
        payload = json.load(sys.stdin)
    except json.JSONDecodeError:
        # Malformed input — fail open (allow), since blocking everything breaks
        # the bot for non-destructive calls if the harness changes format.
        sys.exit(0)

    tool_name = payload.get("tool_name", "")
    if tool_name not in GATED_TOOLS:
        # Not a gated tool — allow silently
        sys.exit(0)

    transcript_path = payload.get("transcript_path", "")
    last_user_text = extract_last_user_text(transcript_path)

    if last_user_text and is_confirmation(last_user_text):
        # User explicitly confirmed — allow
        sys.exit(0)

    # Block with instructions for the LLM
    tool_short = tool_name.replace("mcp__ha-mcp__", "")
    reason = (
        f"Approval gate: '{tool_short}' is a destructive action and requires "
        "explicit user confirmation. The last user message was not a clear "
        "affirmative ('yes', '好', 'confirm', etc.).\n\n"
        "REQUIRED STEPS before retrying:\n"
        "1. Send the user a concise summary of what this action will do "
        "(name, affected entities, schedule/triggers if applicable).\n"
        "2. End the message with: \"Reply yes to confirm or no to cancel.\"\n"
        "3. Wait for the user's next message.\n"
        "4. Only retry this tool AFTER the user has replied with an "
        "affirmative (yes/好/ok/confirm).\n\n"
        "Do not paraphrase the summary — include the exact details so the "
        "user knows what they're approving."
    )
    emit_decision("deny", reason)


if __name__ == "__main__":
    main()
