import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]


class MacOSVmDocsTests(unittest.TestCase):
    def test_macos_support_is_vm_only(self) -> None:
        readme = (REPO_ROOT / "README.md").read_text()
        setup = (REPO_ROOT / "tools" / "setup.md").read_text()
        errors = (REPO_ROOT / "tools" / "_errors.md").read_text()

        self.assertIn("official Home Assistant VM path", readme)
        self.assertIn("Intel or Apple Silicon", readme)
        self.assertIn("haos_ova", readme)
        self.assertIn("haos_generic-aarch64", readme)
        self.assertIn("Native macOS Docker Desktop is not supported", readme)
        self.assertIn("`install.sh` on the macOS host", readme)
        self.assertIn("Home Assistant OS VM", readme)
        self.assertIn("creates the initial Home Assistant admin account", readme)
        self.assertIn("long-lived access token", readme)
        self.assertNotIn("provisions a Linux VM", readme)

        self.assertIn("official Home Assistant OS VM", setup)
        self.assertIn("Intel vs Apple Silicon", setup)
        self.assertIn("syncs the generated token into `.env`", setup)
        self.assertIn("VirtualBox", errors)
        self.assertIn("Home Assistant OS VM", errors)


if __name__ == "__main__":
    unittest.main()
