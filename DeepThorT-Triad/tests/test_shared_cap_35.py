"""Medium/High hard cap, conservative admission and automatic transitions."""
import unittest
from deepthort_local.win_cpu_cap import calculate_ram_limit

class SharedCap50Tests(unittest.TestCase):
    def test_default_65_percent(self):
        total=40*1024**3
        self.assertEqual(calculate_ram_limit(total,total),total*65//100)
    def test_reserve_under_pressure(self):
        total=40*1024**3
        self.assertEqual(calculate_ram_limit(total,12*1024**3),8*1024**3)
    def test_no_raise_above_ceiling(self):
        with self.assertRaises(ValueError):
            calculate_ram_limit(40*1024**3,40*1024**3,81)
    def test_lower_explicit_limit_still_allowed(self):
        total=40*1024**3
        self.assertEqual(calculate_ram_limit(total,total,30),total*30//100)

    def test_previous_explicit_cap_and_cpu_ceiling(self):
        from deepthort_local.win_cpu_cap import MAX_CPU_PERCENT,MAX_RAM_PERCENT
        total=40*1024**3
        self.assertEqual(MAX_CPU_PERCENT,85)
        self.assertEqual(MAX_RAM_PERCENT,80)
        self.assertEqual(calculate_ram_limit(total,total,80),total*80//100)
        self.assertEqual(calculate_ram_limit(total,total,40),total*40//100)
        self.assertEqual(calculate_ram_limit(total,25*1024**3),21*1024**3)
        self.assertEqual(calculate_ram_limit(total,18*1024**3),14*1024**3)

class AutomaticResourceTests(unittest.TestCase):
    def test_protection_immediate_and_recovery_hysteresis(self):
        from deepthort_local.resource_policy import AutomaticResources,GIB
        p=AutomaticResources();total=40*GIB
        self.assertEqual(p.choose(False,20*GIB,total),85)
        self.assertEqual(p.choose(True,20*GIB,total),50)
        self.assertEqual(p.choose(False,20*GIB,total),50)
        self.assertEqual(p.choose(False,20*GIB,total),85)
        self.assertEqual(p.choose(False,5*GIB,total),50)
        self.assertEqual(p.choose(False,7*GIB,total),50)
        self.assertEqual(p.choose(False,9*GIB,total),50)
        self.assertEqual(p.choose(False,9*GIB,total),85)
        self.assertEqual(p.choose(None,9*GIB,total),50)

    def test_medium_budget_is_cooperative_and_slots_are_bounded(self):
        from deepthort_local.resource_policy import admission_budget,managed_slots,GIB
        total=40*GIB;cap=32*GIB
        self.assertEqual(admission_budget(cap,20*GIB,total,5000),(26*GIB,18*GIB,total))
        self.assertEqual(admission_budget(16*GIB,20*GIB,total,8500),(16*GIB,20*GIB,total))
        self.assertEqual(managed_slots((cap,20*GIB,total,5000)),1)
        self.assertEqual(managed_slots((cap,5*GIB,total,5000)),0)
        self.assertEqual(managed_slots((cap,20*GIB,total,8500)),4)

    def test_game_library_hints(self):
        from deepthort_local.resource_policy import game_library_path
        self.assertTrue(game_library_path(r'D:\SteamLibrary\steamapps\common\X4 Foundations\X4.exe'))
        self.assertTrue(game_library_path(r'C:\Epic Games\Game\Game.exe'))
        self.assertFalse(game_library_path(r'C:\Epic Games\EpicGamesLauncher.exe'))
        self.assertFalse(game_library_path(r'C:\Windows\notepad.exe'))

    @unittest.skipUnless(__import__('os').name=='nt','Native Windows Job Object')
    def test_live_cpu_transition_readback(self):
        import ctypes,sys
        from ctypes import wintypes
        from deepthort_local.win_cpu_cap import run_capped,CpuRate,JobObjectCpuRateControlInformation
        seen=[];calls=[]
        query=ctypes.WinDLL('kernel32',use_last_error=True).QueryInformationJobObject
        query.argtypes=(wintypes.HANDLE,ctypes.c_int,ctypes.c_void_p,wintypes.DWORD,ctypes.c_void_p)
        query.restype=wintypes.BOOL
        def policy(available,total):
            calls.append(1)
            return 85 if len(calls)==1 else 50
        def observe(job,cap,finished):
            value=CpuRate()
            self.assertTrue(query(job,JobObjectCpuRateControlInformation,ctypes.byref(value),ctypes.sizeof(value),None))
            seen.append(value.CpuRate)
        self.assertEqual(run_capped([sys.executable,'-c','import time;time.sleep(6)'],
            percent=85,ram_percent=65,observe=observe,cpu_policy=policy),0)
        self.assertEqual(seen[0],8500)
        self.assertIn(5000,seen)
