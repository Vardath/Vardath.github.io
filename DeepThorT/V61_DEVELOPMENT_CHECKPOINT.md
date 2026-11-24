# v61 development checkpoint — roadmap recovery

Source-only change from v60. Windows diagnostics of 24 November show the active v60 installation still holds an old failed indexed draft, no active build and a failed JANUS instruction. This checkpoint does not claim an independently completed mod.

* Resumed indexed correction batches rotate their focus using durable reserved-attempt counts instead of repeatedly starting at the first checks.
* A single-file vanilla ship collision during a fully reviewed roadmap correction now records the inspected source and permits two bounded identifier-selection attempts, surviving restart. A valid model choice is converted to the source-backed macro/index pair and binding in the same SQLite transaction. Existing conflict and coverage guards remain enforced.
* Recovery remains a planning operation: no project files are created, no approval is inferred. A changed inspection digest will not reuse the saved recovery.

New regression module: tests/test_roadmap_recovery_v61.py. CI and real Windows acceptance must be checked before deployment. Next: integrate the verified component bundle into approved Build (including binary artifacts, per-file hashes and reconciliation), then address JANUS failed interpretation and persistent multi-milestone execution. Preserve the executable, models, state, existing UI and shared 30% resource budget.

## Native asset checkpoint

The project sidebar can explicitly review and materialize a saved request-scoped native attachment into the selected extension workspace, preserving binary bytes and verifying every member against the approved bundle manifest. Refuses conflicting files and safely resumes matching members. Not game installation or full roadmap approval. Geometry lookup is request-scoped; recovering a ship identity can trigger attachment selection in the same planning run. Placement retries are bounded and persisted. Tests: tests/test_native_bundle_v61.py. General Build still needs reconciliation of the materialized asset manifest with subsequent gameplay milestones; no runtime clearance or full mod is claimed. Windows hard-link support and GUI acceptance remain unverified.
