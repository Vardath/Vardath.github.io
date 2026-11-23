"""Capacity estimator must agree with the actual scratch-only model."""
import unittest
from capability.capacity_plan import estimate
from capability.modern_model import ModernConfig, ModernScratchTransformer


class CapacityPlanTests(unittest.TestCase):
    def test_parameter_count_matches_model(self):
        for vocab, width, layers, heads, context in [(300, 64, 2, 4, 256), (512, 128, 3, 8, 512)]:
            cfg = ModernConfig(vocab_size=vocab, width=width, layers=layers,
                               heads=heads, context_size=context)
            self.assertEqual(estimate(vocab, width, layers, heads, context)["parameters"],
                             ModernScratchTransformer(cfg).parameter_count)

    def test_rejects_invalid_rope_head(self):
        with self.assertRaises(ValueError):
            estimate(300, 40, 2, 8, 256)

    def test_optimizer_lower_bound(self):
        result = estimate(300, 64, 2, 4, 256)
        self.assertGreater(result["adamw_fp32_weights_grad_moments_gib"],
                           result["weights_fp32_gib"])


if __name__ == "__main__":
    unittest.main()
