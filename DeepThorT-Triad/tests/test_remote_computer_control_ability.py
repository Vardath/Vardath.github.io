import json,tempfile,unittest
from pathlib import Path
from unittest.mock import patch
from deepthort_local import remote_computer_control as m

SPEC={'host':'computer.example.org','port':3389,'seconds':30,'authorised_host':True}
RESULT={'client_process_observed':True,'client_scope_closed':True,'stop_reason':'duration_elapsed'}

class RemoteComputerTests(unittest.TestCase):
    def test_profile_restricts_redirect_and_prompts(self):
        text=m.profile(SPEC).decode('utf-16')
        for line in ('full address:s:computer.example.org:3389','authentication level:i:1',
                     'prompt for credentials:i:1','redirectclipboard:i:0','drivestoredirect:s:',
                     'audiocapturemode:i:0','autoreconnection enabled:i:0'):
            self.assertIn(line,text.splitlines())
        self.assertNotIn('password',text.lower())
    def test_refuses_injection_or_unapproved_host(self):
        for s in (dict(SPEC,host='computer.example.org\npassword'),dict(SPEC,authorised_host=False),
                  dict(SPEC,seconds=999),dict(SPEC,port=True)):
            with self.assertRaises(ValueError):m.checked(s)
    def test_review_guard_and_observation_not_connection_claim(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td).resolve();(root/'spec.json').write_text(json.dumps(SPEC),encoding='utf8')
            with patch.object(m,'runtime',return_value={'path':'fixture','kind':'stat','expected':'a'*64}) as client,patch.object(m.network,'require',return_value=True) as permission:
                plan,_=m.review(root,'spec.json','out.json')
                r=m.execute(root,plan,backend=lambda s,stage,c:RESULT.copy())
                self.assertFalse(r['remote_connection_verified'])
                self.assertFalse(r['autonomous_input_sent'])
                self.assertEqual(r['backend'],'injected_fixture')
                plan,_=m.review(root,'spec.json','other.json')
                permission.side_effect=PermissionError('blocked')
                with self.assertRaises(PermissionError):m.execute(root,plan,backend=lambda *_:self.fail('blocked'))
                self.assertFalse((root/'other.json').exists())
if __name__=='__main__':unittest.main()
