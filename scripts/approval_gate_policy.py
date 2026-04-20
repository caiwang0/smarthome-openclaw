import json
import re
from dataclasses import dataclass
from pathlib import Path


GATED_TOOLS = frozenset({
    "mcp__ha-mcp__ha_config_set_automation",
    "mcp__ha-mcp__ha_config_remove_automation",
    "mcp__ha-mcp__ha_config_set_script",
    "mcp__ha-mcp__ha_config_remove_script",
    "mcp__ha-mcp__ha_config_entries_flow",
    "mcp__ha-mcp__ha_delete_config_entry",
    "mcp__ha-mcp__ha_set_integration_enabled",
    "mcp__ha-mcp__ha_remove_device",
    "mcp__ha-mcp__ha_update_device",
    "mcp__ha-mcp__ha_rename_entity",
    "mcp__ha-mcp__ha_restart",
    "mcp__ha-mcp__ha_reload_core",
    "mcp__ha-mcp__ha_backup_restore",
    "mcp__ha-mcp__ha_hacs_download",
    "mcp__ha-mcp__ha_hacs_add_repository",
})

CONFIRMATION_PATTERNS = [
    r"^\s*(yes|yeah|yep|yup|y|ok|okay|sure|confirm|confirmed|proceed|do it|go ahead|alright|approved?)\b",
    r"^\s*(是|是的|好|好的|确认|確認|继续|繼續|可以|行|同意|批准)",
    r"^\s*(sí|si|claro|adelante|confirmo|de acuerdo)\b",
    r"^\s*(oui|d'accord|continuez|confirmé|allez-y)\b",
    r"^\s*(ja|bestätigt|weiter|mach)\b",
    r"^\s*(はい|承認|進めて|了解)",
    r"^\s*(ya|boleh|setuju|teruskan)\b",
]


@dataclass(frozen=True)
class GateDecision:
    decision: str
    reason: str


def extract_last_user_text(transcript_path: str) -> str | None:
    """Return the text of the most recent user message in the transcript, or None."""
    try:
        path = Path(transcript_path)
        if not path.is_file():
            return None
        with path.open("r", encoding="utf-8") as handle:
            lines = handle.readlines()
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
    if len(normalized) > 80:
        return False
    return any(re.search(pattern, normalized, re.IGNORECASE) for pattern in CONFIRMATION_PATTERNS)


def is_follow_up_config_flow(payload: dict) -> bool:
    """Allow config-flow calls that are already inside an existing flow."""
    if payload.get("tool_name") != "mcp__ha-mcp__ha_config_entries_flow":
        return False

    tool_input = payload.get("tool_input")
    if not isinstance(tool_input, dict):
        return False

    return "flow_id" in tool_input


def build_denial_reason(tool_name: str) -> str:
    tool_short = tool_name.replace("mcp__ha-mcp__", "")
    return (
        f"Approval gate: '{tool_short}' requires explicit user confirmation "
        "before a persistent configuration action can proceed. The last user "
        "message was not a clear affirmative ('yes', '好', 'confirm', etc.).\n\n"
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


def evaluate_payload(payload: object) -> GateDecision | None:
    """Return a deny decision when policy blocks the payload, else None."""
    if not isinstance(payload, dict):
        return None

    if is_follow_up_config_flow(payload):
        return None

    tool_name = payload.get("tool_name", "")
    if tool_name not in GATED_TOOLS:
        return None

    transcript_path = payload.get("transcript_path", "")
    last_user_text = extract_last_user_text(str(transcript_path))
    if last_user_text and is_confirmation(last_user_text):
        return None

    return GateDecision(decision="deny", reason=build_denial_reason(str(tool_name)))
