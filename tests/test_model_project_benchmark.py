import json
import unittest

from model_benchmark_project import SEED, check, judge


class ProjectBenchmarkTests(unittest.TestCase):
    def setUp(self):
        self.correct = dict(SEED)
        self.correct['dispatch.py'] = SEED['dispatch.py'].replace('return capacity', 'return stock')

    def test_seed_failure_and_dependency(self):
        self.assertIn('remaining', check(SEED, 0))
        self.assertIsNone(check(self.correct, 0))
        self.correct['dispatch.py'] = self.correct['dispatch.py'].replace('loadable(stock, capacity)', 'min(stock, capacity)')
        self.assertIn('using loadable', check(self.correct, 0))

    def test_amend_and_preserve_other_file(self):
        patch = {'stock.py': 'def loadable(stock, capacity): return min(max(0,stock-2),capacity)'}
        result = judge('amend', self.correct, json.dumps(patch))
        self.assertTrue(result['passed'], result)
        self.assertEqual(self.correct['dispatch.py'], result['files']['dispatch.py'])
        patch['dispatch.py'] = self.correct['dispatch.py']
        self.assertFalse(judge('amend', self.correct, json.dumps(patch))['passed'])

    def test_repair_and_reject_extra_code(self):
        patch = {'dispatch.py':self.correct['dispatch.py']}
        self.assertTrue(judge('repair', SEED, json.dumps(patch))['passed'])
        for source in ('import os\n'+patch['dispatch.py'], patch['dispatch.py'].replace('from stock', 'from unknown')):
            self.assertFalse(judge('repair', SEED, json.dumps({'dispatch.py':source}))['passed'])
        self.assertFalse(judge('repair', SEED, '{"dispatch.py":"x","dispatch.py":"y"}')['passed'])
