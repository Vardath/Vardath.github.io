"""The v41 repair retest must never reuse same-size stale CPython bytecode."""
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from deepthort_local.development_cycle import isolated_verification_environment


class VerificationBytecodeTests(unittest.TestCase):
    def test_non_verification_commands_inherit_unmodified_process_environment(self):
        with tempfile.TemporaryDirectory() as tmp:
            argv = [sys.executable, '-m', 'unittest', 'discover']
            self.assertIsNone(isolated_verification_environment(['npm', 'test'], tmp, 7))
            self.assertIsNone(isolated_verification_environment(argv, tmp, None))
            self.assertIsNone(isolated_verification_environment(argv, tmp, 0))
            self.assertIsNone(isolated_verification_environment(argv, tmp, True))
            first = isolated_verification_environment(argv, tmp, 7)
            second = isolated_verification_environment(argv, tmp, 7)
            self.assertNotEqual(first['PYTHONPYCACHEPREFIX'], second['PYTHONPYCACHEPREFIX'])
            self.assertEqual(first.get('PATH'), os.environ.get('PATH'))
            self.assertEqual(first.get('PYTHONPATH'), os.environ.get('PYTHONPATH'))
            self.assertTrue(Path(first['PYTHONPYCACHEPREFIX']).parent.is_dir())

    def test_same_size_same_timestamp_repair_runs_fresh_python_sources(self):
        cmd = [sys.executable, '-m', 'unittest', 'discover']
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            project = root / 'game'
            project.mkdir()
            src = project / 'main.py'
            bad = 'def add(a, b):\n    return a - b\n'
            good = 'def add(a, b):\n    return a + b\n'
            self.assertEqual(len(bad.encode()), len(good.encode()))
            src.write_text(bad, encoding='utf-8')
            (project / 'test_main.py').write_text(
                'import unittest\nfrom main import add\n'
                'class TestAdding(unittest.TestCase):\n'
                '    def test_add(self):\n        self.assertEqual(add(2, 3), 5)\n',
                encoding='utf-8')
            original_time = src.stat().st_mtime_ns
            def run():
                env = isolated_verification_environment(cmd, root / 'state', 44)
                return subprocess.run(cmd, cwd=project, env=env, stdout=subprocess.PIPE,
                                      stderr=subprocess.STDOUT, text=True,
                                      timeout=45, check=False)
            failed = run()
            self.assertNotEqual(failed.returncode, 0, failed.stdout)
            self.assertIn('FAILED', failed.stdout)
            src.write_text(good, encoding='utf-8')
            os.utime(src, ns=(original_time, original_time))
            self.assertEqual(src.stat().st_mtime_ns, original_time)
            passed = run()
            self.assertEqual(passed.returncode, 0, passed.stdout)
            self.assertIn('OK', passed.stdout)
            self.assertEqual(src.read_text(encoding='utf-8'), good)


if __name__ == '__main__':
    unittest.main()
