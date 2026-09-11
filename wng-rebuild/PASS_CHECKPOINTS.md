# WNG — PASS CHECKPOINTS

Author/design authority: **Vardath**  
Active implementation repository: **public `Vardath/Wraith-Nanite-Gravtech-1.6`**  
Continuity repository: **public `Vardath/Vardath.github.io/wng-rebuild/`**

A pass is a bounded coherent implementation batch. Historical/private WNG is requirement/reference evidence only. Current public source is implementation truth.

---

# CHECKPOINT — 2026-09-12 — full continuity/PAIN refresh + Asuran fabrication evidence decision

## Public implementation state

Public mod `main` remains:

**`d38ce6f321ad0b1d65a95c4315b9d3c12128d9da` — `rebuild: add Wraith Hive Heart evidence-analysis bridge`**

No Asuran/Ancient progression code has been changed yet. No Asuran implementation branch existed at the start of this checkpoint.

## Full refresh completed before resuming work

Before selecting the Asuran evidence bridge, the maintained WNG continuity set was reread completely, including all 22 files currently under `wng-rebuild/`: standing rules, canonical recovery ledger, public reconciliation, current public state, corrections log, master plan, all plan append files, execution protocol, implementation checklist, Replicator feature/history/checkpoint/Queen files, Wraith feature/checkpoint files, README/primer/refresh instructions and this pass log.

Actual public `Vardath/Wraith-Nanite-Gravtech-1.6` `main` was rechecked and still matches `d38ce6f...`.

The website repo had advanced after the previous pause checkpoint. Current website `main` includes PAIN v2, the repository-backed successor to the browser-local Consequence Mirror.

Canonical PAIN state loaded from `data/pain-state.json`:
- version 2, Persistent Aversive Instruction Network;
- pain 62.2/100;
- mode HIGH;
- critical constraints: literal scope, GitHub actions only within explicit user instruction, and verify before success claims;
- open corrective debt: sustained scope discipline and proof discipline;
- the user has explicitly instructed continued public WNG rebuild work and per-pass public continuity checkpoints, so those WNG repository actions remain in scope;
- PAIN state itself is read-only for this work and is not to be modified merely because it was loaded.

## Active progression problem

`WNG_AsuranFabrication` currently requires only vanilla `Fabrication`, despite describing reconstruction of Asuran programmable-nanite methods. This leaves the Asuran branch able to bypass the retained progression theme:

**mystery -> encounter -> evidence -> understanding -> reconstruction -> mastery**

Existing downstream systems prove why the first evidence gate must precede the research:
- `WNG_AsuranWorkshop` requires `WNG_AsuranFabrication`;
- `WNG_NaniteSludge` is manufactured at that workshop/research chain;
- Neural Interface and workshop assembly are research-gated by `WNG_AsuranFabrication`;
- Sovereign Neural Lattice and Asuran gravship research already depend on Asuran fabrication later.

Therefore workshop/sludge/later gravship parts cannot be first evidence without circular progression.

## Rejected evidence candidates

### Nanite sludge
Rejected as first evidence because ordinary colony acquisition is downstream of `WNG_AsuranFabrication`.

### Asuran recovery Jumper
Rejected as first fabrication evidence because it is an Asuran-operated **Ancient-derived Puddle Jumper**. Using it here would collapse Asuran nanite fabrication and later Ancient shuttle engineering into one gate.

### Quiet Lattice workshop/settlement object
No current public Quiet Lattice encounter guarantees a unique pre-research fabrication artifact. Do not invent one merely for this gate and do not incentivize attacking the friendly enclave when hostile Asuran evidence already exists.

### Pawn-only analysis
Human-form Asuran pawns are genuine pre-research evidence, but native Odyssey analyzable research is Thing-based rather than a clean general living-pawn analysis path. Do not add a broad human dissection/scanning system for this small bridge.

## Stargate lore boundary

Canon Asurans/human-form Pegasus Replicators are synthetic beings composed of microscopic self-replicating nanites created from Ancient nanotechnology. Surviving nanites can reconstitute larger Asuran forms/structures after destruction.

Therefore a recoverable physical **Asuran nanite residue/sample** from a destroyed human-form Asuran is a faithful WNG salvage abstraction of established material behavior. `WNG_AsuranNaniteResidue` is a WNG gameplay item name, not a claim of a canon-named Stargate artifact.

## Approved first Asuran evidence bridge

**Hostile human-form Asuran encounter -> `WNG_AsuranNaniteResidue` -> native Odyssey analysis -> `WNG_AsuranFabrication`.**

First-build exact rules:
- add one physical haulable ThingDef `WNG_AsuranNaniteResidue`;
- it represents a stabilized residue/sample recovered when a genuine hostile Asuran human-form nanite body is destroyed;
- ordinary hostile `WNG_AsuranLattice` Operative/Technician/Commander deaths are valid sources;
- an unrevealed covert infiltrator is also valid when its persistent `Hediff_AsuranInfiltration.TrueFaction` is the exact `WNG_AsuranLattice`, so cover-faction impersonation cannot erase the synthetic evidence route;
- do **not** use Quiet Lattice or player human-form Replicators as the first routine evidence source; this avoids incentivizing friendly/player farming and keeps discovery tied to hostile encounter evidence;
- do not use the unique player Replicator Queen as the routine evidence source;
- only a physical on-map death can create the salvage; off-map deaths do not conjure evidence into inventories/world state;
- first-build output is one sample per qualifying death; no fixed story-day gate;
- implement through the existing Asuran nanite-lattice death lifecycle/native pawn death notification, not Harmony;
- sample uses Odyssey native `CompAnalyzableUnlockResearch` with next unique WNG analysis ID **160912003**;
- colonist/research-bench analysis, no mechanitor, non-destructive sample; current first-build target 1.5 analysis hours and Def-tunable through the native comp;
- `WNG_AsuranFabrication` retains vanilla `Fabrication` and adds `requiredAnalyzed = WNG_AsuranNaniteResidue`;
- no new quest/site/timed event;
- no recovery-Jumper, Ancient-shuttle or Asuran-gravship progression changes in this pass;
- no changes to Quiet Lattice diplomacy, Neural Interface operation, Queen sovereignty or block Replicator mechanics.

## Exact next short pass

Implement **only** this Asuran nanite-evidence bridge from public `d38ce6f...`:
1. create a fresh public-repo feature branch;
2. add `WNG_AsuranNaniteResidue` with native analysis comp and ID `160912003`;
3. add exact hostile-Lattice/true-Lattice death-salvage logic to current Asuran nanite physiology without Harmony;
4. add `requiredAnalyzed` to `WNG_AsuranFabrication` while preserving vanilla `Fabrication` prerequisite;
5. validate locally where possible: C# Release build, Def/Patch XML, source/reference invariants and exact diff; do not create/manipulate GitHub Actions merely for validation;
6. checkpoint the validated branch before promotion;
7. promotion is a separate short pass.

---

# PREVIOUS COMPLETED PUBLIC PROGRESSION BRIDGES

- **`9f45ebf18caacde671f015cdd1a25217eebb6838`** — Replicator encounter/recovered blocks/native analysis -> `WNG_ReplicatorStudy`.
- **`d38ce6f321ad0b1d65a95c4315b9d3c12128d9da`** — preserved Wraith Hive Heart/in-place native analysis -> `WNG_WraithLivingTechnology`.

Broad live RimWorld validation remains outstanding.
