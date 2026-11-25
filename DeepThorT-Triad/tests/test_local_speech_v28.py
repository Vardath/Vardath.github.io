import unittest
from deepthort_local.speech_probe import fixture_exercise
from deepthort_local.local_speech import choose_voice,NoVoice
class SpeechTests(unittest.TestCase):
    def test_scene_audio_receipts(self):
        self.assertEqual(fixture_exercise()['status'],'passed')
    def test_language_and_exact_voice(self):
        voices=[{'id':'us','name':'US','culture':'en-US','gender':'Male'},
                {'id':'au','name':'AU','culture':'en-AU','gender':'Female'}]
        self.assertEqual(choose_voice(voices,'Australian English')['id'],'au')
        self.assertEqual(choose_voice(voices,'English','US')['id'],'us')
        with self.assertRaises(NoVoice):choose_voice(voices,'French')
        with self.assertRaises(NoVoice):choose_voice(voices,'en-AU','US')
