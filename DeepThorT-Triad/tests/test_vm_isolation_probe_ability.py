import json,tempfile,unittest
from pathlib import Path
from unittest.mock import patch
from deepthort_local import vm_isolation_probe as m

SPEC={'probe':'readonly_guest_media','seconds':30,'trusted_emulator':True}

class VMIsolationTests(unittest.TestCase):
    def test_fixture_and_exact_guest_result(self):
        data=m.fixture()
        self.assertEqual(len(data),1474560);self.assertEqual(data[510:514],b'\x55\xaa\x34\x12')
        self.assertIn(m.SUCCESS,data[:510]);self.assertIn(m.FAILURE,data[:510])
        r=m.assess(m.SUCCESS,data,data)
        self.assertTrue(r['guest_bios_write_denied'])
        self.assertFalse(r['general_security_isolation_verified'])
        self.assertFalse(r['guest_network_access_tested'])
    def test_changed_media_and_fake_marker_rejected(self):
        data=m.fixture()
        for marker,after in ((m.FAILURE,data),(b'',data),(m.SUCCESS,data[:-1]+b'x')):
            with self.assertRaises(ValueError):m.assess(marker,data,after)
        with self.assertRaises(ValueError):m.checked(dict(SPEC,trusted_emulator=False))
        cmd=m.command(SPEC,'qemu-system-x86_64.exe')
        self.assertIn('if=floppy,file=probe.img,format=raw,readonly=on',cmd)
        self.assertIn('none',cmd[cmd.index('-nic')+1])
    def test_review_and_no_overwrite(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td).resolve();(root/'spec.json').write_text(json.dumps(SPEC),encoding='utf8')
            with patch.object(m.vm,'runtime',return_value={'path':'fixture','kind':'stat','expected':'a'*64}),patch.object(m,'require_storage'):
                plan,_=m.review(root,'spec.json','out.json')
                r=m.execute(root,plan,backend=lambda *_:(m.SUCCESS,m.fixture(),m.fixture()))
                self.assertEqual(r['backend'],'injected_fixture')
                with self.assertRaises(ValueError):m.execute(root,plan,backend=lambda *_:self.fail('overwrite'))
                plan,_=m.review(root,'spec.json','bad.json')
                with self.assertRaises(ValueError):m.execute(root,plan,backend=lambda *_:(m.FAILURE,m.fixture(),m.fixture()))
                self.assertFalse((root/'bad.json').exists())
if __name__=='__main__':unittest.main()
