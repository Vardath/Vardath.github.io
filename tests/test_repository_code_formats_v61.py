import tempfile
import unittest
from pathlib import Path
from deepthort_local.repository_index import RepositoryIndex

class CodeFormatTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup)
        root=Path(self.tmp.name);self.root=root/'project';self.root.mkdir()
        self.index=RepositoryIndex(root/'index.sqlite')
    def put(self,path,text):
        f=self.root/path;f.parent.mkdir(parents=True,exist_ok=True);f.write_text(text)
    def test_js_ts_dependencies_and_declarations(self):
        self.put('lib/market.ts','export interface Trade { amount: number; }\nexport function buy(amount: number) { return amount; }\n')
        self.put('main.ts','import { buy } from "./lib/market";\nexport function run() { return buy(3); }\n')
        self.put('page.js','export { run } from "./main.ts";\n')
        self.index.refresh(self.root)
        self.assertEqual(self.index.impact(self.root,['lib/market.ts'])['dependents'],['main.ts','page.js'])
        self.assertTrue(any(x['name']=='buy' for x in self.index.search(self.root,'buy')))
        self.assertIn('main.ts',[r['path'] for r in self.index.references(self.root,'buy')])
    def test_ambiguous_and_outside_imports(self):
        self.put('market.ts','export function buy() {}')
        self.put('market.js','export function buy() {}')
        self.put('main.ts','import { buy } from "./market";\nimport x from "../outside";')
        self.index.refresh(self.root)
        self.assertEqual(self.index.impact(self.root,['market.ts'])['dependents'],[])
        (self.root/'market.js').unlink();self.index.refresh(self.root)
        self.assertEqual(self.index.impact(self.root,['market.ts'])['dependents'],['main.ts'])
    def test_comments_strings_and_templates_not_code(self):
        self.put('provider.js','export function buy() {}')
        self.put('fake.js','/*\nimport x from "./provider";\nexport function fake() {}\n*/\nconst text = "import x from ./provider";')
        self.put('template.js','const s = \x60export function fake() {}\x60;')
        self.index.refresh(self.root)
        self.assertEqual(self.index.impact(self.root,['provider.js'])['dependents'],[])
        self.assertFalse(any(x['name']=='fake' for x in self.index.search(self.root,'fake')))
    def test_cs_namespaces_and_methods(self):
        self.put('Economy.cs','namespace Game.Economy;\npublic class Market {\npublic int Buy(int amount) { return amount; }\n}')
        self.put('Main.cs','using Game.Economy;\nnamespace Game.UI;\npublic class Main {}')
        self.index.refresh(self.root)
        self.assertEqual(self.index.impact(self.root,['Economy.cs'])['dependents'],['Main.cs'])
        self.assertTrue(any(x['name']=='Buy' for x in self.index.search(self.root,'Buy')))
        self.put('Other.cs','namespace Game.Economy;\npublic class Other {}')
        self.index.refresh(self.root)
        self.assertEqual(self.index.impact(self.root,['Economy.cs'])['dependents'],[])
    def test_stale_module_and_excluded_files(self):
        self.put('a.js','export function buy() {}')
        self.put('b.js','import { buy } from "./a.js";')
        self.index.refresh(self.root)
        self.assertEqual(self.index.impact(self.root,['a.js'])['dependents'],['b.js'])
        self.assertEqual(self.index.impact(self.root,['a.js'],exclude=['b.js'])['dependents'],[])
        (self.root/'b.js').write_text('export function other() {}')
        self.assertEqual(self.index.impact(self.root,['a.js'])['dependents'],[])
if __name__=='__main__':unittest.main()
