# DeepThorT v40 — project-scoped unattended work (23 November 2026)

## Why this pass exists

v39 could install curated routine software following an approved plan, but each
generated project file and each verification still generated a separate modal.
That made even small multi-file development jobs stop after each stage. v40
adds bounded, durable authority tied to the user's **one explicit plan or
milestone approval**. It does **not** turn arbitrary chat into a job.

## Implemented

- New `deepthort_local/project_authority.py`: persisted policy
  (`state/project-work-policy.json`) and per-job receipts
  (`state/project-grants/job-N.json`), with exact project root, approved job
  identity, plan fingerprint, max 24 individual files, pre-write SHA-256 of
  existing targets, a 30-day expiry, generated-file SHA receipts and revocation.
- Work queue checkbox **Continue approved file steps and fixed tests without
  repeated prompts** (enabled on first use, per owner's instruction) and
  **Revoke selected job automation**. Switching off prevents future automatic
  actions but does not cancel work already running; use Stop tool for that.
- Every approved draft, milestone and legacy build-plan dialog explains that
  this approval, when standing project work is enabled, also authorizes
  bounded writes and supported local test profiles. A separate grant is
  created after the approved job actually exists. No model output can create
  a grant. If grant creation fails, ordinary manual review still works.
- Generated files are saved through the **existing** `apply_approved_file`
  atomic writer and timestamped backups. A file or path changed since plan
  approval does not automatically overwrite; work falls back to manual review
  or needs attention. Paths containing hidden/protected project components,
  executables, installers and Windows script launch formats never receive
  unattended file grants.
- Once ALL planned files have exact saved-file receipts and the job is
  waiting for verification, an idle GUI tick can start only the deterministic
  existing Python, npm, .NET, Godot or X4 validation entry points, with
  `shell=False`, a 2-hour test runtime cap, game/queue/JANUS/resource gates,
  and no repeat confirmation. Failure stops the job for inspection rather than
  claiming completion or silently retrying.
- The previously added exact-source snapshot, Godot/X4 acceptance audits and
  requirement/milestone verification gates remain authoritative. New source
  fingerprints are evidence of what was written, NOT correctness.
- The original ONNX inference server, model, JANUS/Sentinel cognition, Windows
  launcher and existing installed state are unchanged.

## Limits that still matter

This is a **per-job standing authorization**, not a general autonomous task
graph. Each new milestone is still separately approved. The current queue
does not automatically design a repair or launch a new independent build after
a failed test. Generated project tests may run untrusted project code with
the Windows user's normal privileges: a fixed test command is NOT a sandbox.
The default-on policy is intentionally visible and can be disabled before
approving a plan. Manual generated scripts, arbitrary tools, unknown packages,
deletes, credential access, publishing and elevated operations are NOT
granted unattended authority.

Existing automatic writes use timestamped backups, not Git commits or a
multi-file transaction. A crash mid-operation can leave earlier files saved;
the grant, job steps and file hashes must reconcile before further automatic
work. JobStore's historic interrupted-running transition is to **paused**,
not automatic replay of an uncertain tool run. After restarting, inspect
an interrupted job and resume deliberately.

A source hash and an installer exit code are not independent proof of safe
project code, a working game or an installed application. Linux virtual-display
tests cannot demonstrate native WinGet/UAC, physical-machine ONNX inference,
Blender/Godot GUI operation or X4 gameplay.

## Validation and deployment

- New `tests/test_project_authority_v40.py` covers policy, authorization,
  exact file and project binding, changed existing files, backups, revocation,
  restart, test profile confinement and tamper rejection.
- Run GitHub Actions `DeepThorT tests` for full isolated regression.
- Update an existing v39 install at `D:\\deepthort` by overlaying source
  files. **Keep** the v39 `DeepThorT.exe` launcher,
  `models`, `state`, `node_modules`, `reference`, `cache`, and projects.
  Do not delete local Windows-only files. Back up `state` first.
- Approve a plan for a disposable local Python project and verify automatic
  stage saves plus actual unittest execution. Edit a planned file externally
  between approval and generation: unattended write must stop. Disable the
  work preference and repeat: each step must return to review. Revoke a grant,
  pause the queue, run a game, and confirm no new automatic test starts.
- Export a diagnostic ZIP for Windows failures; check actual process output
  and artifacts rather than interpreting a Python test as game validation.

## Next passes

v41: resilient task graph (step-to-test-to-repair with bounded retries),
versioned Git checkpoints/undo, better interrupted-process reconciliation,
and post-install executable/version probes. Following passes: deeper
requirements-to-tool resolution, signed provenance and safe acquisition,
versioned application adapters, GUI-only automation and real game acceptance.
