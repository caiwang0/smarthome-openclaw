import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]


class MacOSVmDocsTests(unittest.TestCase):
    def test_macos_support_is_vm_only(self) -> None:
        readme = (REPO_ROOT / "README.md").read_text()
        setup = (REPO_ROOT / "tools" / "setup.md").read_text()
        errors = (REPO_ROOT / "tools" / "_errors.md").read_text()

        self.assertIn("Linux VM + SmartHub", readme)
        self.assertIn("Home Assistant OS in a VM", readme)
        self.assertIn("Native macOS Docker Desktop is not supported", readme)
        self.assertIn("`install.sh` on the macOS host", readme)
        self.assertIn("provisions a Linux VM", readme)
        self.assertNotIn("**macOS / Linux:**", readme)

        self.assertIn("macOS host", setup)
        self.assertIn("Linux guest", setup)
        self.assertIn("VirtualBox", errors)
        self.assertIn("Linux VM + SmartHub", errors)


if __name__ == "__main__":
    unittest.main()
