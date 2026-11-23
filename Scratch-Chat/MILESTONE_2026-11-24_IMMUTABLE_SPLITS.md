# Scratch Chat milestone — 2026-11-24: immutable dialogue splits

## Verified baseline and limits
The connected GitHub Actions job lookup for run 45160508915 reports completed/success for the Scratch Chat source-test job. This is a previous baseline, not verification of this change. Commit-workflow lookup for a352d3b returned no associated runs; that endpoint is PR-oriented and does not establish absence of push runs.

## Changes
- Split preparation now refuses to overwrite any preexisting output artifacts, preserving independent evaluation partitions and their digests. An empty existing directory is permitted.
- Added tests/test_immutable_dialogue_splits.py for repeat invocation with a different seed and preservation of unrelated files.
- Added the tests to the push-triggered Scratch Chat source-test workflow.
- Commits: fdfc2c6, 990b024, b3387e0.

## Unverified and next work
These new tests have not been observed passing in GitHub Actions at the time of this note. The current split writer is not transactionally atomic for interrupted first writes; follow-up should stage then publish a complete directory and verify no preexisting path is overwritten. Cross-source semantic deduplication remains unproven.

No licensed external dialogue snapshot was acquired or approved, no dialogue checkpoint trained, no new conversational metrics, and no actual DeepThorT application acceptance. Do not infer readiness from Shakespeare token loss or transport-only tests. The highest-priority blocker remains a provenance-reviewed, pinned dialogue corpus and access to feasible training compute.
