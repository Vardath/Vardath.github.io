import json,tempfile,unittest
from pathlib import Path
from unittest.mock import patch
from deepthort_local import virtual_computer as m

SPEC={'iso':'boot.iso','memory_mib':256,'seconds':30,'trusted_boot_media':True}
RESULT={'process_observed':True,'stop_reason':'observation_elapsed','cleanup_scope_closed':True}

class VirtualComputerTests(unittest.TestCase):
    def test_fixed_offline_command(self):
        cmd=m.command(SPEC,'qemu-system-x86_64.exe')
        for pair in (['-machine','pc,accel=tcg'],['-nic','none'],['-smp','1'],['-m','256'],['-drive','file=boot.iso,format=raw,media=cdrom,readonly=on']):
            self.assertTrue(any(cmd[i:i+2]==pair for i in range(len(cmd)-1)))
        self.assertNotIn('-virtfs',cmd);self.assertNotIn('-enable-kvm',cmd)
    def test_invalid_scope(self):
        for spec in (dict(SPEC,trusted_boot_media=False),dict(SPEC,memory_mib=4096),dict(SPEC,seconds=900)):
            with self.assertRaises(ValueError):m.checked(spec)
    def test_exact_iso_and_honest_receipt(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td).resolve();(root/'boot.iso').write_bytes(b'x'*65536)
            (root/'spec.json').write_text(json.dumps(SPEC),encoding='utf8')
            with patch.object(m,'runtime',return_value={'path':'fixture','kind':'stat','expected':'a'*64}),patch.object(m,'require_storage'):
                plan,_=m.review(root,'spec.json','out.json')
                r=m.execute(root,plan,backend=lambda *_:RESULT.copy())
                self.assertFalse(r['guest_boot_verified']);self.assertFalse(r['security_isolation_verified'])
                self.assertEqual(r['backend'],'injected_fixture')
                plan,_=m.review(root,'spec.json','other.json');(root/'boot.iso').write_bytes(b'y'*65536)
                with self.assertRaises(ValueError):m.execute(root,plan,backend=lambda *_:self.fail('stale image'))
                self.assertFalse((root/'other.json').exists())
if __name__=='__main__':unittest.main()
