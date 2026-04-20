import re
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]


class AutomationDocsTests(unittest.TestCase):
    def test_best_practices_pack_is_vendored_and_has_provenance(self) -> None:
        pack_dir = REPO_ROOT / "tools" / "ha-best-practices"
        provenance = pack_dir / "README.md"
        update_script = REPO_ROOT / "scripts" / "update-ha-best-practices.sh"

        self.assertTrue(pack_dir.exists(), "missing vendored best-practices pack")
        self.assertTrue(provenance.exists(), "missing vendored pack provenance README")

        provenance_text = provenance.read_text()
        self.assertIn("https://github.com/homeassistant-ai/skills", provenance_text)
        self.assertRegex(provenance_text, r"Pinned commit:\s*`[0-9a-f]{7,40}`")

        self.assertTrue(update_script.exists(), "missing best-practices refresh script")
        script_text = update_script.read_text()
        self.assertIn("homeassistant-ai/skills", script_text)
        self.assertIn("git clone", script_text)
        self.assertIn("Pinned commit", script_text)


if __name__ == "__main__":
    unittest.main()
