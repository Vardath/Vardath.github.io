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
