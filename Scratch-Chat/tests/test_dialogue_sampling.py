"""Seeded dialogue epoch sampling must cover every example and resume identically."""
import unittest
from capability.dialogue_sft_train import example_index


class DialogueSamplingTests(unittest.TestCase):
    def test_epoch_is_permutation(self):
        for count in (1, 2, 7, 23):
            for epoch in range(3):
                order = [example_index(epoch * count + i, count, 2026)
                         for i in range(count)]
                self.assertEqual(sorted(order), list(range(count)))

    def test_reproducible_across_resume(self):
        full = [example_index(i, 11, 2026) for i in range(35)]
        resumed = [example_index(i, 11, 2026) for i in range(17, 35)]
        self.assertEqual(full[17:], resumed)

    def test_invalid(self):
        with self.assertRaises(ValueError):
            example_index(-1, 2, 1)
        with self.assertRaises(ValueError):
            example_index(0, 0, 1)


if __name__ == "__main__":
    unittest.main()
