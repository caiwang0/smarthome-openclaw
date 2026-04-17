import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]


class MacOSSupportDocsTests(unittest.TestCase):
    def test_readme_defines_native_macos_target_and_boundaries(self) -> None:
        readme = (REPO_ROOT / "README.md").read_text().lower()

        self.assertIn("native macos docker desktop", readme)
        self.assertIn("mainstream smarthub flow through docker desktop", readme)
        self.assertIn("linux vm + smarthub", readme)
        self.assertIn("home assistant os in a vm", readme)
        self.assertIn("bluetooth", readme)
        self.assertIn("usb radios", readme)
        self.assertIn("low-level networking", readme)
        self.assertIn("while the mac remains on the home lan", readme)

    def test_vm_fallback_guidance_matches_the_official_macos_guide(self) -> None:
        combined = "\n".join(
            (
                (REPO_ROOT / "README.md").read_text(),
                (REPO_ROOT / "tools" / "setup.md").read_text(),
                (REPO_ROOT / "tools" / "_errors.md").read_text(),
            )
        ).lower()

        self.assertIn("virtualbox", combined)
        self.assertIn("intel", combined)
        self.assertIn("apple silicon", combined)
        self.assertIn("2 gb ram", combined)
        self.assertIn("2 vcpus", combined)
        self.assertIn("efi", combined)
        self.assertIn("bridged adapter", combined)
        self.assertIn("utm", combined)
        self.assertIn("openclaw can guide parts of that vm setup", combined)
        self.assertIn("gui steps still require user action", combined)


if __name__ == "__main__":
    unittest.main()
