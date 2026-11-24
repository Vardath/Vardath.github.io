# DeepThorT v34 — unanticipated failure modes, preflight safeguards and recovery

This release is based on **v33**, with no model replacement, UI panel addition, autonomous execution authority or changes to the existing project approval policy.

## Failure modes addressed

| Failure mode | Behavior in v34 | What is **not** guaranteed |
|---|---|---|
| Executable or generated script changes between approval and launch | New learned-tool actions carry pinned executable identity and script SHA-256. JANUS rechecks immediately before `Popen` and moves stale actions to **needs_attention** without launching them. | It does not sandbox already-approved scripts or eliminate adversarial filesystem changes *during* process startup. Older queued legacy actions have no retroactive snapshot. |
| Selected input or output artifact changes after approval | Approved learned commands pin selected input and expected output state. If the input changes, or a new output appears or an existing output changes, the queued action is blocked. | A program may still write other files or use the network under the Windows user's permissions. |
| Candidate script changes while the full-source approval dialog is open | The script proposal hash and previously displayed target-file hash are rechecked. A different draft or an external edit requires another review. | This is not a multi-process OS transaction or code safety proof. |
| Interrupted file write leaves a `.deepthort-tmp` sentinel forever | Writes use unique exclusive temporary files, flush to disk, recheck approval and atomically replace one file. Prior contents are backed up when overwriting. | A power loss can leave an orphan temporary file; it is not automatically deleted or rolled back. Multi-file project edits are not atomic. |
| A CLI tool hangs indefinitely | JANUS now ends approved **tool** processes after 60 minutes and **verification** processes after 120 minutes, marking the action **needs_attention** and preserving its available log. | A terminated process may already have changed files; never auto-resume without inspection. CPU/GPU scheduling and game-mode cancellation follow the existing system. |
| Tool floods logs or disk is almost full | JANUS terminates an approved process producing more than **8 MB** of log output; refuses to start new actions when less than **150 MB** is available. | The cap applies to JANUS captured output, not arbitrary files an authorized script can write elsewhere. Existing recipe evidence ingestion still requires a much smaller (256 KB) log. |
| A Windows crash damages local SQLite state | **Export diagnostics** now includes bounded read-only database quick-check results and free-space metadata, without copying full SQLite databases or prompts. | This detects some errors; it does **not** repair or back up damaged databases. Back up `state` before updating. |
| GUI tests fail because stale Tkinter windows influence later modules | `regression_cli.py` runs every test module in a separate process and uses a fresh Xvfb display on Linux, with a machine-readable result option. | This is test isolation, not a fix for the underlying combined-process Tkinter teardown warnings. |
| An internal project symlink redirects a user-approved write | Project file writes now reject symlink components even when the symlink target is within the workspace. | Manually run external tools can use filesystem paths outside the workspace. |

## How to exercise the new safeguards (Windows)

1. Back up `D:\deepthort\state` and close DeepThorT.
2. Extract `DeepThorT_Desktop_v34_Windows.zip` over `D:\deepthort`, retaining `models`, `node_modules`, `cache`, `reference`, `state` and projects.
3. **Computer & Tools → Scan this computer**. Choose a small disposable project (not an irreplaceable game/mod).
4. Use **Investigate app…** on Python or Git (approve a help probe), then **Learn procedure…**. Review and stage any proposed script, *without* executing it.
5. Review the proposed command separately. Use a disposable output path for the first execution. In **JANUS & Sentinel**, check the action and its output log. A passing exit code is not gameplay or task correctness.
6. For a deliberate tampering test, approve a generated script and modify that script *before JANUS launches the queued command*. The runner should mark the action **needs_attention** without launching it. Avoid running this test on real project files.
7. Use **Export diagnostics**. Confirm that `summary.json` has `state_health`, with no prompt or SQLite record contents. If an unfamiliar error appears, send that ZIP; do not attempt forty X4 planning passes merely to gather diagnostics.

## Scope of verification

Regression tests cover hash mismatches, old-schema migration, approval-dialog races, output appearance, input changes, internal symlink rejection, hanging tools, oversized stdout, low disk space and on-demand database diagnostics. Tests use a local Python process and synthetic project files. These results do not prove Blender automation, Godot exports, actual Xenon PE performance or Windows GUI operation on the user's PC.

## Remaining important gaps

- **Scripts are not sandboxed:** Python and GDScript can access arbitrary paths, network devices and OS APIs. The review dialog now explicitly warns about this and flags selected risky imports/calls. A real Windows sandbox/container requires separate engineering and testing.
- **Untrusted documentation and stdout are only reference material**, never authoritative instructions.
- **Large game projects still require actual end-to-end acceptance tests**, asset verification, engine-version-aware adapters, dependency resolution and manual review of security-sensitive changes.
- **Concurrent external modification between the final hash check and process startup remains possible**. Preventing hostile races requires OS-level process and filesystem isolation rather than further prompt instructions.
- **No automatic remote/cloud tool discovery or unapproved installers** were added.
