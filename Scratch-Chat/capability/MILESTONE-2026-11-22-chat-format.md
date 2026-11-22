# Scratch Chat capability milestone — 2026-11-22

## Verified repository changes
- Added `capability/chat_format.py` to serialize multi-turn role-delimited dialogue and return character spans for assistant responses (including end-of-turn markers).
- Added `capability/test_chat_format.py` with deterministic serialization, assistant span, delimiter-injection and JSONL conversion tests.
- These are preparation utilities, not a tokenizer or trainer integration. A training implementation must map character spans to token spans correctly, including boundary-crossing subword tokens, and mask all non-assistant labels. The model tokenizer must reserve delimiter tokens before training.
- Earlier GitHub Actions run 44958336270 failed on a duplicate-leakage regression assertion. The preceding run committed a targeted assertion fix; its follow-on result has not been independently verified here.
- This run's two source commits were accepted by GitHub. No passing CI, dataset ingestion, checkpoint, trained-model quality, or DeepThorT end-to-end test is claimed.

## Immediate capability gates
1. Review and pin genuinely redistributable dialogue data with explicit license, source revision and privacy review; retain original hashes.
2. Produce group-isolated, decontaminated train/validation/test splits; preserve independent evaluation prompts.
3. Integrate tokenizer-aware assistant-only label masking and prove it on tiny controlled batches.
4. Train original randomly initialized weights, store deterministic config, seeds, optimizer state and checkpoint hashes.
5. Run independent multi-turn, tool-use and actual DeepThorT JSONL integration acceptance; record failures without inflating capability claims.
6. Use CPU Actions for bounded verification only; investigate externally available free GPU offerings without assuming allocation.
