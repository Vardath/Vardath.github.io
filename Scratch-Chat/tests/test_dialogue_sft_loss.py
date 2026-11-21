"""Regression checks for shifted assistant-only cross entropy."""
import unittest
import torch
import torch.nn.functional as F
from capability.dialogue_sft_loss import assistant_causal_loss


class AssistantCausalLossTest(unittest.TestCase):
    def test_shift_and_mask(self):
        logits = torch.tensor([[[1., 0., 0.], [0., 1., 0.], [0., 0., 1.], [1., 0., 0.]]], requires_grad=True)
        labels = torch.tensor([[-100, -100, 2, 0]])
        expected = F.cross_entropy(logits[:, 1:3, :].reshape(-1, 3), torch.tensor([2, 0]))
        actual = assistant_causal_loss(logits, labels)
        self.assertTrue(torch.allclose(actual, expected))
        actual.backward()
        self.assertEqual(float(logits.grad[0, 0].abs().sum()), 0.0)
        self.assertEqual(float(logits.grad[0, 3].abs().sum()), 0.0)

    def test_rejects_empty_supervision(self):
        with self.assertRaises(ValueError):
            assistant_causal_loss(torch.zeros(1, 3, 4), torch.full((1, 3), -100))

    def test_rejects_bad_dimensions(self):
        with self.assertRaises(ValueError):
            assistant_causal_loss(torch.zeros(2, 3, 4), torch.zeros(1, 3, dtype=torch.long))

    def test_rejects_out_of_vocab(self):
        with self.assertRaises(ValueError):
            assistant_causal_loss(torch.zeros(1, 3, 4), torch.tensor([[-100, 8, -100]]))


if __name__ == "__main__":
    unittest.main()
