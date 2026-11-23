# Scratch Chat milestone — 2026-11-23 pilot validation ordering

Verified prior source-test baseline: GitHub Actions run 45160508915, unit-tests success. This does not establish success for the commits below.

Inspected the current original-weight dialogue pilot. It parsed the source manifest and verified split files before checking whether the output directory already contained a checkpoint or whether model capacity controls were invalid. Consequently an absent split could mask the intended overwrite/capacity error and force unnecessary dataset reads. Fixed ordering: parse manifest, reject nonempty output, validate capacity and training controls, verify source/splits, then perform mandatory lexical contamination screening before writing output. Added regression tests asserting the split verifier is not invoked for overwrite or invalid-capacity requests.

Commits: d2e5c25535aaaf64f44a87c7a000cde2b820e8a6 and 392116646e50fb8f3b03e138dadb1a45640e161c. Follow-on source CI result is unverified at milestone creation.

This is defensive pipeline repair, not model training. No new external corpus was admitted or checkpoint trained. Existing independent Scratch Chat weights must not be replaced by pretrained weights. Outstanding: approved revision-pinned and privacy-reviewed dialogue source; independently grouped/decontaminated train/validation/test; bounded original-weight pilot; adequate GPU training; multi-turn and tool-use acceptance; real DeepThorT JSON-line integration. GitHub Actions CPU is suitable for bounded pilot tests only.
