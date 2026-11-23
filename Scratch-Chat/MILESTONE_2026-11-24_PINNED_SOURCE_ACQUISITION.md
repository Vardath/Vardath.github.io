# Scratch Chat milestone — 2026-11-24: pinned dialogue acquisition

## Verified baseline
GitHub Actions source-test run [45160508915](https://github.com/Vardath/Vardath.github.io/actions/runs/45160508915) completed successfully, including the dialogue/protocol step. This is an older baseline, **not** verification of this milestone.

## Implemented
- `capability/source_snapshot.py` accepts an explicit HTTPS snapshot URL and independently supplied SHA-256, bounds the download, refuses redirects, checks bytes before atomic publication, and removes partial downloads after errors.
- `tests/test_source_snapshot.py` checks URL rejection, byte integrity, overwrite prevention, hash mismatch cleanup, size limit and the mandatory `NOT_APPROVED` state.
- `.github/workflows/scratch-chat-tests.yml` includes this regression suite on push. New CI conclusion remains pending.

## Admission and training status
This utility is an acquisition staging step, **not** source-license verification, approval, privacy review, split decontamination or training. No third-party dataset has been downloaded or approved in this pass. No new model weights, checkpoint, loss metrics or DeepThorT acceptance claims.

## Next substantive work
Select a dataset whose exact immutable revision, contributor terms and license allow intended uses; independently obtain its SHA-256; review original records and consent/privacy; record source manifest and rejected records; split by source conversation; perform exact and near-duplicate contamination audits; then run bounded original-weight SFT and independent multi-turn/tool-use and actual DeepThorT JSONL tests. Do not substitute pretrained weights for Scratch Chat. Free GPU options (Colab/Kaggle) remain unallocated and cannot be assumed.
