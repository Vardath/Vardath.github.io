"""Pilot must refuse contaminated splits before allocating output or training."""
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from capability.run_dialogue_pilot import run_pipeline


class PilotContaminationTests(unittest.TestCase):
    def test_near_duplicate_failure_prevents_training(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            manifest = root / "manifest.json"
            manifest.write_text(json.dumps({"source_id": "fixture", "revision": "test"}), encoding="utf-8")
            output = root / "checkpoint_output"
            with patch("capability.run_dialogue_pilot.verify_split_files") as verify, \
                 patch("capability.run_dialogue_pilot.audit_near_duplicates",
                       return_value={"passed": False, "findings": [{"a": "train:1", "b": "test:1"}]}) as audit:
                with self.assertRaisesRegex(ValueError, "near-duplicates"):
                    run_pipeline(manifest, root, output, duplicate_threshold=0.75)
                verify.assert_called_once()
                audit.assert_called_once_with(root, threshold=0.75)
                self.assertFalse(output.exists())


if __name__ == "__main__":
    unittest.main()
