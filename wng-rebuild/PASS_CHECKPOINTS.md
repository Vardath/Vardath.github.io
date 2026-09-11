# WNG — PASS CHECKPOINTS

Author/design authority: **Vardath**  
Active implementation repository: **public `Vardath/Wraith-Nanite-Gravtech-1.6`**  
Continuity repository: **public `Vardath/Vardath.github.io/wng-rebuild/`**

# PURPOSE

This is the mandatory short-pass checkpoint log for the WNG rebuild.

A **pass** is a bounded, coherent implementation batch — not one line or one tiny edit, and not a multi-hour uncheckpointed session. Each pass should complete a meaningful slice that can be reasoned about and validated before moving on.

**After every meaningful pass, before beginning the next one, update this file with:**
- exact public `main` SHA at the checkpoint;
- active branch name and exact branch SHA if work is not yet promoted;
- what was actually implemented/changed during the pass;
- what was validated, and whether validation was static or live-game;
- what remains unfinished in that feature slice;
- exact next steps for the next pass;
- any defect or dependency discovered during the pass;
- whether continuity files such as `CURRENT_PUBLIC_STATE.md` also need updating.

Never write a checkpoint as though branch-only work is already public. Never treat private/reference work as current implementation.

---

# CHECKPOINT — 2026-09-11 — Neural Interface / exact human-form reconstruction validated on branch

## Public implementation state

Public mod `main` remains:

**`0b8150f3ff6ca7138482ba9a604847f5967fc48b` — captured Queen sovereign consequences.**

The Neural Interface work in this checkpoint is branch-only until promotion.

## Active branch

Branch:

**`rebuild/neural-interface-foundation-20260911`**

Clean branch HEAD after removing the temporary validator:

**`7220a394173d850863156123b8bf27016b7290a5` — `cleanup: remove Neural Interface validator`**

Validated source/Def tree was tested at `e3defb46c82441e31e8e7bea1f788e9174f30889`; `7220a...` differs only by removal of the temporary validation workflow.

## What this pass implemented

New source:
- `Source/WNG/Asuran/AsuranNeuralInterface.cs`

New Defs:
- `Defs/AbilityDefs/Abilities_NeuralInterface.xml`
- `Defs/PawnKindDefs/PawnKinds_HumanFormReplicator.xml`

Updated:
- `Defs/GeneDefs/Genes_AsuranFabrication.xml`

Implemented behavior:
- real touch-range `WNG_NeuralInterface` ability granted by the existing `WNG_AsuranNanitePhysiology` gene;
- use restricted to player-controlled living nanite humanoids after `WNG_AsuranFabrication` research;
- valid subjects are other living spawned biological humanlikes on the same map; existing nanite humanoids and block Replicators are excluded;
- operation state is revalidated at execution/touch range so a changed/vanished subject cancels safely;
- native faction recruitment uses `Pawn.SetFaction(caster.Faction, caster)` rather than a fake allegiance flag;
- native prisoner state uses `Pawn_GuestTracker.SetGuestStatus(..., GuestStatus.Prisoner)` and requires a downed/prisoner/slave-compatible target state;
- Ideology-gated slavery uses native `GuestStatus.Slave` and is unavailable without Ideology;
- direct skill-pattern extraction copies skill levels upward into the operator, passions and XP state using native `SkillRecord` fields;
- real `WNG_HumanFormReplicatorCopy` PawnKind added for reconstructed synthetic persons;
- reconstruction leaves the exact biological source pawn intact and creates a genuinely separate pawn;
- current reconstruction cost is Def-tunable and first-build value is 60% of the operator's existing Nanite Reserve;
- reserve is checked before generation but spent only after a viable copy has been created and physically placed;
- if placement fails, reserve is not spent;
- if reserve commit fails after placement, the generated copy is destroyed/rolled back instead of granting a free duplicate;
- exact person snapshot preserves source name, gender, biological/chronological age, childhood/adulthood backstories, explicit title and birth surname, body/head/hair/skin presentation, traits, skill levels, passions and XP;
- source genes are copied using the current RimWorld gene tracker distinction between `Xenogenes` and endogenes; the obsolete private-build `Gene.Xenogene` assumption was removed;
- WNG nanite identity genes are layered after the source identity/genome pass while the final PawnKind remains the current WNG nanite humanoid synthetic identity;
- source pawn is never deleted/recreated as part of copy semantics.

## Validation / defect fixed

Initial validation run:

**`34597748048` — FAILED**

Failure was one compile-time API mismatch inherited from historical reference assumptions:
- `Gene.Xenogene` does not exist in the current referenced RimWorld API.

The implementation was corrected against current native `Pawn_GeneTracker` API by determining source gene type through:
- `source.genes.Xenogenes.Contains(sourceGene)`

Final validation run:

**`34599563874` — SUCCESS**

Validated:
- `dotnet build Source/WNG/WNG.csproj -c Release` — passed with **0 warnings / 0 errors**;
- all **102** current Def/Patch XML files parsed successfully;
- native recruitment/prisoner/slave calls present;
- exact age/backstory/skill/passion/gene snapshot invariants present;
- source xenogene/endogene distinction present using current API;
- transactional Nanite Reserve commit/rollback present;
- Neural Interface ability/gene/PawnKind wiring present.

This is source/Def validation, **not live RimWorld validation**.

## Remaining human-form slice

Still required after this foundation:
- live-game validation of Neural Interface targeting, cooldown/operation UI, recruit/prisoner/slavery transitions and copy spawning/save-load;
- infiltration/impersonation/reveal as a real mechanic;
- Quiet Lattice non-hostile enclave;
- player human-form variants and broader role/faction composition;
- native WNG backstories;
- further copy fidelity audit for optional DLC identity trackers/presentation not explicitly included in the current exact core snapshot;
- final UI/art/audio polish.

## Exact next pass

**Promotion + continuity pass**, then begin real human-form infiltration/reveal foundation:

1. Recheck public `main` is still `0b8150...`.
2. Promote the clean validated Neural Interface tree as a clean public commit without temporary validator history.
3. Verify intended public diff only.
4. Update `CURRENT_PUBLIC_STATE.md` to the new public SHA and remove Neural Interface/exact copy-reconstruction from required debt while retaining live-test and optional-fidelity debt.
5. Update this checkpoint with the promoted SHA.
6. Create a fresh branch from the new public HEAD for infiltration/reveal.
7. Implement a real persistent hidden/revealed synthetic identity state, with concrete reveal paths from scanning/injury/suspicious behavior rather than flavor text.
8. Checkpoint before the next subsystem.

---

# PRIOR CHECKPOINT — captured Queen consequences promoted to public

Public milestone:

**`0b8150f3ff6ca7138482ba9a604847f5967fc48b` — `rebuild: add captured Queen sovereign consequences`**

Promotion used the validated clean branch tree and did not copy temporary validation/helper commits into public history.

Captured-Queen validation runs:
- remote sovereignty: **34596238345 — SUCCESS**;
- mixed sovereign threat: **34596657164 — SUCCESS**.

---

# EARLIER PUBLIC MILESTONES

- Temporary Asuran lattice intrusion: **`26680fe84b95a0bfd5a23841b714fdba9cde1a98`**.
- Recurring exact-map Queen recovery: **`9ce713704505a220d357f8a6f234fb6e040e0b2e`**.
- Captured Queen sovereign consequences: **`0b8150f3ff6ca7138482ba9a604847f5967fc48b`**.

All completed public slices were source/Def validated before promotion; broad live RimWorld validation remains outstanding.
