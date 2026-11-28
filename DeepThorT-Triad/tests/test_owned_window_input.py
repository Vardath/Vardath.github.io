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

class GuiOperationTests(unittest.TestCase):
    def test_spec_refuses_unbounded_actions(self):
        from deepthort_local.gui_operation import checked
        s={'executable':'app.exe','window_title':'Fixture','window_class':'Test','control_id':101,'text':'hello'}
        self.assertEqual(checked(s),s)
        for change in ({'control_id':True},{'text':'x'*121},{'window_title':''},{'hwnd':1},{'text':'a\nb'}):
            with self.assertRaises(ValueError):checked(dict(s,**change))
    @unittest.skipUnless(os.name=='nt','Native Windows fixture')
    def test_native_standard_edit_and_password_refusal(self):
        import ctypes
        from ctypes import wintypes as w
        from deepthort_local.gui_operation import Windows
        from deepthort_local.mouse_control import owned_window,fn
        with owned_window() as (u,parent,events):
            create=fn(u,'CreateWindowExW',[w.DWORD,w.LPCWSTR,w.LPCWSTR,w.DWORD,ctypes.c_int,ctypes.c_int,
                ctypes.c_int,ctypes.c_int,w.HWND,w.HMENU,w.HINSTANCE,ctypes.c_void_p],w.HWND)
            instance=fn(ctypes.WinDLL('kernel32'),'GetModuleHandleW',[w.LPCWSTR],w.HMODULE)(None)
            normal=create(0,'Edit','',0x40000000,0,0,100,20,parent,101,instance,None)
            secret=create(0,'Edit','',0x40000020,0,30,100,20,parent,102,instance,None)
            self.assertTrue(normal);self.assertTrue(secret)
            b=Windows()
            self.assertTrue(b.set_text(parent,os.getpid(),101,'hello',still_owned=lambda pid:pid==os.getpid()))
            with self.assertRaises(ValueError):b.set_text(parent,os.getpid(),102,'x',still_owned=lambda pid:True)
            with self.assertRaises(ValueError):b.set_text(parent,os.getpid(),101,'x',still_owned=lambda pid:False)
