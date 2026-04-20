import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]


class IntegrationDocsTests(unittest.TestCase):
    def test_discovery_entrypoint_and_confirmation_boundary(self) -> None:
        discovery = (REPO_ROOT / "tools" / "integrations" / "_discovery.md").read_text().lower()
        guide = (REPO_ROOT / "tools" / "integrations" / "_guide.md").read_text()
        setup = (REPO_ROOT / "tools" / "setup.md").read_text()

        self.assertIn("read-only discovery", discovery)
        self.assertIn("passive-first", discovery)
        self.assertIn("ha_config_entries_get", discovery)
        self.assertIn("ha_search_entities", discovery)
        self.assertLess(discovery.index("ha_config_entries_get"), discovery.index("avahi-browse -atr"))
        self.assertLess(discovery.index("avahi-browse -atr"), discovery.index("ssdp"))
        self.assertLess(discovery.index("ssdp"), discovery.index("ip neigh"))
        self.assertLess(discovery.index("ip neigh"), discovery.index("arp-scan"))
        self.assertLess(discovery.index("arp-scan"), discovery.index("nmap"))
        self.assertIn("present the results as candidates", discovery)
        self.assertIn("explicit user confirmation before any config-flow start or add-device action", discovery)
        self.assertIn("selecting a discovered device candidate still requires explicit user confirmation before any add-device action", discovery)
        self.assertIn("do not start `ha_config_entries_flow` from this doc", discovery)

        self.assertIn("Discovery First", guide)
        self.assertIn("passive-first", guide)
        self.assertIn("explicitly confirms the candidate", guide)
        self.assertIn("explicit user confirmation before any add-device action", guide)
        self.assertIn("Start the flow only after explicit user confirmation", guide)

        self.assertIn("hand off into discovery via `tools/integrations/_discovery.md`", setup)
        self.assertIn("passive-first discovery entrypoint", setup)

    def test_fingerprint_corpus_schema_and_discovery_contract(self) -> None:
        discovery = (REPO_ROOT / "tools" / "integrations" / "_discovery.md").read_text().lower()
        fingerprint_dir = REPO_ROOT / "tools" / "integrations" / "fingerprints"
        fingerprint_files = [
            "xiaomi.md",
            "hue.md",
            "shelly.md",
            "esphome.md",
            "broadlink.md",
        ]
        required_fields = {
            "vendor:",
            "integration_domains:",
            "mac_ouis:",
            "mdns_service_types:",
            "ssdp_signatures:",
        }

        self.assertIn("tools/integrations/fingerprints/*.md", discovery)
        self.assertIn("integration_domains", discovery)
        self.assertIn("mac_ouis", discovery)
        self.assertIn("mdns_service_types", discovery)
        self.assertIn("ssdp_signatures", discovery)
        self.assertNotIn("do not broaden into fingerprint corpus files here; that comes later.", discovery)

        for filename in fingerprint_files:
            path = fingerprint_dir / filename
            self.assertTrue(path.exists(), f"missing fingerprint file: {filename}")
            fingerprint_text = path.read_text().lower()
            self.assertTrue(
                all(field in fingerprint_text for field in required_fields),
                f"fingerprint schema drift in {filename}",
            )

    def test_host_guest_browser_boundaries_are_explicit(self) -> None:
        guide = (REPO_ROOT / "tools" / "integrations" / "_guide.md").read_text()
        common = (REPO_ROOT / "tools" / "_common.md").read_text()

        self.assertIn("macOS host: do not run `hostname -I`", guide)
        self.assertIn("macOS host: do not run `systemctl --user`", guide)
        self.assertIn("macOS host: do not run `avahi-publish-address`", guide)
        self.assertIn("Linux guest: Home Assistant, Docker, Avahi", guide)
        self.assertIn("Linux guest: `hostname -I`", guide)
        self.assertIn("browser machine", guide)
        self.assertIn("Inside the Linux guest, run `HA_GUEST_IP=$(hostname -I | awk '{print $1}')`", guide)
        self.assertIn("On the browser machine", guide)

        self.assertIn("macOS host", common)
        self.assertIn("Linux guest", common)
        self.assertIn("browser machine", common)


if __name__ == "__main__":
    unittest.main()
