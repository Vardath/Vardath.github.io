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

# CHECKPOINT — 2026-09-11 — recurring Queen recovery landed; captured-Queen branch started

## Public implementation state

Public mod repository:

`Vardath/Wraith-Nanite-Gravtech-1.6`

Verified public `main`:

**`9ce713704505a220d357f8a6f234fb6e040e0b2e` — `docs: record recurring exact-map Queen recovery`**

### Landed immediately before this checkpoint

#### Temporary Asuran lattice intrusion

Public milestone:

**`26680fe84b95a0bfd5a23841b714fdba9cde1a98`**

Implemented:
- real temporary `TemporaryAsuran` authority transaction;
- exact snapshot of prior authority/controller/domain/faction;
- restoration of Queen/Neural-Lattice/autonomous state;
- EMP/containment/timeout/death/downing/separation interruption;
- split/recombine/save-load state continuity;
- no permanent Queen sovereignty for ordinary Asurans;
- hostile Asuran-lattice automatic trigger remains bounded/Def-tunable.

Validation:
- C# build passed;
- all Def/Patch XML parsed;
- temporary validation workflow removed before promotion;
- source/Def validation only, not live RimWorld validation.

#### Recurring exact-map Queen recovery

Public milestone:

**`9ce713704505a220d357f8a6f234fb6e040e0b2e`**

Implemented:
- later recovery attempts after the initial vault-triggered operation;
- exact target is the exact Queen's current player-home map only;
- no recovery attack on a different colony while Queen is traveling/off-map;
- existing real recovery Jumper/subdual/loading/departure/capture transaction reused;
- current cadence is Def-tunable, first-build default 2–4 in-game days;
- transient spawn failure retries rather than silently consuming the attempt;
- one real Queen-recovery operation at a time;
- exact recovery operatives are determined from the recovery Jumper's native `CompShuttle.requiredPawns`, so unrelated Asurans cannot keep a failed recovery marked active;
- scheduler state is save-persistent.

Validation:
- C# build passed;
- Def/Patch XML parse passed after exact-operative refinement;
- temporary validation workflow removed before promotion;
- source/Def validation only, not live RimWorld validation.

## Current branch-only work

Active branch:

**`rebuild/captured-queen-sovereign-threats-20260911`**

Current branch SHA:

**`af77e358a411f25e7c2ab88dfeb8a76e4b2bff03` — assimilation offspring sovereignty inheritance correction**

This branch is **NOT public `main` yet**.

Implemented on branch during the first captured-Queen pass:
- assimilation-born Replicator offspring now copy the parent's `CompReplicatorSovereignty` state in addition to learned Replicator/adaptation state;
- this closes the inheritance defect where Queen-, Neural-Lattice- or Temporary-Asuran-controlled hostile blocks could reproduce children that silently lost their exact controller domain.

Validation state:
- branch change committed;
- full branch validation/promotion has **not yet** been completed for the captured-Queen slice.

## Captured-Queen consequence design boundary established

The next consequence is not an abstract faction buff, outbreak counter or proxy Queen.

Required architecture:
- the **exact kidnapped Queen pawn** remains the genuine controller identity;
- Asuran-backed sovereign blocks must carry real `Queen` authority with that exact pawn as controller;
- the exact capturing Asuran faction must genuinely retain the Queen in its native kidnapped-pawn tracker for this remote/captive control path to remain valid;
- if that faction no longer retains the exact Queen, remote captured-Queen authority becomes invalid and controlled blocks fall back through normal recorded authority/faction release behavior;
- rescuing/recovering the Queen must therefore have real mechanical consequences;
- mixed Asuran + sovereign block threats must use real spawned block Replicators, real same-domain behavior and normal Replicator specialist/combat logic.

## Next pass

Complete a coherent captured-Queen sovereign-threat batch, not a one-line micro-pass:

1. Add exact **captor-retention detection** using the Asuran faction's native `KidnappedPawnsTracker` and the exact global Queen reference.
2. Extend Queen authority validity with a narrowly-scoped **captured-Lattice remote-control case** that applies only while that exact Asuran faction genuinely retains that exact Queen.
3. Add a safe assignment/spawn path that creates real Asuran-owned block Replicators carrying the exact captured Queen's `Queen` authority/domain.
4. Build the first mixed Asuran + sovereign-block hostile threat composition around that exact state.
5. Ensure authority collapses/reverts correctly if the exact Queen is no longer retained.
6. Re-check assimilation offspring, hierarchy split/recombine and same-domain behavior under captured-Queen authority.
7. Run C# build + Def/Patch XML validation on the whole captured-Queen branch.
8. Only then consider promotion to public `main`.
9. After that pass, update this file **before starting the next subsystem**.

## Continuity maintenance debt at this checkpoint

`CURRENT_PUBLIC_STATE.md` still records public HEAD `26680fe...` and still lists recurring Queen recovery as unfinished. It must be updated to public HEAD **`9ce713...`** and recurring recovery must move from debt to implemented foundation. This correction should be made as part of the next continuity write, not forgotten.
