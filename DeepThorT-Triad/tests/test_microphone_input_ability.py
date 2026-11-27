import ctypes,io,os,tempfile,unittest,wave
from pathlib import Path
from deepthort_local import microphone_input as m
class MicrophoneTests(unittest.TestCase):
    def test_bounded_fixture_and_explicit_publication(self):
        calls=[]
        def backend(seconds,cancelled):
            calls.append(seconds);return b'\x01\x00'*(m.RATE*seconds)
        with self.assertRaises(PermissionError):m.capture(1,backend=backend)
        self.assertEqual(calls,[])
        payload=m.capture(2,approved=True,backend=backend)
        with wave.open(io.BytesIO(payload),'rb') as f:
            self.assertEqual((f.getframerate(),f.getnchannels(),f.getsampwidth(),f.getnframes()),(16000,1,2,32000))
        with tempfile.TemporaryDirectory() as td:
            with self.assertRaises(PermissionError):m.save(td,'capture.wav',[],payload,2)
            with self.assertRaises(ValueError):m.save(td,'../capture.wav',[],payload,2,approved=True)
            with self.assertRaises(ValueError):m.save(td,'capture.wav',['capture.wav'],payload,2,approved=True)
            r=m.save(td,'capture.wav',[],payload,2,approved=True)
            self.assertFalse(r['transcribed']);self.assertEqual(Path(td,'capture.wav').read_bytes(),payload)
            with self.assertRaises(ValueError):m.save(td,'capture.wav',[],payload,2,approved=True)
    def test_cancellation_and_incomplete_audio(self):
        for seconds in (0,31,True):
            with self.assertRaises(ValueError):m.capture(seconds,approved=True,backend=lambda *a:self.fail('unexpected capture'))
        with self.assertRaises(ValueError):m.capture(1,lambda:True,approved=True,backend=lambda *a:self.fail('unexpected capture'))
        with self.assertRaises(ValueError):m.capture(1,approved=True,backend=lambda *a:b'\0')
        flag=[False]
        def cancelled_backend(*a):flag[0]=True;return b'\0'*(m.RATE*2)
        with self.assertRaises(ValueError):m.capture(1,lambda:flag[0],approved=True,backend=cancelled_backend)
    @unittest.skipUnless(os.name=='nt','Windows ABI only')
    def test_windows_wave_abi(self):
        self.assertEqual(ctypes.sizeof(m.Format),18)
        self.assertEqual(ctypes.sizeof(m.Header),48 if ctypes.sizeof(ctypes.c_void_p)==8 else 32)
        self.assertEqual(m.Header.dwBytesRecorded.offset,ctypes.sizeof(ctypes.c_void_p)+4)


class ScreenCaptureTests(unittest.TestCase):
    def test_explicit_capture_save_and_exact_handoff(self):
        from deepthort_local import screen_capture as s
        calls=[]
        def backend(box):
            calls.append(box);return bytes([12,34,56])*16
        with self.assertRaises(PermissionError):s.capture((0,0,4,4),(16,16),backend=backend)
        self.assertEqual(calls,[])
        raw=s.capture((0,0,4,4),(16,16),approved=True,backend=backend)
        with tempfile.TemporaryDirectory() as td:
            root=Path(td).resolve()
            with self.assertRaises(PermissionError):s.save(root,'screen.png',[],raw)
            with self.assertRaises(ValueError):s.save(root,'../screen.png',[],raw,approved=True)
            r=s.save(root,'screen.png',[],raw,approved=True)
            path=root/'screen.png';prompt=s.prompt_for(r['sha256'])
            self.assertEqual(s.exact_snapshot(root,path,prompt),raw)
            with self.assertRaises(ValueError):s.save(root,'screen.png',[],raw,approved=True)
            path.write_bytes(raw+b'x')
            with self.assertRaises(ValueError):s.exact_snapshot(root,path,prompt)
    def test_reject_invalid_region_or_pixels(self):
        from deepthort_local import screen_capture as s
        for box in ((-1,0,4,4),(0,0,True,4),(0,0,0,4),(15,15,4,4),(0,0,2048,2048)):
            with self.assertRaises(ValueError):s.capture(box,(16,16),approved=True,backend=lambda *_:self.fail('unexpected capture'))
        with self.assertRaises(ValueError):s.capture((0,0,4,4),(16,16),approved=True,backend=lambda _:b'x')
