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
