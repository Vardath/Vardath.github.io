# Scratch Chat — held-out answer leakage gate (2026-11-23)

## Verified baseline
GitHub Actions source-test run [45121940179](https://github.com/Vardath/Vardath.github.io/actions/runs/45121940179) completed successfully (unit-tests job, compilation and dialogue/protocol suites). This baseline **predates** the changes below.

## Changes
- Cross-split lexical Jaccard audit now screens both user prompts and assistant answers, comparing each type separately. Previously repeated assistant completions could enter independent evaluation splits when user prompts differed.
- Preserves the indexed candidate-pair approach and record-count semantics; findings identify `kind: prompt` or `kind: answer`.
- Rejects assistant replies with no normalized lexical tokens.
- Added three regression tests, updated prior fixtures to avoid unintended duplicate answers, and included the new suite in `.github/workflows/scratch-chat-tests.yml`.

Commits: `ff759db75fc9880efbb2c809787132c9d3d381e6`, `b95fa1fdb3d198773c5278cd68e960a7a4b10144`, `c98edfdbf64cb9394e9ee48f4232c8794bb4fa4a`, `8bc747802b41ee587301fc9361d5338037c2f826`.

## Limitations and next work
This is **lexical**, not semantic or embedding-based decontamination; legitimate short generic answers can produce false positives and require explicit review rather than disabling the gate. No newly licensed corpus has been admitted, no dialogue-trained checkpoint has been produced, and no actual DeepThorT conversational acceptance is claimed. Dolly remains quarantined. GitHub Actions CPU remains bounded pilot infrastructure only. Free GPU options require checking current eligibility, quotas, dataset permissions and checkpoint persistence before using them.

Follow-on CI is triggered by push commits but must be checked independently; no green result for these changes is claimed here.
