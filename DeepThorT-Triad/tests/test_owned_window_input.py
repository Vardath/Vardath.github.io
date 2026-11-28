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

class BackgroundDesktopTests(unittest.TestCase):
    def test_expected_title_not_equivalent_to_task_success(self):
        from deepthort_local.background_desktop import result_for,checked
        s={'executable':'app.exe','seconds':15,'expected_window_title':'Ready'}
        observed={'status':'window_observed','windows':[{'title':'Ready','hung':False}],
                  'shared_root_cap_verified':True,'separate_desktop':True,'foreground_switched':False}
        r=result_for(s,observed)
        self.assertTrue(r['expected_window_observed'])
        self.assertFalse(r['functional_success_verified'])
        self.assertFalse(result_for(s,dict(observed,status='preempted'))['expected_window_observed'])
        self.assertFalse(result_for(s,dict(observed,windows=[{'title':'Other','hung':False}]))['expected_window_observed'])
        with self.assertRaises(ValueError):result_for(s,dict(observed,shared_root_cap_verified=False))
        with self.assertRaises(ValueError):checked(dict(s,seconds=46))
    def test_review_guards_exact_project_binary(self):
        import tempfile
        import json
        from pathlib import Path
        from deepthort_local.background_desktop import review,validate
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp).resolve()
            (root/'app.exe').write_bytes(b'fixture')
            (root/'spec.json').write_text(json.dumps({'executable':'app.exe','seconds':15,'expected_window_title':'Ready'}))
            plan,_=review(root,'spec.json','result.json')
            self.assertEqual(validate(root,plan)[2].run_seconds,15)
            (root/'app.exe').write_bytes(b'changed')
            with self.assertRaises(ValueError):validate(root,plan)

class LiveScreenTests(unittest.TestCase):
    def test_sample_identity_and_caption(self):
        import tempfile
        from deepthort_local.live_screen import samples,interpret
        from deepthort_local.texture_pixels import encode
        s={'region':[0,0,2,2],'samples':2,'interval_seconds':1}
        now=[0.]
        def capture(box,screen,approved):return encode(2,2,'RGB',bytes([int(now[0])]*12))
        with tempfile.TemporaryDirectory() as tmp:
            kwargs=dict(screen_size=lambda:(100,100),capture_fn=capture,clock=lambda:now[0],sleep=lambda n:now.__setitem__(0,now[0]+n))
            with self.assertRaises(PermissionError):samples(s,(100,100),tmp,**kwargs)
            paths,rows=samples(s,(100,100),tmp,approved=True,**kwargs)
            self.assertNotEqual(rows[0]['sha256'],rows[1]['sha256'])
            result=interpret(paths,rows,[],captioner=lambda p,t:['first','second'])
            self.assertEqual(result[1]['caption'],'second')
            paths[0].write_bytes(b'changed')
            with self.assertRaises(ValueError):interpret(paths,rows,[],captioner=lambda p,t:['first','second'])
    def test_scope_and_display_change(self):
        import tempfile
        from deepthort_local.live_screen import samples,checked
        s={'region':[0,0,2,2],'samples':2,'interval_seconds':1}
        for patch in ({'samples':5},{'interval_seconds':0},{'region':[0,0,4000,4000]}):
            with self.assertRaises(ValueError):checked(dict(s,**patch))
        with tempfile.TemporaryDirectory() as tmp:
            with self.assertRaises(ValueError):samples(s,(100,100),tmp,approved=True,screen_size=lambda:(90,90))

class ControllerInputTests(unittest.TestCase):
    def test_fixed_action_generation_and_strict_evidence(self):
        from deepthort_local.controller_input import script,assess,checked
        s={'actions':[{'kind':'button','button':'A'},{'kind':'axis','axis':'LEFT_X','direction':-1}]}
        gd=script(s)
        self.assertIn('InputEventJoypadButton.new()',gd)
        self.assertIn('InputEventJoypadMotion.new()',gd)
        self.assertIn('event_1.axis_value = -1.0',gd)
        self.assertIn('Input.parse_input_event(release_1)',gd)
        log='JANUS_CONTROLLER 0 passed\nJANUS_CONTROLLER 1 passed\n'
        self.assertTrue(assess(s,log)['engine_action_press_release_verified'])
        for bad in ('',log+'ERROR: broken',log+'JANUS_CONTROLLER 0 passed\n'):
            with self.assertRaises(ValueError):assess(s,bad)
        for a in ({'kind':'button','button':'unknown'},{'kind':'axis','axis':'LEFT_X','direction':True},{'kind':'button','button':'A','device':1}):
            with self.assertRaises(ValueError):checked({'actions':[a]})
