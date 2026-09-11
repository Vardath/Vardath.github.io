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

# CHECKPOINT — 2026-09-11 — captured Queen remote-sovereignty foundation validated on branch

## Public implementation state

Public mod `main` remains:

**`9ce713704505a220d357f8a6f234fb6e040e0b2e` — recurring exact-map Queen recovery.**

No captured-Queen consequence work from this pass has been promoted to public `main` yet.

## Active branch

Branch:

**`rebuild/captured-queen-sovereign-threats-20260911`**

Validated branch HEAD:

**`70533bf848a6b1d00f15bf5f6a7b06c7e49a25dc` — `rebuild: add captured Queen remote sovereignty foundation`**

## What this pass implemented

- assimilation-born block Replicators now inherit the parent block's exact `CompReplicatorSovereignty` state as well as learned Replicator/adaptation state;
- added exact captured-Queen retention detection against the **real `WNG_AsuranLattice` faction's native `KidnappedPawnsTracker`** and exact global Queen pawn reference;
- captured-Queen remote authority exists only while `GameComponent_ReplicatorQueenState` says the exact Queen is `CapturedByAsurans` **and** that exact Asuran Lattice faction still physically/native-logically retains that exact pawn in `KidnappedPawnsListForReading`;
- added captured-Queen faction lookup for the exact retained Queen;
- added `TryAssignCapturedQueen` / `TryAcquireForCapturedQueen` assignment path for real spawned WNG block Replicators;
- captured-Queen blocks use genuine `ReplicatorControlAuthority.Queen`, the exact kidnapped Queen pawn as controller, and the exact Queen domain key — no proxy Queen, outbreak modifier or abstract faction buff;
- captured remote Queen authority is allowed to remain valid without same-map physical presence **only** for the exact retained-Queen/captor-faction case;
- remote blocks must actually belong to that exact captor faction for authority to remain valid;
- if the exact Queen is no longer retained by that faction, normal per-block sovereignty validation fails and the existing release path restores the recorded pre-control/autonomous faction/domain;
- rescuing/removing the exact Queen therefore has a real mechanical effect on any remote captured-Queen sovereign blocks;
- ordinary player Queen control, Neural-Lattice control and Temporary-Asuran intrusion retain their existing physical-presence/identity rules.

## Validation

GitHub Actions run:

**`34596238345` — SUCCESS**

Validated:
- `dotnet build Source/WNG/WNG.csproj -c Release` — passed;
- all current Def/Patch XML parsing — passed;
- captured-Queen retention/assignment/remote-validity invariants — passed;
- assimilation sovereignty inheritance invariant — passed;
- temporary workflow and patch helper removed by the validated branch commit.

This is **source/Def validation, not live RimWorld validation**.

## Validation-wrapper failures during this pass

Two temporary workflow attempts failed before modifying source because the embedded patch wrapper was malformed. They were validation-mechanism failures only; no failed source patch was promoted. The final direct patch-script workflow succeeded and removed its temporary helpers.

## Remaining captured-Queen slice

Still not implemented/public:
- actual mixed **Asuran + sovereign block Replicator hostile threat composition**;
- a Def-tunable event/incident cadence/trigger for those threats while the exact Queen remains captured;
- real spawning of autonomous-source Replicator blocks followed by captured-Queen assignment so loss of Queen retention can revert them to `WNG_ReplicatorSwarm` rather than leaving permanent Asuran-owned blocks;
- sensible block form/specialist mix and threat sizing;
- exact hostile Lord/assault integration;
- save/load/event scheduling rules preventing duplicate threats;
- live RimWorld validation.

## Exact next pass

Build one coherent **captured-Queen mixed-threat pass**:

1. Add a captured-Queen consequence Def/extension with author-tunable interval/chance/threat composition rather than hard-coded story-day behavior.
2. Schedule threats only while the exact Queen is genuinely retained by `WNG_AsuranLattice`.
3. Target an eligible player-home map using normal hostile incident rules; do not pretend the Queen herself is physically on that map.
4. Spawn real Asuran human-form combatants plus real WNG block Replicators.
5. Generate block Replicators from the autonomous `WNG_ReplicatorSwarm` faction first, then bind them through `TryAcquireForCapturedQueen` so their `originalFaction` is the real autonomous swarm.
6. Use real Queen authority/domain on every sovereign block, real same-domain specialist behavior and normal Replicator combat AI.
7. Give the mixed force a real hostile assault Lord/job.
8. Ensure the event is unavailable when exact Queen retention ends and existing remote blocks subsequently release through normal sovereignty validation.
9. Run C# build + Def/Patch XML + static mixed-threat invariants.
10. Checkpoint this file again before promotion or the next subsystem.

---

# PRIOR CHECKPOINT — recurring Queen recovery landed; captured-Queen branch started

Public milestone before this branch:

**`9ce713704505a220d357f8a6f234fb6e040e0b2e`**

Landed public foundations immediately before the captured-Queen branch:
- Temporary Asuran lattice intrusion at `26680fe84b95a0bfd5a23841b714fdba9cde1a98`;
- recurring exact-map Queen recovery at `9ce713704505a220d357f8a6f234fb6e040e0b2e`;
- recurring recovery uses only the exact Queen's physically occupied player-home map, real recovery Jumper/subdual/loading/departure semantics, one operation at a time, Def-tunable 2–4 day current cadence and save-persistent scheduling;
- both public slices passed C# build and Def/Patch XML validation before promotion; live RimWorld validation remains required.

The captured-Queen branch originally began at `af77e358a411f25e7c2ab88dfeb8a76e4b2bff03` with the assimilation offspring sovereignty-inheritance correction; that work is now included in validated branch HEAD `70533bf...` above.
