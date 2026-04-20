#!/usr/bin/env bash
set -euo pipefail

# Pinned commit for tools/ha-best-practices/.
PINNED_COMMIT="e503410aa2c412dd27579562f194ee6614314dd8"
UPSTREAM_REPO="https://github.com/homeassistant-ai/skills.git"
UPSTREAM_PATH="skills/home-assistant-best-practices"

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
TARGET_DIR="${REPO_ROOT}/tools/ha-best-practices"
TMP_DIR="$(mktemp -d)"

cleanup() {
  rm -rf "${TMP_DIR}"
}
trap cleanup EXIT

git clone "${UPSTREAM_REPO}" "${TMP_DIR}/repo" >/dev/null 2>&1
git -C "${TMP_DIR}/repo" checkout "${PINNED_COMMIT}" >/dev/null 2>&1

rm -rf "${TARGET_DIR}/references" "${TARGET_DIR}/SKILL.md"
cp "${TMP_DIR}/repo/${UPSTREAM_PATH}/SKILL.md" "${TARGET_DIR}/SKILL.md"
cp -R "${TMP_DIR}/repo/${UPSTREAM_PATH}/references" "${TARGET_DIR}/references"

cat > "${TARGET_DIR}/README.md" <<EOF
# Home Assistant Best Practices Snapshot

- Upstream repository: <https://github.com/homeassistant-ai/skills>
- Vendored skill path: \`skills/home-assistant-best-practices\`
- Pinned commit: \`${PINNED_COMMIT}\`
- Vendored on: \`$(date +%F)\`
- Included files: upstream \`SKILL.md\` plus the \`references/\` directory used by that skill

This directory is a committed offline snapshot of the upstream \`home-assistant-best-practices\` pack.

Local routing rules for this repo:

- Load this pack only when \`tools/automations/_guide.md\` reaches Step 4, "Draft the automation JSON".
- Treat the pack as advisory Home Assistant guidance for automation structure, helpers, refactoring safety, and domain-specific gotchas.
- \`CLAUDE.md\` remains authoritative for SmartHub-specific user interaction rules such as confirmation boundaries, language matching, and markdown-link requirements.

Use \`scripts/update-ha-best-practices.sh\` to refresh this snapshot deliberately.
EOF

echo "Synced tools/ha-best-practices at pinned commit ${PINNED_COMMIT}"
