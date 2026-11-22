"""Regression checks for bounded capacity controls; no corpus or pretrained weights."""
import unittest
from unittest.mock import patch
from pathlib import Path
from capability.run_dialogue_pilot import run_pipeline


class CapacityControlsTest(unittest.TestCase):
    def test_rejects_incompatible_heads_before_creating_outputs(self):
        with patch("capability.run_dialogue_pilot.verify_split_files", return_value=None):
            # Invalid manifest path is intentionally checked first, so use a temporary manifest.
            import tempfile
            import json
            with tempfile.TemporaryDirectory() as tmp:
                root = Path(tmp)
                manifest = root / "manifest.json"
                manifest.write_text(json.dumps({"source_id": "synthetic"}), encoding="utf-8")
                with self.assertRaisesRegex(ValueError, "Invalid model capacity controls"):
                    run_pipeline(manifest, root, root / "out",
                                 width=65, heads=4)
                self.assertFalse((root / "out").exists())


if __name__ == "__main__":
    unittest.main()
