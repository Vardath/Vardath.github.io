import tempfile
import unittest
from pathlib import Path
from deepthort_local.repository_index import RepositoryIndex

class FormatTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup)
        p=Path(self.tmp.name);self.root=p/'project';self.root.mkdir()
        self.index=RepositoryIndex(p/'index.sqlite')
    def put(self,p,s):
        f=self.root/p;f.parent.mkdir(parents=True,exist_ok=True);f.write_text(s,encoding='utf-8')
    def test_godot_resource_graph(self):
        self.put('fleet.gd','class_name Fleet\nsignal changed\nfunc move_ship():\n    pass\n')
        self.put('main.gd','extends "res://fleet.gd"\nfunc launch():\n    move_ship()\n')
        self.put('main.tscn','[gd_scene load_steps=2 format=3]\n[ext_resource type="Script" path="res://main.gd" id="1"]\n')
        self.index.refresh(self.root)
        self.assertEqual(self.index.impact(self.root,['fleet.gd'])['dependents'],['main.gd','main.tscn'])
        self.assertTrue(any(x['name']=='move_ship' for x in self.index.search(self.root,'move_ship')))
        self.assertEqual(self.index.references(self.root,'move_ship')[0]['path'],'main.gd')
    def test_godot_fake_strings_and_traversal(self):
        self.put('a.gd','func example():\n    pass\n')
        self.put('b.gd','var text = "load(\\\"res://a.gd\\\")"\n# preload("res://a.gd")\nvar other = """\npreload("res://a.gd")\n"""\nvar bad = load("res://../a.gd")\n')
        self.index.refresh(self.root)
        self.assertEqual(self.index.impact(self.root,['a.gd'])['dependents'],[])
    def test_xml_typed_unique_references(self):
        self.put('assets/macros/a.xml','<macros><macro name="ship_a_macro"><component ref="ship_a_component"/></macro></macros>')
        self.put('assets/components/a.xml','<components><component name="ship_a_component"/></components>')
        self.put('libraries/wares.xml','<wares><ware><component ref="ship_a_macro"/><macro ref="ship_a_macro"/></ware></wares>')
        self.index.refresh(self.root)
        self.assertEqual(self.index.impact(self.root,['assets/components/a.xml'])['dependents'],['assets/macros/a.xml','libraries/wares.xml'])
        self.put('duplicate.xml','<components><component name="ship_a_component"/></components>')
        self.index.refresh(self.root)
        self.assertEqual(self.index.impact(self.root,['assets/components/a.xml'])['dependents'],[])
    def test_xml_rejects_entities_and_malformed(self):
        self.put('bad.xml','<!DOCTYPE a [<!ENTITY x SYSTEM "file:///tmp/secret">]><a>&x;</a>')
        self.put('broken.xml','<macro name="invalid">')
        self.index.refresh(self.root)
        self.assertEqual(self.index.search(self.root,'invalid secret'),[])
    def test_stale_resource_removal(self):
        self.put('a.gd','func hello():\n    pass\n')
        self.put('b.gd','extends "res://a.gd"\n')
        self.index.refresh(self.root)
        (self.root/'b.gd').unlink()
        self.assertEqual(self.index.impact(self.root,['a.gd'])['dependents'],[])
if __name__=='__main__':unittest.main()
