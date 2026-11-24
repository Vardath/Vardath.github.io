# v61 development checkpoint — roadmap recovery

Source-only change from v60. Windows diagnostics of 24 November show the active v60 installation still holds an old failed indexed draft, no active build and a failed JANUS instruction. This checkpoint does not claim an independently completed mod.

* Resumed indexed correction batches rotate their focus using durable reserved-attempt counts instead of repeatedly starting at the first checks.
* A single-file vanilla ship collision during a fully reviewed roadmap correction now records the inspected source and permits two bounded identifier-selection attempts, surviving restart. A valid model choice is converted to the source-backed macro/index pair and binding in the same SQLite transaction. Existing conflict and coverage guards remain enforced.
* Recovery remains a planning operation: no project files are created, no approval is inferred. A changed inspection digest will not reuse the saved recovery.

New regression module: tests/test_roadmap_recovery_v61.py. CI and real Windows acceptance must be checked before deployment. Next: integrate the verified component bundle into approved Build (including binary artifacts, per-file hashes and reconciliation), then address JANUS failed interpretation and persistent multi-milestone execution. Preserve the executable, models, state, existing UI and shared 30% resource budget.

## Native asset checkpoint

The project sidebar can explicitly review and materialize a saved request-scoped native attachment into the selected extension workspace, preserving binary bytes and verifying every member against the approved bundle manifest. Refuses conflicting files and safely resumes matching members. Not game installation or full roadmap approval. Geometry lookup is request-scoped; recovering a ship identity can trigger attachment selection in the same planning run. Placement retries are bounded and persisted. Tests: tests/test_native_bundle_v61.py. General Build still needs reconciliation of the materialized asset manifest with subsequent gameplay milestones; no runtime clearance or full mod is claimed. Windows hard-link support and GUI acceptance remain unverified.

## Active recovery council

JANUS now retranslates failed planning checks against the exact indexed source and recorded evidence. Sentinel independently accepts or rejects each retranslation; only accepted, bounded advice is eligible for the next targeted implementation call. Further stalls permit another evidence-bound review, and measurable progress discards stale advice. Failed approved test repairs use the same general recovery mechanism with actual saved source candidates and diagnostics. The original specification, approved paths and verification limits remain unchanged. Council inference is leased during multi-turn review. New tests: tests/test_recovery_council_v61.py. Local and Windows execution, CI and extended autonomous runs remain unverified.

## Planning supervision and bounded recovery

JANUS and Sentinel now observe the newest incomplete draft plans as well as the approved job queue. Draft stage changes are durably recorded. When idle, outside gaming, with project work enabled and JANUS unpaused, recognised indexed planning failures can be requeued automatically, at most twice per objective progress epoch. A reviewed section or newly closed check can renew the budget; error wording changes and restarts cannot. Cancelled and superseded plans are excluded. Sentinel rejection is carried into the next council review, never passed to the implementation model as accepted advice. Three recovery-council unit tests were executed in Linux against hash-matching source blobs with mocked inference; all passed. Additional supervision tests added; full CI and live Windows remain unverified.

## Sentinel master-specification guard

The original source is retrieved from the exact approved draft or hierarchical milestone, never a JANUS paraphrase. New indexed section proposals and corrections, regular drafts, approved file goals, generated code and repair proposals receive independent semantic review before acceptance or write. Small specifications are supplied in full; long specifications retain verbatim root intent plus a relevant exact original excerpt in every bounded review. Every candidate chunk receives a verdict. Rejection is recorded and reported to JANUS; it cannot enter the normal source-write path. This is model-based semantic supervision, not a guarantee of perfect interpretation or runtime correctness. Tests use mocked model replies, including the space game versus railway game example. Existing manual edits, native bundle imports and tool execution still need corresponding semantic review integration. No CI or Windows acceptance claim.

## Sentinel-to-JANUS correction loop

Normal (non-indexed) planning now reviews fragments before merging or saving them; previously a semantic rejection occurred only after the complete plan was returned. Recovered fragments are rechecked. Indexed non-X4 planning now includes rejection feedback. On a semantic refusal JANUS proposes a new approach and Sentinel checks that retranslation; accepted guidance joins the rejection diagnostic. Approved text-file generation can attempt up to three distinct reviewed candidates, using fresh inference sessions and unchanged original requirements. No rejected candidate reaches the source write path. A rejected approved file goal still requires roadmap reconciliation, rather than silent changes to approved scope. New regression module tests the correction loop; full CI and Windows live acceptance outstanding.
