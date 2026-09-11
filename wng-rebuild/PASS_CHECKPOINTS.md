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

# CHECKPOINT — 2026-09-11 — captured Queen mixed sovereign threat validated on branch

## Public implementation state

Public mod `main` remains:

**`9ce713704505a220d357f8a6f234fb6e040e0b2e` — recurring exact-map Queen recovery.**

The captured-Queen consequence branch is validated but has **not yet been promoted** at this checkpoint.

## Active branch

Branch:

**`rebuild/captured-queen-sovereign-threats-20260911`**

Current clean branch HEAD after removing the temporary validator:

**`4ec9872d5f34c1c1ed542e0da93b5052b25e45f8` — `cleanup: remove captured Queen mixed threat validator`**

The validated mixed-threat source/Def tree was tested at `2859e9d174d569e1910cff4ca92c05e0ac493870`; `4ec987...` differs only by removal of the temporary validation workflow.

## What this pass implemented

New source:

`Source/WNG/Replicators/ReplicatorCapturedQueenThreats.cs`

New Def:

`Defs/IncidentDefs/Incidents_CapturedQueen.xml`

Implemented behavior:
- new `CapturedQueenThreatExtension` keeps cadence, retry delay, attempt chance, Asuran count, block count, point share and composition chances author-tunable in Def data;
- current first-build schedule is 3–6 in-game days with a 0.70 scheduled-attempt chance and a short retry delay for transient inability to fire; these are tuning values, not design locks;
- `GameComponent_CapturedQueenThreats` persists `nextThreatTick`/check state through save/load;
- scheduler is active only while the exact global Queen is genuinely retained in the exact `WNG_AsuranLattice` native kidnapped-pawn tracker;
- losing that exact retention resets the scheduler rather than leaving a permanent Asuran bonus;
- only player-home maps with living spawned free colonists are eligible targets;
- the Queen herself is **not** falsely spawned/projected onto the target map;
- an already-active captured-Queen sovereign block force prevents another mixed force from stacking immediately;
- `WNG_CapturedQueenSovereignStrike` has `baseChance=0`; it is driven by the captured-Queen scheduler rather than accidentally entering ordinary storyteller random incident selection;
- threat size uses current storyteller points and a Def-tunable Asuran/block point split, with bounded min/max counts;
- real `WNG_AsuranOperative`, `WNG_AsuranTechnician` and `WNG_AsuranCommander` PawnKinds form the human-form side;
- block force uses real Drone/Hunter plus Def-tunable chances for Controller/Repairer/Burrower/Artillery, Bulwark and high-point Titan presence; Siege Mass is deliberately not in this first mixed-strike pool;
- every block is generated first under real autonomous `WNG_ReplicatorSwarm` ownership and only then assigned with `TryAcquireForCapturedQueen`;
- this preserves each block's real autonomous `originalFaction`, so when exact Queen retention ends its Queen authority validation fails and existing sovereignty release returns it to the autonomous swarm instead of leaving a permanent Asuran-owned fake;
- every successfully bound block uses genuine `ReplicatorControlAuthority.Queen`, exact Queen pawn reference and exact Queen domain key;
- Asurans and sovereign blocks are put into one real hostile `LordJob_AssaultColony` under the exact captor faction;
- existing Replicator same-domain specialist/combat behavior remains in use rather than adding a proxy combat system;
- spawn rollback removes a partially constructed force if the mixed incident cannot establish at least one real Asuran and one real sovereign block.

## Validation

GitHub Actions run:

**`34596657164` — SUCCESS**

Validated:
- `dotnet build Source/WNG/WNG.csproj -c Release` — passed;
- all current Def/Patch XML parsed successfully;
- captured-Queen mixed-threat scheduler/state invariant present;
- exact captured-Queen retention lookup present;
- autonomous Replicator source-faction path present;
- captured-Queen assignment path present;
- real `LordJob_AssaultColony` integration present;
- save persistence for next threat tick present;
- incident Def is scheduler-only (`baseChance=0`) and points-scalable.

Temporary validation workflow was removed at `4ec987...`.

This is **source/Def validation, not live RimWorld validation**.

## Captured-Queen consequence status after this pass

Branch implementation now contains the complete current planned foundation for:
- captured-Queen exact retention;
- remote exact-Queen sovereign block authority;
- authority collapse when retention ends;
- assimilation offspring authority inheritance;
- save-persistent captured-Queen consequence scheduling;
- real mixed Asuran + sovereign block hostile strikes.

Remaining for this branch before moving to another subsystem:
- promote the clean validated tree to public `main` without dragging temporary validation-helper commits into public history if practical;
- update `CURRENT_PUBLIC_STATE.md` to the promoted public HEAD and remove captured-Queen mixed threats from the required-debt list;
- live RimWorld validation remains pending and must stay recorded as such.

## Exact next pass

**Promotion + continuity pass:**

1. Recheck public `main` has not advanced from `9ce713...`.
2. Promote the clean validated captured-Queen tree to public `main` as a clean fast-forward/squashed public commit where practical.
3. Verify public `main` contains only intended source/Def changes and no temporary validation workflow/helper.
4. Update `CURRENT_PUBLIC_STATE.md` with the exact new public HEAD and captured-Queen consequence status.
5. Update this checkpoint with the promoted SHA.
6. Select the next genuine required subsystem from the reconciled debt list; current likely next major rebuild branch is the human-form Neural Interface / exact copy-reconstruction foundation unless newer Vardath instruction changes priority.

---

# PRIOR CHECKPOINT — captured Queen remote-sovereignty foundation validated on branch

Public mod `main` at that checkpoint:

**`9ce713704505a220d357f8a6f234fb6e040e0b2e`**

Validated branch milestone:

**`70533bf848a6b1d00f15bf5f6a7b06c7e49a25dc` — captured Queen remote-sovereignty foundation.**

That pass implemented:
- assimilation-born sovereignty inheritance;
- exact captured-Queen retention against native `KidnappedPawnsTracker`;
- captured-Queen faction lookup;
- real remote exact-Queen authority assignment/validation;
- exact authority collapse/reversion when retention ends.

Validation run: **`34596238345` — SUCCESS**.

---

# EARLIER PUBLIC MILESTONES

- Temporary Asuran lattice intrusion: **`26680fe84b95a0bfd5a23841b714fdba9cde1a98`**.
- Recurring exact-map Queen recovery: **`9ce713704505a220d357f8a6f234fb6e040e0b2e`**.

Both were source/Def validated before promotion; broad live RimWorld validation remains outstanding.
