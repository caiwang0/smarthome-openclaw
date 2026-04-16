import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]


class RecoveryDocsTests(unittest.TestCase):
    def test_recovery_ladder_is_canonical_and_shared(self) -> None:
        errors = (REPO_ROOT / "tools" / "_errors.md").read_text().lower()
        ladder = errors.split("## recovery ladder", 1)[1]
        setup = (REPO_ROOT / "tools" / "setup.md").read_text().lower()
        guide = (REPO_ROOT / "tools" / "integrations" / "_guide.md").read_text().lower()
        claude = (REPO_ROOT / "CLAUDE.md").read_text().lower()

        self.assertIn("recovery ladder", errors)
        self.assertIn("probe", ladder)
        self.assertIn("inspect", ladder)
        self.assertIn("retry once", ladder)
        self.assertIn("restart transient services", ladder)
        self.assertIn("resume the checkpointed install", ladder)
        self.assertIn("escalate", ladder)
        self.assertLess(ladder.index("probe"), ladder.index("inspect"))
        self.assertLess(ladder.index("inspect"), ladder.index("retry once"))
        self.assertLess(ladder.index("retry once"), ladder.index("restart transient services"))
        self.assertLess(ladder.index("restart transient services"), ladder.index("resume the checkpointed install"))
        self.assertLess(ladder.index("resume the checkpointed install"), ladder.index("escalate"))
        self.assertIn("ask before deleting `ha-config`", ladder)
        self.assertIn("ask before replacing an existing token/account", ladder)
        self.assertIn("ask before making a config flow or oauth choice", ladder)

        self.assertIn("recovery ladder in `tools/_errors.md`", claude)
        self.assertIn("recovery ladder in `tools/_errors.md`", setup)
        self.assertIn("recovery ladder in `tools/_errors.md`", guide)


if __name__ == "__main__":
    unittest.main()
