import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]


class SetupDocsTests(unittest.TestCase):
    def test_setup_docs_handle_seeded_and_manual_readiness_paths(self) -> None:
        setup = (REPO_ROOT / "tools" / "setup.md").read_text()
        errors = (REPO_ROOT / "tools" / "_errors.md").read_text()
        claude = (REPO_ROOT / "CLAUDE.md").read_text()
        readme = (REPO_ROOT / "README.md").read_text()

        self.assertIn("/api/config", setup)
        self.assertIn("your_long_lived_access_token_here", setup)
        self.assertIn("skip to Step 8", setup)

        self.assertIn("/api/config", errors)
        self.assertIn("your_long_lived_access_token_here", errors)

        self.assertIn("/api/config", claude)
        self.assertIn("Authorization: Bearer ${HA_TOKEN}", claude)

        self.assertIn("/api/config", readme)


if __name__ == "__main__":
    unittest.main()
