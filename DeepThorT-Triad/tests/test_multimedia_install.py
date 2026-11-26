import json
import tempfile
import unittest
from pathlib import Path
from deepthort_local.multimedia_profile import (
    REPO, REVISION, LICENSE, FILES, validate_manifest, installed, install_plan, model_path)


def fixture():
    return {'sha':REVISION, 'siblings':[
        {'rfilename':name, 'size':900_000_000 if name=='unet/openvino_model.bin' else 10,
         'lfs':{'sha256':'a'*64}} for name in sorted(FILES)]}


class MultimediaInstallTests(unittest.TestCase):
    def test_ready_language_models_install_only_multimedia(self):
        plan=install_plan(role_ok=lambda role:True,runtime_ok=True,media_ok=False,creative_ok=True)
        self.assertEqual([(x[0],x[1]) for x in plan],[('download_multimedia.py',())])

    def test_only_missing_language_role_and_media(self):
        plan=install_plan(role_ok=lambda role:role!='janus',runtime_ok=True,media_ok=False,creative_ok=True)
        self.assertEqual([(x[0],x[1]) for x in plan],
                         [('download_model.py',('--role','janus')),('download_multimedia.py',())])

    def test_runtime_only_and_nothing_missing(self):
        self.assertEqual(install_plan(role_ok=lambda role:True,runtime_ok=False,media_ok=True,creative_ok=True)[0][1],('--runtime-only',))
        self.assertEqual(install_plan(role_ok=lambda role:True,runtime_ok=True,media_ok=True,creative_ok=True),[])

    def test_missing_intelligent_fourth_is_not_diffusion(self):
        plan=install_plan(role_ok=lambda role:True,runtime_ok=True,media_ok=True,creative_ok=False)
        self.assertEqual([(x[0],x[1]) for x in plan],[('download_creative.py',())])

    def test_snapshot_pin_and_allowlist(self):
        data=fixture()
        data['siblings'].append({'rfilename':'../untrusted.py','size':1,'blobId':'b'*40})
        result=validate_manifest(data)
        self.assertEqual(set(result['files']),FILES)
        self.assertEqual((result['repo'],result['revision'],result['license']),(REPO,REVISION,LICENSE))

    def test_incomplete_duplicate_wrong_revision_and_oversize_rejected(self):
        for fault in ('missing','duplicate','revision','oversize','hash'):
            with self.subTest(fault=fault):
                data=fixture()
                if fault=='missing':data['siblings'].pop()
                elif fault=='duplicate':data['siblings'].append(data['siblings'][0])
                elif fault=='revision':data['sha']='wrong'
                elif fault=='oversize':data['siblings'][0]['size']=3_000_000_001
                else:data['siblings'][0]['lfs']['sha256']='bad'
                with self.assertRaises(ValueError):validate_manifest(data)

    def test_missing_install_and_incomplete_receipt(self):
        with tempfile.TemporaryDirectory() as tmp:
            self.assertFalse(installed(tmp))
            path=model_path(tmp)
            path.mkdir(parents=True)
            (path/'verified-install.json').write_text(json.dumps(validate_manifest(fixture())),encoding='utf-8')
            self.assertFalse(installed(tmp))


if __name__=='__main__':
    unittest.main()
