**v28 continuation:** `ACCEPTANCE_CONTRACTS.md` describes explicit test/API contract tracking and guards against zero-test verification. These checks do not establish game-behavior correctness.

---

# DeepThorT v27 — conservative requirement reconciliation and evidence freshness

**Release scope:** Pass 6 of the Capability Library and hierarchical game-development work. The original desktop layout, 40-pass planning allowance, JANUS/Sentinel topology, local ONNX model, Windows launcher, project backups, and explicit approval boundary are unchanged.

## Implemented

1. **Original requirement conflict detection.** Before saving a new hierarchical roadmap, DeepThorT checks *verbatim, anchored* `must`/`shall` requirements for exactly opposing demands on the same normalized subject and action. It also detects impossible numerical bounds when the same subject, action and unit are explicitly constrained, such as `Stations must support at least 100 docking bays` versus `Stations must support at most 50 docking bays`. Direct conflicts stop roadmap creation and display both source statements; no assumed preference or automatic rewrite is applied. Conditional qualifications and ambiguous paraphrases are *not* automatically flagged. `should` statements do not override mandatory requirements.
2. **Explicit requirement dependencies.** `REQ-1: ...` and `REQ-2: ...; depends-on: REQ-1` are recognized as user-supplied dependency declarations. Duplicate labels, missing referenced IDs, self-dependencies and cycles are rejected. These edges are auditable evidence, not a claim of inferred semantics or proof that the corresponding code files are adequate.
3. **Proposed acceptance criteria.** Original, explicit modal requirements are returned with exact specification section and character offsets, stable requirement candidate IDs, and a `verification_state=unverified`. These are *obligations to test*, not auto-generated passing tests or proof that a game feature works. Unstructured prose is still retained in the full specification index, even where no direct test criterion is extracted.
4. **Read-only local Python interface inspection.** For planned `.py` files that exist, the checker parses Python AST without importing/executing code. It flags syntax errors and missing symbols in statically resolvable `from <planned local module> import <symbol>` relationships. Missing planned files remain `pending`, not `verified`. Dynamic module exports, third-party imports, native modules, and non-Python code cannot be validated by this static checker. Paths must remain inside the approved project (including symlink resolution).
5. **Fresh approved verification evidence.** Once an approved desktop build verification test reports exit 0, the application records SHA-256 hashes of the actual planned files. A changed, deleted or replaced file invalidates that test's evidence. An already verified milestone is demoted when stale evidence is detected; later verified milestones are demoted as well because they may depend on the changed prerequisite. The user must approve another test through the existing **Verify build** control before progress resumes. This changes no source or permissions automatically. Older v25/v26 verification rows without file hashes remain readable but cannot retroactively provide hash-level guarantees.
6. **Static interface verification gate.** When a previously approved verification result is being reconciled, confirmed syntax errors and missing locally declared Python exports prevent promotion. The job is returned to `waiting_verification`, with the reason recorded in its job detail. After repairing code, the user must explicitly re-run the build check; editing code alone cannot redeem an earlier green result.

## Read-only inspection commands

In the installed application directory, without starting a game or changing any files:

```powershell
python -m deepthort_local.semantic_reconciliation requirements "D:\projects\game-specification.txt" --limit 100
python -m deepthort_local.semantic_reconciliation interfaces "D:\projects\my-game" "D:\projects\my-game\proposed-plan.json"
```

The `interfaces` input can be `{"files":[{"path":"src/module.py","description":"..."}]}` or an array of those entries. These commands emit JSON. Exit status `2` indicates detected blocking contradictions or static-source problems; `0` means *no issue detected by that limited checker*, **not that the game or plan is correct**. The commands are read-only and do not run model inference or project code.

## Verification and limits

- All original specification content remains in its indexed, hash-checked store. No requirements are dropped or silently resolved.
- Acceptance obligations are candidates derived from recognized explicit wording. Natural-language semantic equivalence, feature quality, gameplay behavior and cross-language API compatibility remain unproven.
- Requirement source links remain section-level until individually confirmed by actual implementation/test evidence. A model-authored file description does not prove a requirement has been implemented.
- Explicit `REQ-N` ordering does not automatically infer file-level dependencies. Previously model-declared file dependencies continue to control milestone ordering; ambiguous cross-subsystem relationships require further modeling and proof.
- New source snapshots cover only the explicitly approved files for one bounded milestone. Hash equality proves byte identity since the last recorded successful test, not test quality or completeness. It cannot certify arbitrary runtime behavior.
- Existing older job records without v27 snapshots are preserved rather than falsely upgraded.
- Local Python checks are bounded; a full Android/Godot/C# interface graph, machine-executed acceptance tests, and robust autonomous replanning are subsequent stages.
- Passing local Linux regression tests does not establish live Windows ONNX inference performance, X4 in-game validity, or an Android APK build.
