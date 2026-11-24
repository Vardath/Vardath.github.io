import tempfile
import unittest
from pathlib import Path
from deepthort_local.regression_guard import affected_paths,capture,stable

class RegressionGuardTests(unittest.TestCase):
    def test_transitive_dependents_including_tests(self):
        master=[{'path':'economy.py','description':'Economy'},
                {'path':'trade.py','description':'Trade; depends-on: economy.py'},
                {'path':'test_trade.py','description':'Tests; depends-on: trade.py'},
                {'path':'graphics.py','description':'Graphics'}]
        self.assertEqual(affected_paths(master,['economy.py']),
                         ['economy.py','test_trade.py','trade.py'])

    def test_source_change_invalidates_test_evidence(self):
        with tempfile.TemporaryDirectory() as t:
            path=Path(t)/'game.py'
            path.write_bytes(b'initial')
            scope={'project':t,'protected':['game.py']}
            before=capture(scope)
            self.assertTrue(stable(scope,before,capture(scope)))
            path.write_bytes(b'changed')
            self.assertFalse(stable(scope,before,capture(scope)))
            self.assertFalse(stable(scope,before,before))

if __name__=='__main__':unittest.main()
