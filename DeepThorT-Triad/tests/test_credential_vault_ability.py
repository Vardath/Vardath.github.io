import os,unittest,uuid
from deepthort_local import credential_vault as v

class Fixture:
    def __init__(self):self.records={}
    def put(self,n,s):self.records[n]=s
    def get(self,n):return self.records.get(n)
    def remove(self,n):return self.records.pop(n,None) is not None

class CredentialTests(unittest.TestCase):
    def test_approval_and_scope(self):
        f=Fixture()
        for call,args in ((v.save,('owner/repo','review','fake_token_123')),(v.retrieve,('owner/repo','review')),(v.forget,('owner/repo','review'))):
            with self.assertRaises(PermissionError):call(*args,backend=f)
        self.assertEqual(f.records,{})
        v.save('Owner/Repo','review','fake_token_123',approved=True,backend=f)
        self.assertEqual(v.retrieve('owner/repo','review',approved=True,backend=f),'fake_token_123')
        self.assertIsNone(v.retrieve('owner/repo','release',approved=True,backend=f))
        self.assertIsNone(v.retrieve('owner/other','review',approved=True,backend=f))
        self.assertTrue(v.forget('owner/repo','review',approved=True,backend=f))
        self.assertFalse(v.forget('owner/repo','review',approved=True,backend=f))
    def test_invalid_scope_and_secret(self):
        f=Fixture()
        for repo,mode,secret in (('../repo','review','fake_token_123'),('owner/repo','unknown','fake_token_123'),('owner/repo','review','bad\nsecret')):
            with self.assertRaises(ValueError):v.save(repo,mode,secret,approved=True,backend=f)
        self.assertEqual(f.records,{})
        f.records[v.target('owner/repo','review')]='invalid\nsecret'
        with self.assertRaisesRegex(ValueError,'Invalid stored credential'):v.retrieve('owner/repo','review',approved=True,backend=f)
    @unittest.skipUnless(os.name=='nt','Native Windows vault required')
    def test_native_roundtrip(self):
        repo='janus-test/'+uuid.uuid4().hex
        try:
            secret='fixture_only_'+uuid.uuid4().hex
            v.save(repo,'review',secret,approved=True)
            self.assertEqual(v.retrieve(repo,'review',approved=True),secret)
            self.assertIsNone(v.retrieve(repo,'release',approved=True))
            v.save(repo,'review','replacement_fixture_123',approved=True)
            self.assertEqual(v.retrieve(repo,'review',approved=True),'replacement_fixture_123')
            self.assertTrue(v.forget(repo,'review',approved=True))
            self.assertIsNone(v.retrieve(repo,'review',approved=True))
        finally:v.forget(repo,'review',approved=True)
    @unittest.skipIf(os.name=='nt','Non-Windows refusal only')
    def test_no_plaintext_fallback(self):
        with self.assertRaises(OSError):v.save('owner/repo','review','fake_token_123',approved=True)
