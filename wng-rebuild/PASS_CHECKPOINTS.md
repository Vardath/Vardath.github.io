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

# CHECKPOINT — 2026-09-11 — captured Queen consequences promoted to public

## Public implementation state

Public mod `main` is now:

**`0b8150f3ff6ca7138482ba9a604847f5967fc48b` — `rebuild: add captured Queen sovereign consequences`**

Promotion was created as one clean public commit using the already-validated clean branch tree with parent `9ce713...`. Temporary validation/helper commits were **not** copied into public `main` history.

Public diff from `9ce713...` contains only intended files:
- `Defs/IncidentDefs/Incidents_CapturedQueen.xml` — added;
- `Source/WNG/Replicators/ReplicatorCapturedQueenThreats.cs` — added;
- `Source/WNG/Replicators/ReplicatorSovereignty.cs` — captured-retained-Queen remote authority foundation;
- `Source/WNG/Replicators/ReplicatorAssimilation.cs` — offspring sovereignty inheritance.

No temporary captured-Queen validation workflow/helper is present in the promoted tree.

## Validation inherited by promoted tree

- remote-sovereignty run **34596238345** — SUCCESS;
- mixed-threat run **34596657164** — SUCCESS;
- C# Release build passed;
- all current Def/Patch XML parsed;
- captured Queen retention/remote-authority/assimilation inheritance invariants passed;
- save-persistent scheduler/autonomous-source block/real mixed assault invariants passed.

This remains source/Def validation, **not live RimWorld validation**.

## Continuity state

`CURRENT_PUBLIC_STATE.md` is updated to exact public HEAD `0b8150...` and removes captured-Queen sovereign consequences/mixed threats from the required debt list.

## Exact next pass

Start a fresh bounded public-repo branch from `0b8150...` for the **Human-form Neural Interface / exact copy-reconstruction foundation**.

Before implementing:
1. inspect current public human-form Asuran/Nanite Reserve/workshop/resource architecture;
2. inspect historical/private Neural Interface only as behavior/reference evidence, never as a known-good source to copy wholesale;
3. map each operation to native RimWorld 1.6/DLC mechanics;
4. first coherent implementation pass should establish the real Neural Interface building/interaction transaction layer and native recruit/imprison/Ideology-enslave operations, plus the resource-cost/rollback mechanism required by later copying;
5. exact copy/reconstruction of biography/name/skills/passions/XP/appearance/genome follows as the next bounded pass unless it can be safely completed in the same validated batch;
6. checkpoint before moving on.

---

# PRIOR CHECKPOINT — captured Queen mixed sovereign threat validated on branch

Public mod `main` at that checkpoint remained `9ce713...`.

Clean branch HEAD:

**`4ec9872d5f34c1c1ed542e0da93b5052b25e45f8`**

Implemented:
- Def-tunable/save-persistent captured-Queen consequence scheduler;
- scheduler-only `WNG_CapturedQueenSovereignStrike`;
- real mixed Asuran + Queen-domain block force;
- autonomous-source block generation then real captured-Queen assignment;
- real hostile `LordJob_AssaultColony`;
- authority collapse/reversion when exact retention ends;
- bounded points-scaled composition and rollback.

Validation run: **34596657164 — SUCCESS**.

---

# PRIOR CHECKPOINT — captured Queen remote-sovereignty foundation validated on branch

Validated branch milestone:

**`70533bf848a6b1d00f15bf5f6a7b06c7e49a25dc`**

Implemented:
- assimilation-born sovereignty inheritance;
- exact captured-Queen retention against native `KidnappedPawnsTracker`;
- captured-Queen faction lookup;
- real remote exact-Queen authority assignment/validation;
- exact authority collapse/reversion when retention ends.

Validation run: **34596238345 — SUCCESS**.

---

# EARLIER PUBLIC MILESTONES

- Temporary Asuran lattice intrusion: **`26680fe84b95a0bfd5a23841b714fdba9cde1a98`**.
- Recurring exact-map Queen recovery: **`9ce713704505a220d357f8a6f234fb6e040e0b2e`**.
- Captured Queen sovereign consequences: **`0b8150f3ff6ca7138482ba9a604847f5967fc48b`**.

All were source/Def validated before public promotion; broad live RimWorld validation remains outstanding.
