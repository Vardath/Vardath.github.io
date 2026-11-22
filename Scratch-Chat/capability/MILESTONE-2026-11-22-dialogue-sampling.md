# Dialogue SFT sampling milestone — 2026-11-22

## Verified baseline
GitHub Actions run 44976935600 unit-tests job completed successfully, including source compilation. That run predates this change.

## Change
Original-weight SFT previously selected training records in fixed input order, with `train[(step - 1) % len(train)]`. Short CPU pilots repeatedly exposed only the first records and could be mistaken for representative dialogue training. Now each epoch uses a deterministic seed-derived permutation, covering every record once per full epoch and permitting exact schedule reconstruction from the saved step and seed. The training report records number of distinct examples visited, completed epochs and sampling strategy. Regression tests cover permutation completeness and resume indexing.

## Unverified
These new commits have not yet been verified by CI. No new model weights trained, no external corpus admitted, no independent conversational or DeepThorT application acceptance established. Seeded sampling does not fix inadequate model capacity, small datasets, or lack of GPU compute. The trainer still rejects overlength records; it does not yet support long-context windowing. Existing checkpoints produced under the old cyclic schedule must NOT be resumed as if they were produced by this new schedule: checkpoint format/version and migration gate are a follow-up requirement.

## Next
Version the sampler in checkpoint immutable provenance before allowing resume, acquire a reviewed revision-pinned external dialogue corpus, perform bounded original-weight pilot and independent acceptance. No Shakespeare-only benchmark may be represented as conversational progress.
