# DeepThorT v28 — source contracts and test-evidence gates

This pass builds on v27's original-specification reconciliation and approved test-source fingerprints. It **does not** claim to understand arbitrary game requirements, generate behavioral tests autonomously, run programs without consent, or certify gameplay.

## Explicit contract declarations

For fully indexed hierarchical plans, the model may put explicit declarations *in the description of files it actually proposed*:

- `; provides: save_orders` — a Python file promises to expose a top-level symbol `save_orders`.
- `; uses: src/orders.py::save_orders` — a Python consumer promises to import `save_orders` from that planned Python provider.
- `; verifies: REQ-14` — a planned test file declares a test intention linked to a **user-written** `REQ-14` label in the exact source specification.

Example plan fragment (model output, not a built-in game plan):

```json
{"files":[
  {"path":"src/orders.py","description":"Save orders; provides: save_orders"},
  {"path":"src/ui.py","description":"Invoke order storage; uses: src/orders.py::save_orders"},
  {"path":"tests/test_orders.py","description":"Check order persistence; verifies: REQ-14"}
]}
```

Source code is read with a static Python AST parser, **without executing or importing** it. A declared symbol missing from a present Python module, a missing declared import, or a test file with no discoverable Python test functions is reported as a failure. A not-yet-created file is **pending**. Non-Python test code is not asserted to have runnable tests merely because a filename looks right. Labels that were not written into the source specification cannot be fabricated by the model. Unlinked labelled requirements are reported, not silently considered satisfied.

The roadmap approval dialog shows the declared-contract count, number of explicit labelled requirements with no test linkage, and current static issue count. The original approval button remains the only way to queue a milestone. At approved verification reconciliation, a hard static contract violation keeps the milestone waiting for another verified test. Repairing a file does not redeem previous results.

Uncertain phrases such as "approximately", "perhaps" and "if possible" are shown as anchored **nonblocking review candidates**; DeepThorT does not invent their exact meaning, use them to change the request, or require user input for every occurrence.

Inspect a planned project without executing code:

```powershell
python -m deepthort_local.acceptance_contracts "D:\projects\game" "D:\projects\game\plan.json" "D:\projects\specification.txt"
```

Exit 0 indicates **no confirmed static contract defects**. Exit 2 indicates a concrete static defect, **not** a failed game run. The JSON report always has `acceptance_confirmed: false`.

## Real tool exit evidence

DeepThorT's **existing** approval-based Verify build runner now retains a bounded tail of the actual command output, then assesses it after exit:

- Python `unittest discover`: exit 0 **and at least one reported passing test**, with `OK` present. `Ran 0 tests` fails verification even with process exit 0.
- `.NET test`: requires a reported positive passing-test count. An exit-zero `dotnet test` that reports no tests cannot validate a milestone.
- Godot headless `--editor --quit`: exit 0 is clearly labelled an **editor load**, not a gameplay or APK test.
- Other approved tools: process exit 0 is recorded as an **exit check only**, not a behavioral acceptance demonstration.

A successful check attaches its command/output hashes and evidence class to v27's exact saved-source snapshot. Old v27 snapshots remain readable; they are not retrospectively upgraded into test-level evidence. Modifying saved files invalidates snapshots and requires fresh user approval. A project/test process is still capable of producing misleading output; these checks do not prove that its reported assertions genuinely test the full specification.

## Boundaries and next priorities

- No second model, cloud service, new UI control, game-engine operation, increased CPU usage, or new automatic execution permission.
- Only *explicit* source/model declarations are checked. No invented dependencies or guessed API names.
- The planner still uses at most 40 attempts and the unchanged exact-source section index. It is prompted to make relevant declarations, but weak model output may omit them.
- Static Python checks do **not** validate TypeScript, GDScript, XML semantics, imported native modules, dynamic Python APIs, real X4 weapon loadouts, Android build artifacts or gameplay.
- For Faction Command, next validate actual Godot/Android engine tools and add concrete behavioral acceptance harnesses tied to user requirements, while preserving the user-approval and source-hash boundary.
