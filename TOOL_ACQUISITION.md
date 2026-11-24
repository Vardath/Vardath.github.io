# DeepThorT v33 — add verified script-authoring stage to local tool acquisition

## Working workflow

The v32 recipe flow now allows optional model-generated automation scripts. The model may propose a compact JSON object with the existing `title`, `purpose`, `args`, `artifact` keys and additionally `script: {"path": "automation/task.py", "source": "...complete source..."}`. Arguments use `{{script}}` as one whole argument, so it resolves to the approved project-local script path. The proposed script is stored as candidate data, not written or run. The model's output limit (768 tokens) means large programs need staged implementation through DeepThorT's existing file-plan workflow. This is an initial small-script bridge, not unlimited code generation.

1. Run **Scan this computer** and **Investigate app…** to authorize bounded help, then **Learn procedure…** with a concrete task. App-adjacent docs remain untrusted input.
2. If the returned candidate includes source, select **Run learned procedure…**. A full scrollable SOURCE/DIFF modal shows exactly what would be written. Only **Approve WRITE ONLY** uses the existing workspace writer (project path validation, atomic replace, timestamped backup); the application does not run. Cancel leaves files and actions unchanged. The script must be `.py` for Python/Blender or `.gd` for Godot.
3. Inspect the saved script in the project. Select **Run learned procedure…** again and approve the separately displayed command. It runs through JANUS with `shell=False`, existing CPU/gaming/cancel supervision and bounded log retention. Source changes after staging invalidate command approval and any verified artifact evidence.
4. Inspect result and artifact fingerprints as in v32. Exiting zero or creating a file does not verify correctness, safety or game behavior. No unapproved processes run in this workflow.

The SQLite schema migrates old v32 recipe rows without deletion. Generated script source, hashes, approval timestamps and source-evidence identifiers survive restart. Overwriting an existing project file creates a backup after explicit file approval. A script cannot be used as its own output artifact.

**Limitations:** The current model may not reliably draft valid scripts or understand every app. Python AST parsing rejects syntax errors; Godot syntax is checked only by real approved engine checks. Source review does not sandbox malicious code: users must evaluate any network/file-system operations before authorizing execution. This workflow is not an arbitrary command shell, GUI desktop operator, compiler verification or full app/game creation.

**Validation:** 408 tests across 50 isolated modules (including 9 new tests); an actual supervised Python subprocess wrote and verified a small output artifact. These tests were not performed on the user's Windows PC.

---

# DeepThorT v32 — supervised local application capability acquisition

## Implemented (first operational acquisition layer)

The existing **Computer & Tools** tab contains three additional controls without a new panel:

1. **Scan this computer** — identify installed application executable paths. Only an actual, non-symlink executable file for an explicitly supported command-line application is enrolled; a Windows registry entry alone is not an executable. Discovery performs no launches.
2. **Investigate app…** — select a discovered command-line tool. With explicit user approval, queue a fixed `--help` (or appropriate documented help) command as a JANUS `tool` action. The existing JANUS worker, cancellation, game-priority pause and Windows process limits supervise this invocation. Inspect the actual process log. Only a successful, approved invocation with a current log is accepted as help evidence. App-adjacent README/docs files are also read in a small bounded, non-recursive way without executing the app.
3. **Learn procedure…** — provide a concrete task, e.g. *export a Blender object as GLB* or *export a Godot Android APK*. An ordinary durable chat turn is queued for the *same local* Qwen model, using bounded approved-help and local-documentation excerpts. The model returns a small JSON recipe: title, purpose, exact program arguments and expected project-relative artifact. This is saved as **candidate**; no program runs and no job is queued. Non-JSON, invalid, remote/shell-evaluation or absolute-path commands are rejected.
4. **Run learned procedure…** — select a candidate and review the complete final argument vector, project root and expected artifact. Only the affirmative user approval queues an exact command through the existing JANUS worker; `subprocess` uses `shell=False`. The workflow does not run if a game is active and has existing cancellation controls. Scripts in the project may execute user-defined code: **review them before approving**.
5. Select **Run learned procedure…** again to check the result. It distinguishes a queued/running process, an approved command's successful exit, and a newly created or changed output artifact. The last case records immutable fingerprints for the executable, approved argv, JUL process log and current artifact. These records are persisted in `state/tool_acquisition.sqlite3` and are checked before use in subsequent planning. Changed tools, files or logs invalidate them.

## What the verification means

A successful JANUS process with a *changed output artifact* is an **artifact-level result consistent with the approved command**. It is *not* evidence of a correct animation, working Godot game, validated X4 mod or end-to-end software quality. A zero-exit informational command without an output artifact cannot become an artifact-tested workflow. Other test systems and human/game acceptance are still required.

## Limits and safeguards

- The tool-learning registry deliberately supports a finite list of CLI applications: Python, Git, Node.js, Blender, Godot, .NET, Java, Android Debug Bridge and 7-Zip. It cannot yet operate arbitrary GUI-only desktop applications; those will require a separate, permissioned UI automation adapter.
- No automatic internet research, downloads, package installations, arbitrary shell pipelines, or command evaluation flags. Tool identity is checked again before both approval and evidence reuse.
- Only installed executable identity and a bounded amount of documentation/help are retained. Help and local documents are **untrusted reference material**, not instructions to override the user.
- Tool recipes do not generate their own scripts: if a recipe requires a project script, author and review that file through the existing file approval workflow first. No source file is silently created or overwritten.
- Qwen remains the only free-form code-generation model, so drafting tool recipes can queue behind long planning requests. JANUS can report status without waiting, but cannot independently generate novel script logic yet.
- The local SQLite library and JANUS event history survive restart. No tool action is re-run automatically after restart.
- Process exit status and artifact hashes are not sufficient to prove causality or correctness when other software could write the same file. Such results must remain narrowly scoped.

## Validation

The v32 unit tests cover real-file discovery, immutable executable identity, approved help probes, log tampering, blocked commands, candidate-only model output, approval gates, restart recovery, changed-artifact checks and model context. The integration tests exercise a real approved Python `--help` process, an actual approved project script producing a file, the JANUS supervised worker, and Tk chat/candidate wiring. No Windows PC, Blender GUI, Godot export or game was operated as part of this release verification.
