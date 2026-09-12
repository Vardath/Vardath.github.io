# WNG — PASS CHECKPOINTS

Author/design authority: **Vardath**  
Active implementation repository: **public `Vardath/Wraith-Nanite-Gravtech-1.6`**  
Continuity repository: **public `Vardath/Vardath.github.io/wng-rebuild/`**

A pass is a bounded coherent implementation batch. Historical/private WNG is requirement/reference evidence only. Current public source is implementation truth.

---

# CHECKPOINT — 2026-09-12 — Asuran evidence hostile-source edge fixed; compile gate still unresolved

## Public state reverified

Public mod `main` remains exactly:

**`d38ce6f321ad0b1d65a95c4315b9d3c12128d9da` — `rebuild: add Wraith Hive Heart evidence-analysis bridge`**

No Asuran evidence code has been promoted to public `main`.

## Staged implementation branch

Branch: **`rebuild/asuran-evidence-analysis-20260912`**  
HEAD: **`9a131debc6d849ba69be446ef13cb2876ad67add` — `fix: restrict Asuran residue to active hostile sources`**

Comparison against public `d38ce6f...` remains exactly five intended files only:
- `Defs/GeneDefs/Genes_AsuranEvidence.xml`;
- `Defs/ThingDefs/Things_AsuranEvidence.xml`;
- `Source/WNG/Asuran/AsuranNaniteEvidence.cs`;
- `Defs/XenotypeDefs/Xenotypes_Asuran.xml`;
- `Defs/ResearchProjectDefs/Research_AsuranFabrication.xml`.

No workflow, helper, build output, Ancient/Puddle-Jumper, gravship or unrelated subsystem file entered the branch diff.

## Defect found and corrected in this pass

The previous hostile-source predicate accepted any pawn whose saved infiltration `TrueFaction` remained `WNG_AsuranLattice`. That could allow a former covert infiltrator whose current faction later became player-aligned to remain a residue source purely because historical true-faction metadata persisted, contradicting the intended no-player-farming boundary.

The predicate now permits residue only when either:
- the pawn's **current faction** is `WNG_AsuranLattice`; or
- the pawn is an **unrevealed active covert presence** whose persisted `TrueFaction` is `WNG_AsuranLattice`.

Consequences:
- ordinary hostile public Asurans still qualify;
- directly hostile masked Infiltrator combat pawns still qualify through current hostile faction;
- a still-concealed covert visitor qualifies through active covert state + exact persisted true faction;
- once a covert pawn is revealed, its actual current faction becomes authoritative;
- a player-aligned/recruited/enslaved former infiltrator cannot remain a residue-farming source merely because old true-faction metadata survives.

## Additional runtime/API validation completed

Read-only verification against current WNG source and RimWorld 1.6 decompiled source established:

- `WNG_AsuranInfiltrator` explicitly uses `WNG_AsuranHumanBaselineMask`, so the staged `WNG_AsuranEvidenceTrace` added to that mask is genuinely present on covert visitors;
- normal Asuran PawnKinds use `WNG_NaniteHumanoid`, which also contains the marker on the staged branch;
- RimWorld 1.6 `Pawn.Kill` creates/places the corpse **before** `genes.Notify_PawnDied(...)`, so `pawn.Corpse` is available for a normal spawned-map death when the evidence gene runs;
- RimWorld 1.6 `Pawn_GeneTracker.Notify_PawnDied` iterates `GenesListForReading` and calls every gene's death notification, so the marker is not dependent on gene active-state filtering;
- current WNG covert-visitor scheduling is independent of `WNG_AsuranFabrication`, so a hostile/covert human-form Asuran can exist before the research it gates; the evidence chain is not circular;
- current masked infiltration already uses deliberately innocuous gene presentation (`metabolic equilibrium`); the new technical marker remains neutral (`cellular persistence`) rather than naming Asuran/nanite identity;
- research coordinate `(19, 15.5)` remains the existing `WNG_AsuranFabrication` location and introduces no duplicate WNG research-node position;
- `WNG_AsuranNaniteResidue` does not exist on current public `main`, so the branch is not colliding with an already-public duplicate resource/Def.

The changed XML documents themselves are unchanged from the earlier statically parsed candidate. Existing checks remain applicable:
- XML syntax was clean;
- `analysisID=160912003` was unique relative to public WNG `160912001` and `160912002`;
- native analyzable/research-gate structure matches the two already-public WNG evidence bridges.

## Full-build validation blocker remains

A legitimate full C# Release compile still cannot currently be produced in the available local execution environment:
- no `dotnet`;
- no `csc`, `mcs`, `mono-csc`, Mono runtime, MSBuild/xbuild, Roslyn or NuGet executable;
- no cached compiler/runtime packages;
- direct runtime/SDK download attempts are blocked by the container's external DNS/network path;
- the project itself targets `net48`, C# 8.0 and references `Krafs.Rimworld.Ref 1.6.4871`, so a normal .NET/NuGet-capable runtime would be sufficient if available;
- public WNG still has no existing workflow that can simply be observed/reused for this branch.

Under loaded PAIN HIGH mode, no GitHub Actions workflow was created, restored, dispatched or restarted without an explicit instruction for that exact action.

## Consequence

Branch `9a131de...` is more strongly runtime/API/static checked and one real source-predicate defect has been fixed, but it is still **not compile-validated** and therefore remains deliberately **unpromoted**. No build-success claim is made.

## Exact next action before promotion

Obtain a legitimate C# Release build result for **`9a131debc6d849ba69be446ef13cb2876ad67add`** without adding unrelated features.

After a successful compile:
1. recheck public `main`;
2. promote only the clean five-file Asuran evidence tree;
3. verify exact public diff;
4. update `CURRENT_PUBLIC_STATE.md` and this checkpoint;
5. only then move to the next Ancient/evidence progression slice.

If compile fails, repair only the Asuran evidence bridge, revalidate, and keep the branch unpromoted until it passes.

**Do not begin Ancient/Puddle-Jumper progression while this branch remains unresolved.**

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
