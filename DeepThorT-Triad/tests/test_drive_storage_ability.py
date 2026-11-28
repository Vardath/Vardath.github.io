import hashlib
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
from deepthort_local import drive_storage as tool

class DriveStorageTests(unittest.TestCase):
    def setUp(self):
        self.account='owner@example.com'
        self.profile={'user':{'emailAddress':self.account}}
    def test_bounded_folder_listing(self):
        s={'operation':'list','account':self.account,'folder_id':'root','limit':2}
        item={'id':'file123','name':'example.txt','mimeType':'text/plain','trashed':False}
        with patch.object(tool,'fetch',side_effect=[self.profile,{'files':[item],'nextPageToken':'next'},self.profile]) as req:
            receipt,raw=tool.inspect(s,'dummy',approved=True)
            self.assertIsNone(raw);self.assertTrue(receipt['more_results'])
            self.assertEqual(receipt['files'][0]['id'],'file123')
            self.assertIn('pageSize=2',req.call_args_list[1].args[0])
        with patch.object(tool,'fetch',return_value={'user':{'emailAddress':'other@example.com'}}):
            with self.assertRaises(ValueError):tool.inspect(s,'dummy',approved=True)
        with self.assertRaises(PermissionError):tool.inspect(s,'dummy')
    def test_verified_download_and_exclusive_save(self):
        s={'operation':'download','account':self.account,'file_id':'abc'}
        raw=b'actual bytes'
        m={'id':'abc','name':'untrusted.txt','mimeType':'text/plain','trashed':False,'version':'1',
           'size':str(len(raw)),'md5Checksum':hashlib.md5(raw,usedforsecurity=False).hexdigest()}
        with patch.object(tool,'fetch',side_effect=[self.profile,m,raw,m,self.profile]):
            receipt,data=tool.inspect(s,'dummy',approved=True)
        with tempfile.TemporaryDirectory() as directory:
            p=Path(directory)/'new.txt'
            with self.assertRaises(PermissionError):tool.save_download(p,receipt,data)
            tool.save_download(p,receipt,data,approved=True)
            self.assertEqual(p.read_bytes(),raw)
            with self.assertRaises(FileExistsError):tool.save_download(p,receipt,data,approved=True)
        with patch.object(tool,'fetch',side_effect=[self.profile,m,raw,dict(m,version='2')]):
            with self.assertRaises(ValueError):tool.inspect(s,'dummy',approved=True)
        with patch.object(tool,'fetch',side_effect=[self.profile,m,b'wrong']):
            with self.assertRaises(ValueError):tool.inspect(s,'dummy',approved=True)
    def test_refuses_native_docs_and_bad_identifiers(self):
        s={'operation':'download','account':self.account,'file_id':'abc'}
        m={'id':'abc','name':'doc','mimeType':'application/vnd.google-apps.document','trashed':False}
        with patch.object(tool,'fetch',side_effect=[self.profile,m]) as req:
            with self.assertRaises(ValueError):tool.inspect(s,'dummy',approved=True)
            self.assertEqual(req.call_count,2)
        for ident in ("../abc","a?b","' or true"):
            with self.assertRaises(ValueError):tool.checked(dict(s,file_id=ident))

if __name__=='__main__':unittest.main()
