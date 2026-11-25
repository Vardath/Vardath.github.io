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

    def test_dependency_pair_discovery(self):
        import tempfile
        from pathlib import Path
        from deepthort_local.video_tools import find_pair
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);old=root/'old';new=root/'new';old.mkdir();new.mkdir()
            (old/'ffmpeg.exe').write_bytes(b'fixture')
            for name in ('ffmpeg.exe','ffprobe.exe'):(new/name).write_bytes(b'fixture')
            which=lambda name:str(old/name) if (old/name).is_file() else None
            self.assertIsNone(find_pair(windows=True,which=which,extra_dirs=[]))
            self.assertEqual(find_pair(windows=True,which=which,extra_dirs=[new]),
                             tuple(str((new/name).resolve()) for name in ('ffmpeg.exe','ffprobe.exe')))
            (old/'ffprobe.exe').write_bytes(b'fixture')
            self.assertEqual(find_pair(windows=True,which=which,extra_dirs=[new]),
                             tuple(str((old/name).resolve()) for name in ('ffmpeg.exe','ffprobe.exe')))
