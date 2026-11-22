# DeepThorT v26 — requirement intelligence and measured planning performance

## Scope of this implementation

This is a conservative Pass 5 foundation, **not** semantic mastery of a million-word game specification.

1. `requirements_intelligence.py` extracts exact, hash-checked candidate spans from completed indexed specification sections. Lists, numbered requirements and headings become identifiable candidates; unstructured prose is preserved as separate candidates rather than discarded. Stable identifiers are scoped to the indexed master source. At most 64 candidate spans per section are emitted; additional text stays within the last grouped span and is not truncated.
2. `HierarchicalPlanStore` stores the source offsets, hashes and source-scope associations in `hierarchy_requirements`. The `requirement_report(...)` API exposes candidate text, source offsets and the file/milestone intentions linked to that section. **A link is not a claim that the requirement is implemented, semantically understood or tested.**
3. A model may explicitly declare a dependency inside a proposed file description: `; depends-on: path/to/required_file.ext`. The section-review prompt now explains this optional syntax. Dependencies are never inferred from words like “UI” or “database.” The system rejects unknown files, self-dependencies and cycles; stable topological ordering places required files before dependents. Graph edges persist in `hierarchy_dependencies`; changed or injected edges invalidate the roadmap. Independent milestones remain sequentially approval-gated as in v25.
4. A local numeric-only timing report is available without any model inference:

   ```powershell
   cd D:\deepthort
   python -m deepthort_local.planning_metrics D:\deepthort\state\logs
   ```

   It reads existing rotating `model_client.jsonl` and `planner.jsonl` files. It reports durations, malformed replies, passes with new files and progress. It does not copy prompts, model answers, file paths or credentials.
5. `dependency_order` uses a stable heap-based topological order with roughly O((files+edges) log files) complexity, rather than repeatedly scanning every remaining file. This is a scalability improvement for large roadmaps. It is **not** an observed reduction in ONNX generation time.

## What performance data actually says

Running the new read-only reporter against the **earlier** November 22 16:27 diagnostic export (not a v26 Windows run) yielded 139 completed local-model requests, with median 539.59 seconds, mean 544.61 seconds and maximum 1471.22 seconds. There were 45 logged planning passes, 10 malformed-format passes, and just 6 passes with newly accepted files. These logs cover earlier versions and multiple activities; this is a historical reference, **not** a controlled v25-versus-v26 performance benchmark.

The dominant inference-time problem remains the local 1.5B Qwen model's long-running generation under resource limits. No new model, cloud service, hardware acceleration or unsafe background execution has been introduced.

## Compatibility and approval

- Existing v25 roadmap databases are migrated by adding new tables; previous roadmaps without candidate rows remain accessible.
- Source SHA-256 and stored model-file intentions are still checked before reporting, approval and milestone advancement.
- The 24-file per-job ceiling, normal 12-file milestones, 40 planning attempts, JANUS/Sentinel, offline ONNX model, chat GUI, saved sessions, explicit approval and verification gates are unchanged.
- No source file is created from a requirement candidate. Only the model proposes file intentions, and approved work stays in the existing job queue.
- A verified build result only establishes that its *specific authorized check* succeeded; it cannot prove full gameplay correctness.

## Remaining engineering work

- **Semantic requirements:** ask the model to reconcile intent, contradictions, acceptance criteria and APIs across source sections, with validated references; the current candidate IDs are anchored text only.
- **Cross-file interface analysis:** inspect real project APIs/types and actual compiler output. Optional dependency declarations are a start, not a verified dependency graph.
- **Inference efficiency:** profile and benchmark live Windows model runs, memory use and context/prefill performance. Do not claim speedups without paired measurements.
- **Real acceptance:** produce an X4 PE mod, confirm X4 XML IDs and equipment, validate in game, then run Faction Command Android builds and automated gameplay tests.

## Local verification

The v26 test suite checks migration-safe candidate indexing, source fingerprint validation, dependency ordering/cycles, persisted reports, job gating compatibility, scaled dependency chains and privacy-safe timing output. The full suite is run in a virtual X display; this does not verify live Windows inference, Android exports or X4 gameplay.
