# DeepThorT hierarchical development — v25 (Pass 4, first implementation)

## What was implemented

DeepThorT v24 could store and review enormous specifications, but could only submit a **single plan containing at most 24 files**. v25 adds `deepthort_local/hierarchical_planning.py` and a durable `state/hierarchical_plans.sqlite3` roadmap. The local model remains the only source of file names and implementation descriptions; the roadmap does not manufacture them.

After **all original specification sections** have received parseable model proposals, the roadmap:

1. Checks every original section hash and the entire specification fingerprint against `specification_index.sqlite3`.
2. Validates the **aggregate** model-authored plan using the existing project-specific validator. A partial milestone does not substitute for this global check.
3. Records the precise source-section -> proposed file -> milestone associations, including source hashes. All sections must map to at least one proposed file.
4. Rejects incompatible descriptions of the same file across sections rather than silently overwriting one. Files which require more original source text than the local inference can handle are also blocked for explicit model reconciliation. No requirements are silently dropped.
5. Splits accepted proposals into independently scheduled milestones, no more than **12 files by default** (and never above the existing 24-file queue limit). Milestone scopes quote source sections **verbatim** and contain the master specification's SHA-256 fingerprint. Neither an imported full specification nor its index is replaced by a shortened summary.
6. Uses conservative **sequential** scheduling. This is a verification dependency, **not** an assertion that JANUS has independently discovered all architectural or API dependencies.

The roadmap's database is independent from the existing conversation, job and specification databases. On restart, the app recovers it and rejects a roadmap when its master specification or indexed model proposals differ.

## Approval and usage

1. Install v25 over v24, preserving `state`, `models`, references and projects.
2. Submit a large specification using **Draft project plan**; the import shortcut **Ctrl+Shift+O** is unchanged. Large specifications remain indexed in complete sections, up to 40 model calls per invocation. If some sections remain, retry the interrupted draft to resume saved progress.
3. When all sections have been reviewed and the aggregate file plan passes validation, chat displays **ROADMAP READY**. **No build job is queued at this point**.
4. In that same chat and project, click the existing **Approve plan & queue** control. The confirmation shows the next milestone number, source-section references, master hash and file stages. Only that milestone is queued following explicit confirmation.
5. Each proposed file still requires the pre-existing file-review/save process. When all are saved, the build waits for the existing explicit **Verify build** action. Successful command exit alone does not mean the game is fully working; it proves the approved check passed.
6. Only when the approved build job records **Verified: test command exited 0** and all milestone file steps are saved can the milestone be marked verified. The next milestone then becomes separately approvable using the same button. Failed, cancelled, paused and merely saved jobs do **not** advance the roadmap.

Ordinary plans that fit the old single-plan flow still use the existing draft approval and execution process. No new buttons, automatic permissions, cloud inference, new models, JANUS/Sentinel topologies or game-facing UI changes have been added.

## Scope of traceability and limits

- **Traceability is structural, not semantic**: the roadmap proves that each original section was reviewed and associated with model-authored file proposals. It cannot prove that a proposed file correctly implements every requirement contained in the section.
- The model does not yet extract atomic requirements or reason over every cross-milestone architectural dependency. Sequential gates reduce one failure class, but may be overly restrictive and do not guarantee good design.
- Exact text associated with one proposed file must fit in a bounded local inference scope. Cross-section shared files with very large combined requirements are rejected pending deliberate reconciliation. This is not a loss of source text.
- A model request remains limited to approximately 7,500 characters. The new scoped milestone context is capped at 6,500 characters, with a lower excerpt budget. Generating an edit for an already-large existing file can still exceed that limit, in which case it fails safely rather than truncating the source.
- For enormous projects, it may take many batches of 40 local model requests to review all sections. v25 eliminates the post-review 24-file blocker, **not** the 1.5B model's cognitive or inference-speed limitations.
- Only source files generated through explicitly approved stages can be queued. Compilation, Android export, and game testing still require real installed tools and separately approved verification commands.
- A successful test exit is evidence for that specific check; it is not proof that Faction Command or an X4 mod is feature-complete.

## Acceptance tests

`xvfb-run -a python -m unittest discover -s tests -q` — 263 tests passed locally on the v25 source. Added tests cover 25+ file plans, exact section traceability, stale master index and altered model proposals, duplicate/conflicting paths, bounded file groups, restart persistence, idempotent approvals, job-identity and verification gates, Android game classification when X4 is cited as inspiration, and an actual Tk desktop confirmation flow. Windows ONNX inference, game-engine builds, live cancellation of a milestone, and game runtime correctness have not been tested here.

## Further passes

**Pass 5** should add semantically identifiable requirement IDs, deliberate model-authored subsystem/API dependency graphs, project-wide invariant reconciliation, retrieval of previous verified interfaces when implementing later milestones, adaptive prompt budgets, and measured inference/build benchmarks. It should then verify actual Xenon PE mod output and progress toward Faction Command. None of these acceptance results should be presumed from this release.
