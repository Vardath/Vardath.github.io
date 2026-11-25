import unittest
from deepthort_local.visual_probe import exercise
from deepthort_local.stock_images import checked_url,NoRedirect
class VisualTests(unittest.TestCase):
    def test_asset_pipeline(self):
        self.assertEqual(exercise()['status'],'passed')
    def test_no_redirect_or_arbitrary_url(self):
        for url in ('http://upload.wikimedia.org/wikipedia/commons/x.png','https://upload.wikimedia.org.evil.test/wikipedia/commons/x.png','https://upload.wikimedia.org:443/wikipedia/commons/x.png','https://upload.wikimedia.org/private'):
            with self.assertRaises(ValueError):checked_url(url,'upload.wikimedia.org')
        with self.assertRaises(ValueError):NoRedirect().redirect_request(None,None,302,'',{},'https://evil.test')
