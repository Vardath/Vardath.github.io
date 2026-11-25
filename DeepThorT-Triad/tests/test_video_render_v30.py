import unittest
import os
from deepthort_local.video_render import captions,stamp,scene_command
from deepthort_local.render_probe import exercise
class VideoRenderTests(unittest.TestCase):
    def test_caption_intervals(self):
        text=captions([{'narration':'A flower opens.','start_sample':0,'end_sample':22050},
                       {'narration':'The garden grows.','start_sample':22050,'end_sample':44100}])
        self.assertIn('00:00:00,000 --> 00:00:01,000',text)
        self.assertIn('00:00:01,000 --> 00:00:02,000',text)
    def test_fixed_argv(self):
        argv=scene_command('ffmpeg',2,1920,1080,25)
        self.assertIn('image-02.png',argv)
        self.assertEqual(argv[-1],'clip-02.mp4')
        self.assertIn('-protocol_whitelist',argv)
        self.assertIn('libx264',argv)
    @unittest.skipIf(os.name=='nt','Native rendering is tested under the capped Windows preflight')
    def test_real_ffmpeg_fixture(self):
        self.assertEqual(exercise()['status'],'passed')
