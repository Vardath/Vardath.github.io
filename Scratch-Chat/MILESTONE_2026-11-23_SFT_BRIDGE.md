# Scratch Chat: SFT checkpoint / DeepThorT bridge repair (2026-11-23)

## Verified preceding CI
Source-test GitHub Actions runs [45053676503](https://github.com/Vardath/Vardath.github.io/actions/runs/45053676503) and [45053687987](https://github.com/Vardath/Vardath.github.io/actions/runs/45053687987) both returned completed/success for their unit-tests jobs via the connected GitHub Actions jobs API.

## Implementation
The DeepThorT JSONL bridge previously accepted only the pretraining checkpoint format and used legacy `User: ... Assistant:` framing, while dialogue SFT emits `vardath-scratch-assistant-sft-v1` checkpoints and trains on `<|im_start|>role\\n...<|im_end|>` messages. This prevented using original-weight dialogue SFT checkpoints in the intended bridge and introduced a train/inference prompt mismatch.

The bridge now recognizes both checkpoint formats, reads SFT model configuration from its immutable metadata, uses the training chat framing for SFT inference, rejects injected delimiters, and stops on chat boundary markers. The SFT trainer records the tokenizer SHA-256 in immutable checkpoint metadata when given its tokenizer; the pilot supplies that tokenizer path. The bridge requires a matching hash and therefore rejects older SFT checkpoints without this provenance. Added focused regression tests for prompt framing and reserved delimiters.

Commits: b2fb23a, 2f63457, 831567e, b49491c, 5b2d238.

## Limitations / next actions
These are code changes, not a demonstration of trained conversation. New CI has not yet been confirmed. A subprocess-level JSONL test using a real newly trained SFT checkpoint remains required, along with independent multi-turn and tool-use acceptance. Dolly is still quarantined pending licensing, privacy and contamination review. No GPU access is claimed; GitHub Actions CPU remains suitable only for bounded pilots. No Shakespeare-only experiment was run.
