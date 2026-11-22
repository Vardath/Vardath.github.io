# Scratch Chat dialogue turn-order admission milestone — 2026-11-23

Verified prior GitHub Actions run [45035111424](https://github.com/Vardath/Vardath.github.io/actions/runs/45035111424): unit-tests completed successfully. This verification predates the current changes.

Commits:
- 582c3f2938980028397ca7f487a14289cc6af179: fail-closed role sequence validation at the external dialogue admission gate.
- c01495ac972da97a0fb4bae509c5dae1205a517e: regression tests for malformed assistant, user, tool and system ordering.

The source-test workflow is push-triggered on Scratch-Chat paths and already discovers test_dialogue*.py. GitHub's connected commit-run lookup only returns PR-triggered runs; this pass cannot establish the status of the new push CI. Do not report these tests as green without completed job evidence.

The validation rejects orphan tool messages, consecutive user requests, assistant responses lacking a preceding user/tool turn, late system messages and conversations not ending in an assistant answer. It does not yet validate structured tool-call identifiers or guarantee multi-turn quality.

Dolly remains quarantined, not licensed/consent-approved for training. No external-data training, checkpoint, free GPU allocation or actual DeepThorT application acceptance occurred. Next: inspect follow-on CI, address source provenance and privacy review, train on admitted dialogue from random initialization, then independently evaluate conversations and JSONL tool round-trips.
