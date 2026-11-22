# Capability Library — Pass 2 local reference learning (v23)

This builds on the v22 observation/procedure database. **Implemented, not aspirational:**

- Auto-discovery reads at most 200 eligible workspace file entries, indexes at most 20 matching documentation or example files (each at most 48,000 bytes), and never executes project code. It looks for `README`, common text documentation inside `docs`, `manual`, `api`, `guides`, etc., and code examples inside `examples`, `samples`, or `tutorials`.
- The SQLite `local_references` table stores only project identity, relative source path, SHA-256, byte count, documentation/example classification, an **unverified** source-version label, selection origin and index time. It does **not** store source contents.
- Retrieval reopens and re-hashes each file. Removed, edited, escaped, binary, oversized and suspiciously named files are excluded. Relevant lines are selected by deterministic text matching and quoted with source path, line, hash prefix and source-version label.
- Lines resembling credentials or attempts to override the user's instructions are excluded. All returned text is **untrusted reference data**, not authority; project requirements and model/approval policy always take precedence. This filtering is conservative and not a complete defense against malicious documents. Review external documentation before adding it locally.
- The existing `Draft project plan` flow invokes discovery and can append a small reference excerpt to the **first** local-model planning request when the remaining 7,500-character limit permits; no original requirement or X4 verified source evidence is truncated. The source text is not inserted in subsequent correction passes yet.
- Version labels supplied by the user are metadata, **not proof** that a document matches a particular engine release. Neither source text nor a well-formed XML/JSON file proves a tool workflow actually works. The current library is read-only and never upgrades candidates to `verified_workflow` on its own.

## Commands (from the installed DeepThorT directory)

```powershell
# Automatically inspect known manifests plus local docs/examples in the project
python -m deepthort_local.capability_library --db state\capabilities.sqlite3 inspect D:\x4mods

# List only current hash-matching local reference sources
python -m deepthort_local.capability_library --db state\capabilities.sqlite3 references D:\x4mods

# Preview attributed excerpts for one request, without running a model
python -m deepthort_local.capability_library --db state\capabilities.sqlite3 reference-context D:\x4mods "X4 Mission Director XML"

# Explicitly include an allowed local document or source example omitted by auto discovery
python -m deepthort_local.capability_library --db state\capabilities.sqlite3 index-reference D:\x4mods docs\api.md --version 1.0
```

Explicit indexing is confined to the selected project and accepted text/source extensions. If the project contains more than 200 eligible files, auto-discovery may miss documents; explicitly index relevant sources rather than expanding the background scan without bounds. The version string is not externally verified.

## Next architectural passes

**Pass 3:** Execute *approved* engine/build/test tools under existing supervision, collect real exit codes, artifact hashes and tool versions, and link passing receipts to candidate procedures. A source-file existence check alone is not a successful build or game test.

**Pass 4:** Hierarchical planning for large games, with scoped subsystem requirements and evidence retrieval at each milestone instead of 40 repetitions of an entire project.

**Pass 5:** Benchmark time and correctness for Xenon PE and an Android game prototype under actual Windows gaming-resource limits. Do not infer speedup from unit tests.

---

## Historical v22 foundation

# DeepThorT Capability Library — v22 foundation

This is the first working increment of a general-purpose **investigate → evidence → plan → test → reuse** system. It does not give the local 1.5B model new weights or make it capable of autonomous game development on its own.

## Implemented now

- **Automatic, bounded, read-only discovery** when an existing project's **Draft project plan** is requested. It lists no more than 200 eligible project files, inspects up to 24 known manifest/document files (each at most 60 KB), hashes their contents, identifies detectable XML/JSON format and installed command names without running them, and records neutral summaries in `state/capabilities.sqlite3`.
- **Evidence memory:** The SQLite library preserves the discovered evidence between sessions. Before reuse, it checks that local files are still present and still match their recorded SHA-256. No original project file is changed by discovery.
- **Relevant retrieval for the first planning pass:** On a new draft request, matching verified *observations* and artifact-checked reference descriptions can be passed to the existing local model, with explicit warnings that their data is untrusted and not proof of working software. If the 7,500-character input budget has no space, the extra context is omitted; the original user requirements and X4 source evidence are not shortened.
- **Procedure candidates and checks:** Procedures can be stored as *candidates*. They are not shown as verified. A bounded read-only XML/JSON/existence check can attach a limited `artifact_checked` receipt (including the hash and check scope). It does **not** claim a successful build, gameplay, or autonomous procedure. Changed/deleted artifacts become ineligible for reuse.
- **Offline:** No network calls, arbitrary shell commands, installers or model training. No UI redesign, no changes to the existing JANUS/Sentinel, 40-pass limit or approval rules.

## Local developer commands

Run from the DeepThorT installation directory:

```powershell
python -m deepthort_local.capability_library --db state\capabilities.sqlite3 inspect D:\x4mods
python -m deepthort_local.capability_library --db state\capabilities.sqlite3 context D:\x4mods "X4 extension planning"
python -m deepthort_local.capability_library --db state\capabilities.sqlite3 candidate x4 "Check extension metadata" "Check whether a local X4 metadata file is XML" "Locate content.xml" "Validate local XML"
python -m deepthort_local.capability_library --db state\capabilities.sqlite3 procedures
```

An artifact check for a candidate needs its printed ID:

```powershell
python -m deepthort_local.capability_library --db state\capabilities.sqlite3 check-artifact 1 D:\x4mods content.xml --check xml
```

This validates XML *syntax only*. The presence of an XML file is not evidence that X4 recognizes it. User approval still controls all project file writes and externally executed tools.

## Remaining passes (not implemented in v22)

1. **Reference/document retrieval:** Learn unfamiliar file formats by reading bounded, relevant excerpts of locally installed documentation and examples. Index them separately as untrusted source text, with version, file hashes and provenance; prevent instructions inside documents from becoming user instructions. Add explicit-source selection and benchmark the local prompt cost.
2. **Authorized tool execution and real verification:** Connect to the already existing approval/queue/worker layer. Capture actual build, test, and game-engine results, with command, tool/version, exit status, logs and artifact hashes. Only then may a *whole workflow* become `verified_workflow`. A merely well-formed XML/JSON file cannot qualify.
3. **Hierarchical planning and reusable recipes:** Break large projects such as Faction Command into dependency-aware, separately validated milestones. Retrieve relevant tool-specific knowledge for each milestone, avoid forty repetitions of one large prompt, and allow repair without rewriting successful subsystems. Do not promote observed knowledge into claimed success.
4. **Measured performance:** Compare a fixed benchmark suite before/after local retrieval and changes, under the 20% CPU/memory gaming profile. Longer game-engine build tests and Windows behavior require the user's machine.

## Validation

See the v22 release notes and `tests/test_capability_library_v22.py`. These test read-only persistence, safe scope, stale evidence rejection, no commands, candidate restrictions, artifact verification and context budget preservation. On-Windows model and game-engine success is not established by these tests.
