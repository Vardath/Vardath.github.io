import os
import unittest
from deepthort_local.mouse_control import checked,messages,native_mouse
class MouseTests(unittest.TestCase):
    def test_exact_mouse_sequence(self):
        s={'actions':[{'kind':'move','x':2,'y':3},{'kind':'click','x':5,'y':6}]}
        self.assertEqual(messages(s),[(0x200,0,2|(3<<16)),(0x200,0,5|(6<<16)),(0x201,1,5|(6<<16)),(0x202,0,5|(6<<16))])
        for a in ({'kind':'click','x':True,'y':0},{'kind':'click','x':64,'y':0},{'kind':'right','x':0,'y':0},{'kind':'move','x':0,'y':0,'hwnd':1}):
            with self.assertRaises(ValueError):checked({'actions':[a]})
    @unittest.skipUnless(os.name=='nt','Native Windows fixture')
    def test_actual_owned_window_events(self):
        result=native_mouse({'actions':[{'kind':'move','x':2,'y':3},{'kind':'click','x':5,'y':6}]})
        self.assertTrue(result['event_sequence_verified'])
        self.assertEqual(result['messages_observed'],4)
        self.assertFalse(result['global_input_used'])

class KeyboardTests(unittest.TestCase):
    def test_literal_and_key_pairs(self):
        from deepthort_local.keyboard_control import checked,messages
        s={'actions':[{'kind':'text','text':'Ab'},{'kind':'key','key':'LEFT'}]}
        self.assertEqual(messages(s),[(0x102,65,1),(0x102,98,1),(0x100,0x25,1),(0x101,0x25,0xc0000001)])
        for a in ({'kind':'text','text':'a\nb'},{'kind':'key','key':'CTRL+ALT+DEL'},{'kind':'text','text':'x','hwnd':1}):
            with self.assertRaises(ValueError):checked({'actions':[a]})
        with self.assertRaises(ValueError):checked({'actions':[{'kind':'text','text':'x'*32}]*5})
    @unittest.skipUnless(os.name=='nt','Native Windows fixture')
    def test_actual_keyboard_events(self):
        from deepthort_local.keyboard_control import native_keyboard
        r=native_keyboard({'actions':[{'kind':'text','text':'hello'},{'kind':'key','key':'ENTER'}]})
        self.assertEqual(r['messages_observed'],7)
        self.assertEqual(r['characters_observed'],5)
        self.assertTrue(r['event_sequence_verified'])
        self.assertFalse(r['global_input_used'])
