# WNG — PASS CHECKPOINTS

Author/design authority: **Vardath**  
Active implementation repository: **public `Vardath/Wraith-Nanite-Gravtech-1.6`**  
Continuity repository: **public `Vardath/Vardath.github.io/wng-rebuild/`**

# PURPOSE

This is the mandatory short-pass checkpoint log for the WNG rebuild.

A **pass** is a bounded, coherent implementation batch — not one line or one tiny edit, and not a multi-hour uncheckpointed session. Each pass should complete a meaningful slice that can be reasoned about and validated before moving on.

After every meaningful pass, before beginning the next one, record exact public/branch SHAs, implementation, validation boundary, remaining debt and exact next steps. Never write branch-only work as public and never treat historical/private work as a known-good state.

---

# CHECKPOINT — 2026-09-11 — covert Asuran visitor / cover-break foundation validated on branch

## Public implementation state

Public mod `main` remains:

**`c7a9b46a3bef9393301d153e3f56c3c44c7ce95c` — persistent Asuran infiltration concealment/reveal.**

The covert-presence work below is branch-only at this checkpoint.

## Active branch

**`rebuild/humanform-covert-presence-20260911`**

Clean branch HEAD after removing the temporary validator:

**`ba72ec916fcb5cb984ebdc6d8000f2e3111f2efc` — `cleanup: remove covert presence validator`**

The validated source/Def tree was tested at `e021162cb41127badc902515a86fb182acbe417d`; `ba72ec...` differs only by removal of the temporary validation workflow.

## Mandatory native-API correction discovered in this pass

The immediately prior checkpoint said a permanently-hostile `WNG_AsuranLattice` pawn could simply be assigned native `GuestStatus.Guest` while keeping its active hostile faction. **That was incomplete and is superseded.**

Direct inspection of current RimWorld 1.6 `Pawn_GuestTracker.SetGuestStatus` shows that `GuestStatus.Guest` explicitly rejects a pawn whose current faction is hostile to the proposed host. Current `GenHostility` does suppress hostility for a valid `HostFaction`, but the hostile pawn cannot enter that guest state through the native API in the first place.

Therefore the validated WNG implementation uses real impersonation semantics instead of bypassing native rules:
- the exact infiltrator pawn temporarily carries a real non-hostile human cover faction while concealed;
- the exact true `WNG_AsuranLattice` faction reference is stored save-persistently on that same pawn's `Hediff_AsuranInfiltration`;
- native `GuestStatus.Guest` and `LordJob_VisitColony` then operate normally under the cover identity;
- reveal restores the stored exact Asuran source relationship on the same pawn and transitions it into real hostile Asuran behavior;
- no pawn recreation/proxy is used.

This is consistent with the recovered WNG requirement for actual impersonation and with Stargate lore that Asurans are human-looking nanite beings and, after base-code changes, Replicators can assume human forms/identities. It is a WNG gameplay extrapolation of that capability, not a claim that the Asuran Council canonically used RimWorld-style visitor infiltration.

## Files implemented in this pass

Updated:
- `Source/WNG/Asuran/AsuranInfiltration.cs`

Added:
- `Source/WNG/Asuran/AsuranCovertPresence.cs`
- `Defs/IncidentDefs/Incidents_AsuranCovertPresence.xml`

## What this pass implements

- exact true-faction and assumed-cover-faction references are persisted on the same infiltrator pawn;
- covert-presence and deferred-activation state persist through save/load;
- new save-persistent `GameComponent_AsuranCovertPresence` schedules rare infiltrator visits;
- cadence/chance/retry/visit duration/PawnKind/true-faction Def identity are author-tunable through `AsuranCovertPresenceExtension`;
- current first-build cadence is 4–8 in-game days with a 0.65 scheduled-attempt chance; these are tuning values, not design locks;
- the scheduler only targets player-home maps with living spawned colonists and will not stack another still-concealed covert visitor;
- cover identity is selected from a real visible non-hostile humanlike faction rather than inventing a fake cover faction;
- the exact `WNG_AsuranInfiltrator` pawn is generated under that temporary cover faction, preserving its existing concealed human-baseline mask physiology;
- native player `GuestStatus.Guest` is used under the cover identity;
- native `LordJob_VisitColony` drives visitor behavior and visit duration;
- the arrival letter presents only the assumed visitor identity and does not disclose the hidden Asuran source;
- the exact true Asuran faction remains stored on the pawn's persistent infiltration state;
- existing direct Neural Interface scan, EMP, meaningful injury and suspicious self-repair reveal paths now call the same cover-break activation path;
- ordinary reveal on a non-covert hostile infiltrator still only reveals synthetic identity and does not invent a new source faction;
- when a covert infiltrator is revealed while free, guest cover is cleared natively, the exact same pawn returns to its stored `WNG_AsuranLattice` faction, and a real `LordJob_AssaultColony` begins;
- if revealed while a native prisoner, the pawn remains a prisoner while its true Asuran faction is restored;
- if revealed while a native slave, hostile activation is deferred so slavery is not destroyed by WNG code; the same persistent state retries activation only after native slave status ends;
- if revealed while downed/off-map, true-faction restoration occurs and assault activation is deferred until physical conditions permit;
- no Queen identity or block-sovereignty authority is inferred from covert infiltrator state.

## Validation

GitHub Actions run:

**`34605318105` — SUCCESS**

Validated:
- Release C# build passed;
- all current Def/Patch XML parsed successfully;
- save-persistent covert scheduler state present;
- exact true/cover faction references present;
- native `GuestStatus.Guest` visitor path present;
- native `LordJob_VisitColony` path present;
- exact same-pawn reveal/hostile `LordJob_AssaultColony` transition present;
- incident is scheduler-only (`baseChance=0`) and category `Misc`;
- cadence is Def-driven rather than a fixed story-day gate.

Temporary validation workflow was removed at branch HEAD `ba72ec...`.

This is **source/Def validation, not live RimWorld validation**.

## Remaining infiltration debt

This pass materially completes the first planned covert-presence/impersonation path, but live behavior is still unverified. Remaining related work/dependencies include:
- live verification that visitor UI/faction display, guest AI and reveal transitions read correctly in-game;
- live verification of prisoner/slave reveal/save-load behavior;
- native WNG backstories remain missing, so covert visitors can still receive generic generated biography material until the backstory pass lands;
- dedicated final human-form art/audio remains later presentation debt;
- broader human-form society structure still requires Quiet Lattice, player human-form variants and broader role/faction composition.

## Exact next pass

**Promotion + Quiet Lattice reconciliation pass:**
1. recheck public `main` is still `c7a9b46...`;
2. promote the clean validated covert-presence tree to public `main` as one clean commit without temporary validator history;
3. update `CURRENT_PUBLIC_STATE.md` to the exact promoted SHA and remove strategic covert presence from missing-required debt while retaining live-test debt;
4. reconcile the entire Quiet Lattice/human-form faction slice against the canonical history, historical faction/backstory files, current public Defs/assets and Stargate lore before writing code;
5. implement the next coherent Quiet Lattice/player-human-form/faction-role foundation on a fresh public branch;
6. checkpoint again before moving to native WNG backstories or courier integration.

---

# PRIOR CHECKPOINT — infiltration conceal/reveal promoted to public

Public milestone:

**`c7a9b46a3bef9393301d153e3f56c3c44c7ce95c` — `rebuild: add persistent Asuran infiltration concealment and reveal`**

Validation run **`34600994766` — SUCCESS**.

Implemented foundation:
- `WNG_AsuranInfiltrator` PawnKind and human-baseline mask xenotype;
- ordinary Food presentation while concealed using the same native `Need_Food` reserve quantity;
- exact save-persistent `Hediff_AsuranInfiltration` reveal state;
- hidden lattice/depletion/EMP health presentation while concealed;
- same-pawn permanent transition to real `WNG_NaniteHumanoid` identity;
- direct Neural Interface scan reveal;
- EMP reveal;
- Def-tunable meaningful-damage reveal;
- Def-tunable accumulated self-repair suspicion reveal.

The old statement that covert guest status could be assigned directly while retaining a permanently hostile active faction is superseded by the native-API correction in the current checkpoint above.

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
