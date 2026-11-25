"""Secondary model is advisory and shares one OS cap."""
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
from deepthort_local.dual_onnx import memory_room, council_can_start, deliberate_instruction, _object, local_health
from deepthort_local.win_cpu_cap import calculate_ram_limit


class DualOnnxTests(unittest.TestCase):
    def test_40gb_ram_supports_two_when_headroom_exists(self):
        g=1024**3
        self.assertTrue(memory_room(total=40*g,available=15*g))
        self.assertFalse(memory_room(total=40*g,available=4*g))
        self.assertFalse(memory_room(total=16*g,available=12*g))
        self.assertTrue(council_can_start(memory=(40*g,20*g),capped=True))
        self.assertFalse(council_can_start(memory=(40*g,20*g),capped=False))
        self.assertEqual(calculate_ram_limit(40*g,20*g),12*g)
        with self.assertRaises(ValueError):calculate_ram_limit(40*g,20*g,ram_percent=31)

    def test_janus_and_sentinel_independent_calls(self):
        calls=[]
        answers=iter([
            json.dumps({'next_action':'Inspect docking sockets before changing XML',
                        'verification':'Compare discovered PE macro docks',
                        'scope_change':False,'reason':'Safe independent check'}),
            json.dumps({'risk':'Cannot infer IDs from memory',
                        'test':'Validate existing macro and component references',
                        'requires_review':False}),
        ])
        def ask(msg,tokens):
            calls.append(msg)
            return next(answers)
        output=deliberate_instruction('Make the asteroid dock correctly',project='D:/x4mods',
            work_summary='Building one PE ship',asker=ask)
        self.assertEqual(len(calls),2)
        self.assertIn('JANUS',calls[0][0]['content'])
        self.assertIn('Sentinel',calls[1][0]['content'])
        self.assertIn('Validate existing macro',output['verification'])
        self.assertFalse(output['needs_review'])
        self.assertNotIn('execute',output['next_action'])

    def test_scope_change_requires_review(self):
        answers=iter([
            '{"next_action":"Revise approved build plan","verification":"User reviews plan","scope_change":true}',
            '{"risk":"approval required","test":"Review new scope","requires_review":true}',
        ])
        out=deliberate_instruction('Change approved mod',project='D:/x4mods',asker=lambda m,n: next(answers))
        self.assertTrue(out['needs_review'])

    def test_invalid_neural_reply_fails_closed(self):
        for bad in ('not json','[]','{"next_action":"a","verification":"b"}'):
            with self.subTest(bad=bad):
                with self.assertRaises(ValueError):
                    deliberate_instruction('New instruction',project='D:/x4mods',asker=lambda *a:bad)
        with self.assertRaises(ValueError):_object('{bad')

    def test_no_external_local_model_urls(self):
        with self.assertRaises(ValueError):local_health('https://evil.example')

if __name__=='__main__':unittest.main()
