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

# CHECKPOINT — 2026-09-11 — human-form conceal/reveal foundation validated on branch

## Public implementation state

Public mod `main` remains:

**`8495b846c7dd31c079db6d4f007be490df3247f3` — Neural Interface and exact human-form reconstruction.**

The infiltration work below is branch-only at this checkpoint.

## Active branch

Branch:

**`rebuild/humanform-infiltration-20260911`**

Clean branch HEAD after removing the temporary validator:

**`09e6c7eb741d3bf2629d067f99dae8554f45ed69` — `cleanup: remove infiltration validator`**

The validated source/Def tree was tested at `6a9a0479ee0de1150eb892b4500af8d3f2dc1c81`; `09e6c...` differs only by removal of the temporary validation workflow.

## What this pass implemented

New source:
- `Source/WNG/Asuran/AsuranInfiltration.cs`

New Def:
- `Defs/GeneDefs/Genes_AsuranInfiltration.xml`

Updated:
- `Source/WNG/Asuran/AsuranNaniteFabrication.cs`;
- `Source/WNG/Asuran/AsuranNeuralInterface.cs`;
- `Defs/XenotypeDefs/Xenotypes_Asuran.xml`;
- `Defs/PawnKindDefs/PawnKinds_Asuran.xml`;
- `Defs/HediffDefs/Hediffs_AsuranNanite.xml`;
- `Defs/FactionDefs/Factions_Asuran.xml`.

Implemented behavior:
- new real `WNG_AsuranInfiltrator` PawnKind exists as an Asuran role;
- concealed infiltrator generation uses `WNG_AsuranHumanBaselineMask` rather than publicly exposing `WNG_NaniteHumanoid` at generation;
- the mask presents a Baseliner-style xenotype label/icon and ordinary visible Food need while concealed;
- hidden infiltrator physiology still uses the same native `Need_Food` quantity as its finite internal matter reserve, but does not expose the Nanite Reserve label until reveal;
- exact conceal/reveal state is a real `Hediff_AsuranInfiltration` attached to the exact pawn and serialized through save/load;
- concealed infiltration state, nanite lattice, nanite depletion and EMP-disruption health readouts are hidden while cover remains intact;
- reveal is currently permanent and changes state on the same pawn; there is no pawn recreation/proxy/replacement;
- permanent reveal removes only the masking physiology gene, layers the real current `WNG_NaniteHumanoid` genes, changes xenotype metadata to the real WNG nanite humanoid, reconciles needs, and dirties graphics;
- reveal therefore materially changes visible game state from ordinary Food/Baseliner-style cover to public WNG synthetic xenotype/Nanite Reserve/nanite health-state semantics;
- Queen uniqueness and block sovereignty are not granted or inferred by infiltrator state;
- direct Neural Interface contact is a concrete scan path: a concealed infiltrator is accepted as an apparently biological target, but the touch scan exposes the synthetic lattice instead of opening ordinary recruit/copy operations;
- EMP permanently reveals a concealed infiltrator and transfers EMP suppression onto the replacement public nanite-lattice state;
- non-EMP damage of Def-tunable meaningful size (first-build threshold 8 damage) permanently reveals synthetic structure;
- automatic nanite self-repair accumulates Def-tunable suspicion and reveals the pawn after first-build cumulative 1 hit point of visibly unnatural repair;
- current ordinary Asuran combat pool includes a low-weight infiltrator role so the exact concealed/reveal mechanics can occur in normal current faction generation while broader covert arrival/cover-faction delivery remains a separate unfinished pass;
- current physiology class was made inheritable so the mask gene can reuse the real nanite physiology implementation instead of duplicating a second synthetic body system.

## Validation

GitHub Actions run:

**`34600994766` — SUCCESS**

Validated:
- `dotnet build Source/WNG/WNG.csproj -c Release` — passed;
- all current Def/Patch XML parsed successfully;
- save-persistent reveal state present;
- masked public identity -> real WNG xenotype conversion present;
- concealed Food-cover reserve path present;
- hidden synthetic health-readout paths present;
- direct Neural Interface scan reveal present;
- EMP/meaningful-damage reveal present;
- cumulative self-repair suspicion reveal present;
- infiltrator PawnKind/mask xenotype/faction pool wiring present.

Temporary validator removed at branch HEAD `09e6c...`.

This is **source/Def validation, not live RimWorld validation**.

## Important scope boundary

This pass establishes **real conceal/reveal mechanics**, but it does **not yet complete strategic impersonation/delivery**.

Still required in the infiltration subsystem:
- a credible covert arrival/presence path where an infiltrator is not immediately given away simply by arriving as part of an openly hostile Asuran assault;
- cover/guest/visitor behavior that uses native RimWorld relations where possible without replacing the exact pawn or inventing proxy identity;
- persistent transition from cover behavior to hostile Asuran behavior when revealed/activated, while preserving exact pawn identity and the true Asuran source relationship;
- live validation of Bio/Genes/Needs/Health presentation before and after reveal;
- live validation of damage, EMP, Neural Interface scan and repair-triggered reveal/save-load.

Because those are still open, `Human-form infiltration/impersonation/reveal` must **not** yet be removed from the required debt list. The implemented foundation should be recorded separately after promotion.

## Exact next pass

**Promotion + covert-presence design/implementation pass:**

1. Recheck public `main` remains `8495b...`.
2. Promote the clean validated conceal/reveal foundation as one clean public commit without the temporary validator history.
3. Update `CURRENT_PUBLIC_STATE.md` with the new public SHA, recording conceal/reveal as implemented foundation while retaining covert impersonation/presence as required debt.
4. Create a fresh branch from the new public HEAD.
5. Inspect current native visitor/guest/faction/incident APIs before choosing cover semantics; do not fake neutrality by silently deleting/recreating the pawn.
6. Implement one genuine covert-presence path that allows the exact infiltrator pawn to exist around the colony without ordinary hostile-assault presentation immediately disclosing the role.
7. Define exact reveal/activation handling that preserves the pawn and links back to the true Asuran source relationship.
8. Validate and checkpoint before moving to Quiet Lattice.

---

# PRIOR CHECKPOINT — Neural Interface promoted to public

Public milestone:

**`8495b846c7dd31c079db6d4f007be490df3247f3` — `rebuild: add Neural Interface and exact human-form reconstruction`**

Validation:
- initial run **34597748048** exposed obsolete historical `Gene.Xenogene` API use;
- corrected to current `Pawn_GeneTracker.Xenogenes` semantics;
- final run **34599563874 — SUCCESS**;
- Release build **0 warnings / 0 errors**;
- all then-current **102** Def/Patch XML files parsed.

---

# PRIOR PUBLIC MILESTONES

- Temporary Asuran lattice intrusion: **`26680fe84b95a0bfd5a23841b714fdba9cde1a98`**.
- Recurring exact-map Queen recovery: **`9ce713704505a220d357f8a6f234fb6e040e0b2e`**.
- Captured Queen sovereign consequences: **`0b8150f3ff6ca7138482ba9a604847f5967fc48b`**.
- Neural Interface / exact human-form reconstruction: **`8495b846c7dd31c079db6d4f007be490df3247f3`**.

All completed public slices were source/Def validated before promotion; broad live RimWorld validation remains outstanding.
