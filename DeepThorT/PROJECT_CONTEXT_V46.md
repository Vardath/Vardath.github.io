# DeepThorT v46 — diagnostic-driven planning and inspection corrections

Date: 23 November 2026; prior release v45 commit `92522874494efcdfde3e0beb336d11cc7fafdb6d`.

## Field diagnostic interpretation
The Windows 10 diagnostic report was consistent with a correctly selected `D:\x4mods` workspace, usable Qwen ONNX, and verifiable installed Xenon PE reference files. Multiple X4 planning passes failed the complete domain-specific file-plan validator, and separate local ONNX requests encountered connection resets. No successful approved build or native X4 playtest was shown by that report. Slow planning alone is not considered a defect under the 20% process limits.

## Implemented
1. A project-scoped exclusion registry stored under DeepThorT `state/`, not inside the selected game or output folder. The original source file is never opened for mutation, moved, deleted, or uninstalled. Right-click menu on the left Tk Treeview offers exclusion and restore controls. A newly selected folder immediately clears stale previous rows. Pending asynchronous inventory refreshes are filtered a second time at UI render.
2. The same excluded file is omitted from bounded local capability/manifest and reference auto-indexing. Previously indexed, auto-observed evidence of an excluded file is purged immediately. X4 preflight's superficial project-file preview omits excluded top-level files; actual vanilla reference inspection remains independent of this filter. Manually approved file plans and explicit file edits still require their existing project/approval constraints.
3. `PlanContinuation` stores structurally validated model-proposed steps after each accepted revision, with atomic JSON replacement. Its identity binds exact resolved project root, complete request, effective prompt/attachment contents, and source evidence to prevent stale cross-request reuse. Saved data is re-parsed against the current workspace safety constraints and fully domain validated before it may become a draft. A successful validated draft clears its partial checkpoint. No file contents are generated or hardcoded. Existing 40-pass planning cap is unchanged.

## Limits and next pass
This pass does not silently retry a crashed ONNX server or treat an installed X4 game as safe to launch unattended. Windows runtime and physical-mod tests require the user's actual environment and diagnostics after update. State under `D:\deepthort\state` is expected to remain in that folder; `D:\x4mods` is the project output root, not the durable execution-state folder.
