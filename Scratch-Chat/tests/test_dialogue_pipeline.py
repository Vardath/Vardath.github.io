"""Contract tests for the admitted dialogue SFT pipeline (no model training)."""
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from capability.run_dialogue_pilot import run_pipeline


class PipelineTests(unittest.TestCase):
    def test_rejects_missing_manifest_before_writing(self):
        with tempfile.TemporaryDirectory() as root:
            root = Path(root)
            with self.assertRaises(FileNotFoundError):
                run_pipeline(root / "missing.json", root / "splits", root / "out")
            self.assertFalse((root / "out").exists())

    def test_rejects_unapproved_source_before_training(self):
        with tempfile.TemporaryDirectory() as root:
            root = Path(root)
            (root / "manifest.json").write_text('{"decision":"pending"}', encoding="utf-8")
            with self.assertRaises(ValueError):
                run_pipeline(root / "manifest.json", root, root / "out")
            self.assertFalse((root / "out").exists())

    def test_refuses_overwrite_even_with_validated_manifest(self):
        with tempfile.TemporaryDirectory() as root:
            root = Path(root)
            (root / "manifest.json").write_text("{}", encoding="utf-8")
            output = root / "out"
            output.mkdir()
            (output / "original_sft.pt").write_text("preserve")
            with patch("capability.run_dialogue_pilot.verify_split_files", return_value=True):
                with self.assertRaises(FileExistsError):
                    run_pipeline(root / "manifest.json", root, output)
            self.assertEqual((output / "original_sft.pt").read_text(), "preserve")


if __name__ == "__main__":
    unittest.main()
