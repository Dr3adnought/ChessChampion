import tempfile
import unittest
from pathlib import Path

from game.save_load import store
from tests.test_schema_validation_unit import make_valid_payload


class StoreLayerUnitTests(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self._original_save_dir = store.SAVE_GAMES_DIR
        self._original_index_file = store.INDEX_FILE

        store.SAVE_GAMES_DIR = Path(self.temp_dir.name)
        store.INDEX_FILE = store.SAVE_GAMES_DIR / "index.json"
        store.ensure_save_directory()

    def tearDown(self):
        store.SAVE_GAMES_DIR = self._original_save_dir
        store.INDEX_FILE = self._original_index_file
        self.temp_dir.cleanup()

    def test_save_payload_writes_file_and_index(self):
        payload = make_valid_payload()
        payload["save_id"] = "store-unit-01"

        summary = store.save_payload(payload, file_name="store-unit-01.json")

        self.assertEqual(summary["file_name"], "store-unit-01.json")
        self.assertTrue((store.SAVE_GAMES_DIR / "store-unit-01.json").exists())

        saves = store.list_saves()
        self.assertEqual(len(saves), 1)
        self.assertEqual(saves[0]["save_id"], "store-unit-01")

    def test_list_saves_skips_stale_index_entries(self):
        index_payload = {
            "schema_version": store.SCHEMA_VERSION,
            "saves": [
                {
                    "save_id": "ghost-save",
                    "file_name": "missing.json",
                    "source": "manual",
                    "created_at_utc": "2026-05-25T12:00:00Z",
                    "updated_at_utc": "2026-05-25T12:01:00Z",
                }
            ],
        }
        store.write_json(store.INDEX_FILE, index_payload)

        saves, warnings = store.list_saves(include_warnings=True)

        self.assertEqual(saves, [])
        self.assertGreaterEqual(len(warnings), 1)

    def test_delete_save_removes_file_and_index_entry(self):
        payload = make_valid_payload()
        payload["save_id"] = "store-unit-delete"
        store.save_payload(payload, file_name="store-unit-delete.json")

        deleted = store.delete_save("store-unit-delete.json")

        self.assertTrue(deleted)
        self.assertFalse((store.SAVE_GAMES_DIR / "store-unit-delete.json").exists())
        self.assertEqual(store.list_saves(), [])


if __name__ == "__main__":
    unittest.main()
