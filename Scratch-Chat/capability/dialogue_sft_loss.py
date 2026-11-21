"""Causal next-token supervised fine-tuning loss for Scratch Chat.

Consumes dialogue_labels.encode_assistant_labels output. The model predicts
token t from preceding tokens, so targets are labels[:, 1:], not labels[:, :-1].
This module does not claim a trained conversational model.
"""
import torch
import torch.nn.functional as F


def assistant_causal_loss(logits, labels, ignore_index=-100):
    """Return mean loss over assistant target tokens only.

    logits: [batch, sequence, vocabulary], labels: [batch, sequence].
    Reject all-masked batches rather than silently reporting a zero loss.
    """
    if logits.ndim != 3 or labels.ndim != 2:
        raise ValueError("Expected [B,T,V] logits and [B,T] labels")
    if logits.shape[:2] != labels.shape or logits.shape[1] < 2:
        raise ValueError("Mismatched or too-short sequence")
    targets = labels[:, 1:].to(device=logits.device, dtype=torch.long)
    if not torch.any(targets != ignore_index):
        raise ValueError("No supervised assistant targets after causal shift")
    if torch.any((targets != ignore_index) & ((targets < 0) | (targets >= logits.shape[-1]))):
        raise ValueError("Target token outside vocabulary")
    return F.cross_entropy(
        logits[:, :-1, :].contiguous().reshape(-1, logits.shape[-1]),
        targets.contiguous().reshape(-1),
        ignore_index=ignore_index,
    )
