"""50% commit ceiling contract and adaptive lower memory limit."""
import unittest
from deepthort_local.win_cpu_cap import calculate_ram_limit

class SharedCap50Tests(unittest.TestCase):
    def test_default_50_percent(self):
        total=40*1024**3
        self.assertEqual(calculate_ram_limit(total,total),total*50//100)
    def test_reserve_under_pressure(self):
        total=40*1024**3
        self.assertEqual(calculate_ram_limit(total,12*1024**3),8*1024**3)
    def test_no_raise_above_ceiling(self):
        with self.assertRaises(ValueError):
            calculate_ram_limit(40*1024**3,40*1024**3,51)
    def test_lower_explicit_limit_still_allowed(self):
        total=40*1024**3
        self.assertEqual(calculate_ram_limit(total,total,30),total*30//100)

    def test_previous_explicit_cap_and_cpu_ceiling(self):
        from deepthort_local.win_cpu_cap import MAX_CPU_PERCENT,MAX_RAM_PERCENT
        total=40*1024**3
        self.assertEqual(MAX_CPU_PERCENT,40)
        self.assertEqual(MAX_RAM_PERCENT,50)
        self.assertEqual(calculate_ram_limit(total,total,40),total*40//100)
        self.assertEqual(calculate_ram_limit(total,25*1024**3),20*1024**3)
        self.assertEqual(calculate_ram_limit(total,18*1024**3),14*1024**3)
