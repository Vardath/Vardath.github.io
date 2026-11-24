# v61 development checkpoint — roadmap recovery

Source-only change from v60. Windows diagnostics of 24 November show the active v60 installation still holds an old failed indexed draft, no active build and a failed JANUS instruction. This checkpoint does not claim an independently completed mod.

* Resumed indexed correction batches rotate their focus using durable reserved-attempt counts instead of repeatedly starting at the first checks.
* A single-file vanilla ship collision during a fully reviewed roadmap correction now records the inspected source and permits two bounded identifier-selection attempts, surviving restart. A valid model choice is converted to the source-backed macro/index pair and binding in the same SQLite transaction. Existing conflict and coverage guards remain enforced.
* Recovery remains a planning operation: no project files are created, no approval is inferred. A changed inspection digest will not reuse the saved recovery.

New regression module: tests/test_roadmap_recovery_v61.py. CI and real Windows acceptance must be checked before deployment. Next: integrate the verified component bundle into approved Build (including binary artifacts, per-file hashes and reconciliation), then address JANUS failed interpretation and persistent multi-milestone execution. Preserve the executable, models, state, existing UI and shared 30% resource budget.
