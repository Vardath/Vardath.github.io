import tempfile
import unittest
from pathlib import Path
from deepthort_local.repository_index import RepositoryIndex,IndexCancelled

class RepositoryTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup)
        base=Path(self.tmp.name);self.root=base/'project';self.root.mkdir()
        self.db=base/'index.sqlite'
        self.index=RepositoryIndex(self.db)
        (self.root/'economy.py').write_text('class Market:\n    def buy(self, amount, price):\n        return amount * price\n')
        (self.root/'main.py').write_text('from economy import Market\n')
    def test_incremental_persistent_and_dependency_rank(self):
        self.assertEqual(self.index.refresh(self.root)['files'],2)
        self.assertEqual(RepositoryIndex(self.db).refresh(self.root)['reused'],2)
        found=self.index.search(self.root,'unrelated',focus='main.py',omit=['main.py'])
        self.assertEqual(found[0]['path'],'economy.py')
        self.assertIn('Market.buy',[x['name'] for x in found])
        self.assertIn('def buy(self, amount, price)',self.index.context(self.root,'Market buy',budget=600))
    def test_stale_changed_deleted_and_project_scope(self):
        self.index.refresh(self.root)
        (self.root/'economy.py').write_text('def sell(): pass\n')
        self.assertEqual(self.index.search(self.root,'Market buy'),[])
        self.index.refresh(self.root)
        self.assertEqual(self.index.search(self.root,'sell')[0]['name'],'sell')
        (self.root/'economy.py').unlink()
        self.index.refresh(self.root)
        self.assertEqual(self.index.search(self.root,'sell'),[])
        other=self.root.parent/'other';other.mkdir()
        self.assertEqual(self.index.search(other,'Market'),[])
    def test_exclusions_and_cancelled_publication(self):
        (self.root/'secrets.py').write_text('def secret(): pass\n')
        (self.root/'hidden.py').write_text('def hidden(): pass\n')
        (self.root/'node_modules').mkdir()
        (self.root/'node_modules'/'dep.py').write_text('def secret(): pass\n')
        self.index.refresh(self.root,exclude=['hidden.py'])
        self.assertEqual(self.index.search(self.root,'secret hidden'),[])
        with self.assertRaises(IndexCancelled):self.index.refresh(self.root,cancelled=lambda:True)
        self.assertTrue(self.index.search(self.root,'Market'))
        self.assertEqual(self.index.search(self.root,'Market',exclude=['economy.py']),[])
    def test_invalid_python_and_link(self):
        (self.root/'broken.py').write_text('def broken(')
        outside=self.root.parent/'outside.py';outside.write_text('def foreign_function(): pass\n')
        try:(self.root/'link.py').symlink_to(outside)
        except OSError:pass
        self.index.refresh(self.root)
        self.assertEqual(self.index.search(self.root,'broken foreign_function'),[])
if __name__=='__main__':unittest.main()
