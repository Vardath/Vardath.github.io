# Independent acceptance evidence — 2026-11-23

Baseline: Scratch Chat source-test run [45156685535](https://github.com/Vardath/Vardath.github.io/actions/runs/45156685535) completed successfully on `a741a1c` (verified via Actions runs endpoint). This is a source test, not dialogue training or a capability pass.

Changes: `capability/independent_acceptance.py` now retains each JSONL request and parsed provider response in its machine-readable report, in addition to grades, enabling review of actual generated outputs rather than relying only on booleans. Explicit `conversation_ready=false` and `tool_use_evaluated=false` prevent interpreting diagnostic subprocess success as full readiness. Regression tests assert evidence retention and status flags. Commit chain starts at `39fdcd0`.

Caution: raw responses may contain user-provided sensitive text; run only with synthetic/private approved evaluation probes, protect output reports, and do not publish real user prompts. The existing runner supplies fixed synthetic probes.

No new external dataset admitted, no new checkpoint trained, no Shakespeare-only runs, no model-quality improvement claimed. Dolly remains quarantined. Outstanding: revision-pinned and independently licensed dialogue data, actual privacy review and split decontamination, original-weight dialogue training, checkpoint hashes and repeatable resumes, independent multi-turn and tool-use capability tests, and actual DeepThorT host JSONL integration. GPU availability remains unverified; Actions CPU is for bounded pilots only.

Follow-on push CI must be verified separately; successful file commits do not establish passing tests.
