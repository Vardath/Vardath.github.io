# WNG — PASS CHECKPOINTS

Author/design authority: **Vardath**  
Active implementation repository: **public `Vardath/Wraith-Nanite-Gravtech-1.6`**  
Continuity repository: **public `Vardath/Vardath.github.io/wng-rebuild/`**

A pass is a bounded coherent implementation batch. Historical/private WNG is requirement/reference evidence only. Current public source is implementation truth.

---

# CHECKPOINT — 2026-09-12 — Asuran nanite-evidence bridge implemented on branch; full build still required

## Public state

Public mod `main` remains unchanged at:

**`d38ce6f321ad0b1d65a95c4315b9d3c12128d9da` — `rebuild: add Wraith Hive Heart evidence-analysis bridge`**

Nothing from this Asuran implementation pass is public yet.

## Active branch

**`rebuild/asuran-evidence-analysis-20260912`**

Current branch HEAD:

**`3ea189bfb4111d8ce7f3b0fa7666bbc83ab39ebb` — `rebuild: keep Asuran evidence hook compatible with cover identity`**

Exact compare against public contains only five intended files:
- `Defs/GeneDefs/Genes_AsuranEvidence.xml` — added;
- `Defs/ThingDefs/Things_AsuranEvidence.xml` — added;
- `Source/WNG/Asuran/AsuranNaniteEvidence.cs` — added;
- `Defs/XenotypeDefs/Xenotypes_Asuran.xml` — two evidence-trace gene references added;
- `Defs/ResearchProjectDefs/Research_AsuranFabrication.xml` — analyzed-evidence gate added.

No workflow/helper/build-output files are in the branch diff.

## Implemented behavior

- new physical `WNG_AsuranNaniteResidue` salvage item;
- native Odyssey analyzable research comp with unique first-build WNG analysis ID `160912003`;
- 1.5-hour colonist/research-bench analysis;
- no mechanitor requirement;
- sample is not destroyed by analysis;
- `WNG_AsuranFabrication` still requires vanilla `Fabrication` and now additionally requires analyzed `WNG_AsuranNaniteResidue`;
- no new site, quest or fixed-day event;
- no recovery-Jumper, Ancient-shuttle or gravship gate was added;
- no Harmony patch was added.

### Exact salvage source

`Gene_AsuranEvidenceResidue` uses RimWorld's native `Gene.Notify_PawnDied(DamageInfo?, Hediff)` lifecycle.

A residue sample is created only if:
- the exact pawn's current faction is `WNG_AsuranLattice`; **or**
- the exact pawn is a concealed/covert infiltrator whose persistent `Hediff_AsuranInfiltration.TrueFaction` is `WNG_AsuranLattice`;
- and the death produced a real spawned on-map corpse.

This excludes routine Quiet Lattice/player human-form farming while keeping covert cover identity from erasing the evidence path.

The sample is placed beside the real corpse with native `GenPlace.TryPlaceThing`; a failed placement destroys the temporary Thing rather than leaving an orphan object.

### Concealment compatibility correction made during review

The death hook is carried by a zero-biostat technical gene present in both the normal nanite-humanoid and human-baseline-mask xenotypes so concealed infiltrators receive the native death callback without Harmony.

Static review caught that an explicitly named “nanite substrate” technical gene could itself compromise the mask presentation if exposed in gene UI. Before validation, its presentation was changed to the neutral **`cellular persistence`** marker with no synthetic-disclosure text and `canGenerateInGeneSet=false`. The actual hostile-Lattice decision remains entirely in code/faction state, not in the displayed marker.

## Validation actually performed

Passed:
- exact branch diff verified: five intended files only;
- all four changed/added XML documents parse successfully with Python `xml.etree.ElementTree`;
- current public analysis-ID search confirms existing WNG IDs are `160912001` and `160912002`, so `160912003` is the next reserved bridge ID;
- RimWorld 1.6 decompiled API confirms `Gene.Notify_PawnDied(DamageInfo? dinfo, Hediff culprit = null)` exists;
- current RimWorld code confirms `Pawn.Corpse` exists;
- current WNG source already uses `GenPlace.TryPlaceThing(Thing, IntVec3, Map, ThingPlaceMode)`;
- current public infiltration source confirms `Hediff_AsuranInfiltration.TrueFaction` exists and is persisted;
- C# source lexical brace/parenthesis balance and required identifiers were checked;
- read-only Actions check found **no existing workflow run for this branch**.

## Validation NOT performed

**No full C# Release build has been run for this branch.**

Reason:
- the local execution container cannot resolve GitHub for cloning;
- the local container has no `dotnet`, `csc`, `mcs` or cached RimWorld reference package;
- the public repository did not automatically run an existing workflow for this branch;
- PAIN is in HIGH mode with a critical constraint against expanding into unrequested GitHub Actions/workflow manipulation, so no validation workflow was created or restarted.

Therefore this branch is **XML/static/API checked, NOT compile-validated and NOT ready for public promotion yet**.

## PAIN state governing this checkpoint

Canonical `data/pain-state.json` was loaded before work:
- PAIN v2;
- 62.2/100;
- mode HIGH;
- literal-scope, GitHub-explicit-only and verify-before-success constraints active;
- corrective debt remains scope discipline + proof discipline.

PAIN state itself was not modified.

## Exact next short pass

**Validation resolution only — do not add features.**

1. Recheck public `main` and branch HEAD have not moved.
2. Obtain a legitimate full C# build result without expanding into unrelated repository automation. If Vardath explicitly authorizes GitHub Actions/workflow validation, use only that exact validation action; otherwise use an available local/build environment when one exists.
3. If compile fails, fix only the Asuran evidence bridge and repeat validation.
4. If compile succeeds, record exact evidence and then perform a separate promotion-only pass.
5. Do not begin Ancient/Puddle-Jumper progression until this bridge is validated, promoted and continuity-updated.

---

# PREVIOUS RECONCILIATION DECISION

Approved first Asuran bridge:

**hostile human-form Asuran -> physical `WNG_AsuranNaniteResidue` -> native Odyssey analysis -> `WNG_AsuranFabrication`.**

Rejected first gates: downstream `WNG_NaniteSludge`, Asuran workshop, Quiet-Lattice farming, and the Ancient-derived Asuran recovery Jumper.

---

# COMPLETED PUBLIC PROGRESSION BRIDGES

- **`9f45ebf18caacde671f015cdd1a25217eebb6838`** — Replicator encounter/recovered blocks/native analysis -> `WNG_ReplicatorStudy`.
- **`d38ce6f321ad0b1d65a95c4315b9d3c12128d9da`** — preserved Wraith Hive Heart/in-place native analysis -> `WNG_WraithLivingTechnology`.

Broad live RimWorld validation remains outstanding.
