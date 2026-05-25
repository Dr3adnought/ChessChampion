import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from game.settings import AppSettings, load_settings, save_settings


class SettingsUnitTests(unittest.TestCase):
    def test_load_defaults_when_file_missing(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            with patch.dict("os.environ", {"CHESSCHAMPION_DATA_DIR": temp_dir}, clear=False):
                settings = load_settings()
                self.assertFalse(settings.network_enabled)
                self.assertEqual(settings.network_server_url, "ws://localhost:8765")

    def test_save_and_load_round_trip(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            with patch.dict("os.environ", {"CHESSCHAMPION_DATA_DIR": temp_dir}, clear=False):
                saved_path = save_settings(
                    AppSettings(
                        network_enabled=True,
                        network_server_url="wss://example.test/ws",
                        network_heartbeat_interval_ms=2000,
                        reconnect_timeout_seconds=45,
                        debug_network_logging=True,
                    )
                )
                self.assertTrue(Path(saved_path).exists())

                loaded = load_settings()
                self.assertTrue(loaded.network_enabled)
                self.assertEqual(loaded.network_server_url, "wss://example.test/ws")
                self.assertEqual(loaded.network_heartbeat_interval_ms, 2000)
                self.assertEqual(loaded.reconnect_timeout_seconds, 45)
                self.assertTrue(loaded.debug_network_logging)


if __name__ == "__main__":
    unittest.main()
