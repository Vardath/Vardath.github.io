# WNG — PASS CHECKPOINTS

Author/design authority: **Vardath**  
Active implementation repository: **public `Vardath/Wraith-Nanite-Gravtech-1.6`**  
Continuity repository: **public `Vardath/Vardath.github.io/wng-rebuild/`**

A pass is a bounded coherent implementation batch. Historical/private WNG is requirement/reference evidence only. Current public source is implementation truth.

---

# CHECKPOINT — 2026-09-12 — Asuran evidence validation boundary reached; branch not promoted

## Public state reverified

Public mod `main` is still exactly:

**`d38ce6f321ad0b1d65a95c4315b9d3c12128d9da` — `rebuild: add Wraith Hive Heart evidence-analysis bridge`**

No Asuran evidence code is public yet.

## Staged implementation branch

Branch: **`rebuild/asuran-evidence-analysis-20260912`**  
HEAD: **`3ea189bfb4111d8ce7f3b0fa7666bbc83ab39ebb`**

Exact branch diff remains five intended files only:
- `Defs/GeneDefs/Genes_AsuranEvidence.xml`;
- `Defs/ThingDefs/Things_AsuranEvidence.xml`;
- `Source/WNG/Asuran/AsuranNaniteEvidence.cs`;
- `Defs/XenotypeDefs/Xenotypes_Asuran.xml`;
- `Defs/ResearchProjectDefs/Research_AsuranFabrication.xml`.

No workflows, helpers, build outputs or unrelated subsystem files are in the diff.

## Checks completed successfully

- all changed XML documents parse;
- `analysisID=160912003` is unique relative to current public WNG IDs `160912001` and `160912002`;
- exact RimWorld 1.6 native `Gene.Notify_PawnDied(DamageInfo?, Hediff)` API verified;
- `Pawn.Corpse` native API verified;
- native `GenPlace.TryPlaceThing` call shape already used in current WNG source;
- `Hediff_AsuranInfiltration.TrueFaction` verified in current public source;
- hostile-source logic is restricted to current or persisted true faction `WNG_AsuranLattice`;
- Quiet Lattice/player synthetic deaths do not satisfy the source predicate;
- covert mask compatibility was reviewed and the technical gene's public presentation was neutralized to `cellular persistence` rather than revealing nanite identity;
- no Harmony, quest, site, Jumper, Ancient-shuttle or gravship coupling was introduced;
- read-only Actions query found zero existing workflow runs for the branch.

## Full-build validation blocker

A full C# Release compile cannot currently be produced in the available local execution environment:
- no `dotnet`;
- no `csc`;
- no `mcs`/Mono compiler;
- no local cached RimWorld reference package;
- container DNS cannot clone GitHub;
- public WNG repo currently has no `.github/workflows` directory and therefore no existing build workflow to observe/use.

Under loaded PAIN v2 HIGH mode, creating or manipulating a GitHub Actions workflow without an explicit instruction for that exact GitHub action would repeat a recorded scope failure. Therefore **no workflow was created, dispatched or restarted**.

## Consequence

The branch is **static/API/XML checked but not compile-validated**. It is deliberately **not promoted**. No claim of build success is made.

## Exact next action required before promotion

Obtain an explicit legitimate C# build result for branch `3ea189b...` without adding features. The narrowest available route is either:
- Vardath explicitly authorizes a temporary GitHub Actions validation workflow for this branch; or
- a local/runtime environment with .NET/RimWorld references becomes available.

After a successful build, the next pass is promotion-only: recheck public `main`, promote the clean five-file tree, verify the exact public diff, and update continuity. If compile fails, fix only this Asuran evidence bridge and revalidate.

Do **not** begin Ancient/Puddle-Jumper progression while this branch is unresolved.

---

# ASURAN EVIDENCE BRIDGE DECISION

Approved progression chain:

**hostile human-form Asuran encounter -> `WNG_AsuranNaniteResidue` -> native Odyssey analysis -> `WNG_AsuranFabrication`**

Rejected first gates remain: downstream nanite sludge/workshop, Quiet-Lattice farming, and Ancient-derived recovery Jumper hardware.

---

# COMPLETED PUBLIC PROGRESSION BRIDGES

- **`9f45ebf18caacde671f015cdd1a25217eebb6838`** — Replicator evidence -> `WNG_ReplicatorStudy`.
- **`d38ce6f321ad0b1d65a95c4315b9d3c12128d9da`** — Wraith Hive Heart evidence -> `WNG_WraithLivingTechnology`.

Broad live RimWorld validation remains outstanding.
