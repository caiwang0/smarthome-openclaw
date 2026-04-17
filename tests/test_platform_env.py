import os
import subprocess
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
HELPER = REPO_ROOT / "scripts" / "platform-env.sh"


class PlatformEnvTests(unittest.TestCase):
    def run_helper(self, snippet: str, extra_env: dict[str, str] | None = None) -> subprocess.CompletedProcess[str]:
        env = os.environ.copy()
        if extra_env:
            env.update(extra_env)
        return subprocess.run(
            ["bash", "-lc", f". '{HELPER}'; {snippet}"],
            capture_output=True,
            text=True,
            env=env,
        )

    def test_detect_platform_maps_supported_and_unsupported_hosts(self) -> None:
        cases = {
            "Linux": "linux",
            "Darwin": "macos",
            "FreeBSD": "unsupported",
        }

        for reported_uname, expected in cases.items():
            with self.subTest(reported_uname=reported_uname):
                proc = self.run_helper(
                    "smarthub_detect_platform",
                    {"SMARTHUB_TEST_UNAME": reported_uname},
                )
                self.assertEqual(proc.returncode, 0, proc.stderr)
                self.assertEqual(proc.stdout.strip(), expected)

    def test_compose_files_and_default_origin_follow_platform(self) -> None:
        linux = self.run_helper(
            "printf '%s\\n' \"$(smarthub_compose_files)\"; smarthub_default_ha_origin",
            {"SMARTHUB_TEST_UNAME": "Linux", "HA_PORT": "8123"},
        )
        self.assertEqual(linux.returncode, 0, linux.stderr)
        self.assertEqual(
            linux.stdout.strip().splitlines(),
            [
                "docker-compose.yml docker-compose.linux.yml",
                "http://homeassistant.local:8123",
            ],
        )

        macos = self.run_helper(
            "printf '%s\\n' \"$(smarthub_compose_files)\"; smarthub_default_ha_origin",
            {"SMARTHUB_TEST_UNAME": "Darwin", "HA_PORT": "9123"},
        )
        self.assertEqual(macos.returncode, 0, macos.stderr)
        self.assertEqual(
            macos.stdout.strip().splitlines(),
            [
                "docker-compose.yml docker-compose.macos.yml",
                "http://localhost:9123",
            ],
        )

    def test_port_probe_reports_bound_and_unbound_ports(self) -> None:
        busy = self.run_helper(
            "smarthub_port_in_use 8123",
            {"SMARTHUB_TEST_BUSY_PORTS": "8123"},
        )
        self.assertEqual(busy.returncode, 0, busy.stderr)

        free = self.run_helper("smarthub_port_in_use 8124")
        self.assertNotEqual(free.returncode, 0, free.stderr)


if __name__ == "__main__":
    unittest.main()
