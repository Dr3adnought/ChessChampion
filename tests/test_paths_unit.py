import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from game import paths


class PathsUnitTests(unittest.TestCase):
    def test_assets_dir_points_to_repo_assets_in_source_mode(self):
        assets_dir = paths.get_assets_dir()
        self.assertTrue(str(assets_dir).endswith("assets"))

    def test_user_data_override_is_respected(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            with patch.dict("os.environ", {"CHESSCHAMPION_DATA_DIR": temp_dir}, clear=False):
                resolved = paths.get_user_data_dir()
                self.assertEqual(resolved, Path(temp_dir))

    def test_ensure_user_data_layout_creates_expected_directories(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            with patch.dict("os.environ", {"CHESSCHAMPION_DATA_DIR": temp_dir}, clear=False):
                root = paths.ensure_user_data_layout()
                self.assertTrue(root.exists())
                self.assertTrue((root / "saved_games").exists())
                self.assertTrue((root / "logs").exists())


if __name__ == "__main__":
    unittest.main()
