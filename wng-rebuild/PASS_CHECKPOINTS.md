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

# CHECKPOINT — 2026-09-11 — Neural Interface promoted to public

Public mod `main` is now:

**`8495b846c7dd31c079db6d4f007be490df3247f3` — `rebuild: add Neural Interface and exact human-form reconstruction`**

Promotion used the already validated clean branch tree `64e1020a0d3bbe1ec06aac64db52428bbb52dedf` with parent `0b8150...`, producing one clean public commit. Temporary validation workflow history did not enter public `main`.

Public diff from `0b8150...` contains only intended Neural Interface files:
- `Defs/AbilityDefs/Abilities_NeuralInterface.xml` — added;
- `Defs/GeneDefs/Genes_AsuranFabrication.xml` — Neural Interface ability grant added;
- `Defs/PawnKindDefs/PawnKinds_HumanFormReplicator.xml` — added;
- `Source/WNG/Asuran/AsuranNeuralInterface.cs` — added.

Validation inherited by the promoted tree:
- initial run **34597748048** exposed obsolete historical `Gene.Xenogene` API use;
- implementation corrected to current `Pawn_GeneTracker.Xenogenes` semantics;
- final run **34599563874 — SUCCESS**;
- Release build: **0 warnings / 0 errors**;
- all **102** current Def/Patch XML files parsed;
- native recruit/prisoner/slave operations, exact core identity snapshot, current gene-type preservation and transactional Nanite Reserve rollback invariants passed.

`CURRENT_PUBLIC_STATE.md` has been updated to exact public HEAD `8495b...`, Neural Interface/core exact copy-reconstruction is removed from required implementation debt, and live-test/optional broader DLC-copy-fidelity work remains explicitly open.

## Exact next pass

Create a fresh branch from `8495b...` for the **human-form infiltration / impersonation / reveal foundation**.

Required first-pass boundary:
- exact pawn remains the same pawn throughout conceal/reveal;
- hidden/revealed state is persistent and save/load safe;
- concealment must materially affect what the player is told/shown, not only flavor text;
- reveal is permanent unless Vardath later specifies a re-conceal mechanic;
- implement real current-mechanic reveal triggers for scanning, meaningful injury/damage exposure and suspicious synthetic behavior where current APIs allow them;
- Queen uniqueness/block sovereignty remain separate;
- validate source/Defs and checkpoint before moving to Quiet Lattice or another subsystem.

---

# PRIOR CHECKPOINT — Neural Interface / exact human-form reconstruction validated on branch

Public `main` at that checkpoint was `0b8150...`.

Clean branch HEAD:

**`7220a394173d850863156123b8bf27016b7290a5`**

Validated source/Def tree: `e3defb46c82441e31e8e7bea1f788e9174f30889`.

Implemented:
- touch-range player nanite-human Neural Interface;
- native faction recruitment;
- native prisoner status;
- Ideology-gated native slave status;
- skill/passion/XP copying;
- real separate reconstructed human-form pawn;
- Def-tunable 60% first-build Nanite Reserve copy cost;
- transactional placement/cost rollback;
- source name, gender, age, backstories, title/surname, appearance, traits, skills/passions/XP and genome snapshot;
- current RimWorld xenogene/endogene distinction;
- WNG nanite identity layering after source-person snapshot.

Final validation run: **34599563874 — SUCCESS**.

---

# PRIOR PUBLIC MILESTONES

- Temporary Asuran lattice intrusion: **`26680fe84b95a0bfd5a23841b714fdba9cde1a98`**.
- Recurring exact-map Queen recovery: **`9ce713704505a220d357f8a6f234fb6e040e0b2e`**.
- Captured Queen sovereign consequences: **`0b8150f3ff6ca7138482ba9a604847f5967fc48b`**.
- Neural Interface / exact human-form reconstruction: **`8495b846c7dd31c079db6d4f007be490df3247f3`**.

All completed public slices were source/Def validated before promotion; broad live RimWorld validation remains outstanding.
