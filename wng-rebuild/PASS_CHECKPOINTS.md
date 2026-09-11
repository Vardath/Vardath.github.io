# WNG — PASS CHECKPOINTS

Author/design authority: **Vardath**  
Active implementation repository: **public `Vardath/Wraith-Nanite-Gravtech-1.6`**  
Continuity repository: **public `Vardath/Vardath.github.io/wng-rebuild/`**

# PURPOSE

This is the mandatory short-pass checkpoint log for the WNG rebuild.

A **pass** is a bounded, coherent implementation batch — not one line or one tiny edit, and not a multi-hour uncheckpointed session. Each pass should complete a meaningful slice that can be reasoned about and validated before moving on.

After every meaningful pass, before beginning the next one, record exact public/branch SHAs, implementation, validation boundary, remaining debt and exact next steps. Never write branch-only work as public and never treat historical/private work as a known-good state.

---

# CHECKPOINT — 2026-09-11 — infiltration conceal/reveal promoted to public

Public mod `main` is now:

**`c7a9b46a3bef9393301d153e3f56c3c44c7ce95c` — `rebuild: add persistent Asuran infiltration concealment and reveal`**

Promotion used clean validated tree:

**`f90e8a3865d8465df9ba7c28bf75c94267c1c9fd`**

with parent public `8495b846...`, producing one clean public commit. Temporary validation-workflow history did not enter public `main`.

Public diff from `8495b...` contains exactly the intended conceal/reveal files:
- `Defs/FactionDefs/Factions_Asuran.xml`;
- `Defs/GeneDefs/Genes_AsuranInfiltration.xml`;
- `Defs/HediffDefs/Hediffs_AsuranNanite.xml`;
- `Defs/PawnKindDefs/PawnKinds_Asuran.xml`;
- `Defs/XenotypeDefs/Xenotypes_Asuran.xml`;
- `Source/WNG/Asuran/AsuranInfiltration.cs`;
- `Source/WNG/Asuran/AsuranNaniteFabrication.cs`;
- `Source/WNG/Asuran/AsuranNeuralInterface.cs`.

Validation inherited from run **`34600994766` — SUCCESS**:
- Release C# build passed;
- all current Def/Patch XML parsed;
- save-persistent exact-pawn reveal state present;
- Baseliner/Food-cover presentation -> real WNG nanite identity transition present;
- hidden synthetic health readouts while concealed;
- permanent reveal by direct Neural Interface scan, EMP, meaningful injury and accumulated visible self-repair;
- exact pawn/faction identity preserved through conceal/reveal;
- no Queen/block sovereignty inference from ordinary infiltrator state.

This remains source/Def validation, **not live RimWorld validation**.

## Current active branch

Fresh branch from exact new public HEAD:

**`rebuild/humanform-covert-presence-20260911`**

Base:

**`c7a9b46a3bef9393301d153e3f56c3c44c7ce95c`**

No branch-only implementation had been committed when this promotion checkpoint was written.

## Native API finding governing the next pass

Current RimWorld `GenHostility` was checked before designing covert presence. A pawn whose true `Pawn.Faction` remains hostile can still be non-hostile to the player while natively hosted because `HostFaction == Faction.OfPlayer` suppresses ordinary hostility. Therefore the next pass can preserve the exact infiltrator pawn's true `WNG_AsuranLattice` faction while using real `GuestStatus.Guest` as cover, rather than faking neutrality through pawn recreation or player-faction reassignment.

Current `LordJob_VisitColony` also supports a factionless Lord job, allowing visitor behavior without creating a hostile Lord danger signal while the pawn itself retains its real Asuran faction.

## Exact next pass

Implement one coherent **covert-presence / cover-break** path:
1. add Def-tunable/save-persistent covert-arrival scheduling;
2. generate the exact `WNG_AsuranInfiltrator` under true `WNG_AsuranLattice` faction;
3. set native player host/guest status while preserving true pawn faction;
4. use native visitor behavior without a hostile-faction Lord while cover is intact;
5. persist covert guest/activation state on the exact infiltration hediff;
6. on scan/injury/EMP/self-repair reveal or mission activation, clear cover natively and move the same pawn into true Asuran hostile assault behavior;
7. preserve valid native prisoner/slave captivity instead of forcibly converting a captured infiltrator back into an attacker;
8. source/Def validate, remove temporary validator, checkpoint before promotion/Quiet Lattice.

Human-form infiltration debt is **not yet complete** until this strategic covert presence/impersonation path is implemented and validated.

---

# PRIOR CHECKPOINT — human-form conceal/reveal foundation validated on branch

Public `main` at that checkpoint remained `8495b846c7dd31c079db6d4f007be490df3247f3`.

Branch:
**`rebuild/humanform-infiltration-20260911`**

Clean branch HEAD:
**`09e6c7eb741d3bf2629d067f99dae8554f45ed69`**

Validated source/Def tree:
**`6a9a0479ee0de1150eb892b4500af8d3f2dc1c81`**

Implemented:
- `WNG_AsuranInfiltrator` PawnKind and human-baseline mask xenotype;
- ordinary Food presentation while concealed using the same native `Need_Food` reserve quantity;
- exact save-persistent `Hediff_AsuranInfiltration` reveal state;
- hidden lattice/depletion/EMP health presentation while concealed;
- same-pawn permanent transition to real `WNG_NaniteHumanoid` identity;
- direct Neural Interface scan reveal;
- EMP reveal;
- Def-tunable meaningful-damage reveal (first-build 8 damage);
- Def-tunable accumulated self-repair suspicion reveal (first-build 1 HP);
- low-weight current Asuran infiltrator role wiring.

Validation run: **`34600994766` — SUCCESS**.

Important boundary retained: conceal/reveal is real, but covert arrival/guest/activation behavior remained unfinished at that checkpoint.

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
- Infiltration conceal/reveal foundation: **`c7a9b46a3bef9393301d153e3f56c3c44c7ce95c`**.

All completed public slices were source/Def validated before promotion; broad live RimWorld validation remains outstanding.
