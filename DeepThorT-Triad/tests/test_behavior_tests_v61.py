import tempfile
import unittest
from pathlib import Path
from deepthort_local.behavior_tests import validate,guidance,repairable_steps
from deepthort_local.specification_guard import SpecificationRejected,inspect_proposal
from unittest.mock import Mock

GOOD='''import unittest
from economy import Market
class TestMarket(unittest.TestCase):
    def test_buy(self):
        market = Market(100)
        market.buy(5, 10)
        self.assertEqual(market.balance, 50)
'''
class BehaviorTests(unittest.TestCase):
    def test_python_meaningful_candidate_and_trivial_rejection(self):
        self.assertEqual(validate('tests/test_market.py',GOOD),['TestMarket.test_buy'])
        for assertion in ('self.assertTrue(True)','self.assertEqual(market.balance,market.balance)','pass','self.skipTest("later")'):
            with self.assertRaises(SpecificationRejected):
                validate('tests/test_market.py',GOOD.replace('self.assertEqual(market.balance, 50)',assertion))
        with self.assertRaises(SpecificationRejected):
            validate('tests/test_market.py',GOOD.replace('    def test_buy','    @unittest.skip("later")\n    def test_buy'))
    def test_gut_candidate(self):
        source='extends GutTest\nfunc test_trade():\n\tvar result = market.buy(5)\n\tassert_eq(result, 50)\n'
        self.assertEqual(validate('tests/test_trade.gd',source),['test_trade'])
        with self.assertRaises(SpecificationRejected):validate('tests/test_trade.gd',source.replace('assert_eq(result, 50)','assert_true(true)'))
    def test_guidance_from_real_approved_interfaces(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp)
            (root/'economy.py').write_text('class Market:\n    def buy(self, amount, price): pass\n')
            (root/'unapproved.py').write_text('def hidden_api(): pass\n')
            step={'path':'test_market.py','description':'Test trading; depends-on: economy.py'}
            steps=[step,{'path':'economy.py','description':'Implement market'}]
            prompt=guidance(root,step,steps)
            self.assertIn('def buy(self, amount, price)',prompt)
            self.assertNotIn('hidden_api',prompt)
            self.assertEqual(repairable_steps(steps),steps[1:])
    def test_sentinel_behavior_review_has_distinct_prompt(self):
        c=Mock();c._run.return_value='REJECT\nTest does not check balance'
        result=inspect_proposal(c,None,original='Purchasing deducts the cost from balance.',project='.',
             session='test',focus='market behavior',proposal=GOOD,kind='behavior_test')
        self.assertFalse(result['accepted'])
        self.assertIn('assertions distinguish required outcomes',c._run.call_args.kwargs['prompt'])
if __name__=='__main__':unittest.main()
