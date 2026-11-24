import tempfile
import unittest
from pathlib import Path
from deepthort_local.repository_index import RepositoryIndex

class ImpactTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup)
        base=Path(self.tmp.name);self.root=base/'project';self.root.mkdir()
        self.index=RepositoryIndex(base/'index.sqlite')
        (self.root/'economy.py').write_text('def buy(amount, price):\n    return amount * price\n')
        (self.root/'market.py').write_text('from economy import buy\n\ndef trade():\n    return buy(2, 5)\n')
        (self.root/'main.py').write_text('from market import trade\n\ndef run():\n    return trade()\n')
        self.index.refresh(self.root)
    def test_reverse_transitive_impact(self):
        impact=self.index.impact(self.root,['economy.py'])
        self.assertEqual(impact['dependents'],['main.py','market.py'])
        self.assertEqual(set(impact['source_hashes']),{'economy.py','market.py','main.py'})
        self.assertEqual(self.index.references(self.root,'buy')[0]['path'],'market.py')
    def test_stale_dependency_not_used(self):
        (self.root/'market.py').write_text('def trade(): return 0\n')
        self.assertEqual(self.index.impact(self.root,['economy.py'])['dependents'],[])
        self.assertEqual(self.index.references(self.root,'buy'),[])
    def test_excerpts_are_exact_and_rechecked(self):
        row=self.index.search(self.root,'buy',omit=['market.py'])[0]
        self.assertEqual(self.index.excerpt(self.root,row),'def buy(amount, price):\n    return amount * price')
        self.assertIn('return amount * price',self.index.context(self.root,'buy',omit=['market.py'],budget=800))
        (self.root/'economy.py').write_text('def buy(amount, price): return 0\n')
        with self.assertRaises(ValueError):self.index.excerpt(self.root,row)
    def test_relative_import_and_exclusion(self):
        pkg=self.root/'pkg';pkg.mkdir()
        (pkg/'__init__.py').write_text('')
        (pkg/'provider.py').write_text('def calculate(): return 1\n')
        (pkg/'consumer.py').write_text('from .provider import calculate\n')
        self.index.refresh(self.root)
        self.assertEqual(self.index.impact(self.root,['pkg/provider.py'])['dependents'],['pkg/consumer.py'])
        self.assertEqual(self.index.impact(self.root,['pkg/provider.py'],exclude=['pkg/consumer.py'])['dependents'],[])
if __name__=='__main__':unittest.main()
