"""Verify capacity and provenance controls are available to real CLI users."""
import subprocess
import sys
import unittest
from pathlib import Path


class SFTCLIContractTests(unittest.TestCase):
    def test_help_exposes_architecture_and_reproducibility(self):
        project_root = Path(__file__).resolve().parent.parent
        result = subprocess.run(
            [sys.executable, "-m", "capability.dialogue_sft_train", "--help"],
            capture_output=True, text=True, timeout=30, cwd=project_root,
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        for flag in ("--width", "--layers", "--heads", "--context-size",
                     "--learning-rate", "--seed", "--resume"):
            with self.subTest(flag=flag):
                self.assertIn(flag, result.stdout)


if __name__ == "__main__":
    unittest.main()
