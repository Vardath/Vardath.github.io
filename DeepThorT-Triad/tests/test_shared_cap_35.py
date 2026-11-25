"""35% ceiling contract and adaptive lower memory limit."""
import unittest
from deepthort_local.win_cpu_cap import calculate_ram_limit

class SharedCap35Tests(unittest.TestCase):
    def test_default_35_percent(self):
        total=40*1024**3
        self.assertEqual(calculate_ram_limit(total,total),total*35//100)
    def test_reserve_under_pressure(self):
        total=40*1024**3
        self.assertEqual(calculate_ram_limit(total,12*1024**3),8*1024**3)
    def test_no_raise_above_ceiling(self):
        with self.assertRaises(ValueError):
            calculate_ram_limit(40*1024**3,40*1024**3,36)
    def test_lower_explicit_limit_still_allowed(self):
        total=40*1024**3
        self.assertEqual(calculate_ram_limit(total,total,30),total*30//100)
