# WNG — PASS CHECKPOINTS

Author/design authority: **Vardath**  
Active implementation repository: **public `Vardath/Wraith-Nanite-Gravtech-1.6`**  
Continuity repository: **public `Vardath/Vardath.github.io/wng-rebuild/`**

A pass is a bounded coherent implementation batch. Before beginning the next pass, record exact public/branch SHAs, actual implementation, validation boundary, discovered defects/dependencies, remaining work and exact next steps. Branch-only work is never written as public. Historical/private WNG is reference evidence only.

---

# CHECKPOINT — 2026-09-12 — Strategic Wraith hunger count/names UI reconciliation complete

## Public state

Public mod `main` remains:

**`e1a080c93893ff5742f5aa91bc00fd7ecc1699f7` — bounded Wraith Growth Chamber.**

No strategic-hunger UI code was changed in this reconciliation pass.

## Recovered corrected requirement

The recovered plan and explicit later correction agree:
- these boxes belong only to **genuine faction-level strategic Wraith hunger**;
- ordinary pawn `Drain Life`/feeding never opens them;
- local Mature-Hive Feeding Niches/feeding stock never opens them;
- box/stage 1 is only about the biological prisoner/feeding-stock subject(s); individual Wraiths are never selected there;
- submitting stage 1 advances to stage 2;
- stage 2 shows the **count and names of the Wraiths involved/to be fed**;
- the decision sequence remains paused from opening until final completion;
- final Submit accepts/fulfils the feeding agreement;
- Cancel/refusal is a real refusal and retains the configured attack/raid consequence.

Current public source is mechanically incomplete against that requirement: it opens an initial `Dialog_MessageBox`, then releases `requestWindowOpen` and opens a `FloatMenu` of prisoners. There is no involved-Wraith count/name stage, and the flow is not locked as one paused transaction across stages.

## Native UI/API check

RimWorld 1.6 `Dialog_MessageBox` is already a force-paused, input-absorbing `Window`, so it is suitable for the final count/name confirmation stage.

The current prisoner `FloatMenu` is not the correct transaction surface for the recovered requirement. Stage 1 therefore needs a small WNG `Window` with `forcePause=true` / `absorbInputAroundWindow=true` so subject selection/identification and Submit/Cancel remain inside the same paused decision transaction.

## Involved-Wraith identity boundary

Recovered history specifies that count/names must be shown, but it does **not** specify an arbitrary numeric formula such as “N Wraiths per hunger percentage.” Do not invent such a formula merely to make the box look populated.

The first implementation therefore uses **real Wraith pawn identities only**:
- prefer living, same-faction Wraith pawns physically present on the request home map when such Wraiths genuinely exist there;
- otherwise use the requesting faction's exact living Wraith leader as the involved identity;
- deduplicate exact pawns;
- do not generate disposable presentation-only names/pawns;
- if no valid real same-faction Wraith identity can be resolved, do not open a misleading request; schedule the normal retry instead.

This means the count displayed in stage 2 is the count of the actual resolved Wraith identities, not a fabricated hunger-derived number. A later Vardath-defined multi-Wraith roster formula can replace this without redesigning the transaction.

## Exact UI/data-flow decision

**Stage 1 — feeding-stock subject selection/identification**
- open only after the existing genuine strategic-hunger threshold/chance checks pass;
- show eligible biological prisoner/feeding-stock names only;
- player selects the subject if more than one is available;
- no Wraith selection appears in this stage;
- Submit is disabled until one valid subject is selected;
- Cancel/refusal calls the existing strategic refusal path and therefore preserves faction hostility/forced-raid behavior where configured;
- `requestWindowOpen` remains true; stage 1 Submit does not release the strategic request lock.

**Stage 2 — involved-Wraith roster confirmation**
- receives the exact selected prisoner and exact resolved Wraith pawn references from stage 1;
- force-paused `Dialog_MessageBox` displays the requesting faction, exact involved-Wraith count and each resolved Wraith name, plus the selected prisoner's name and existing biological-age/Life-Drained consequence;
- no Wraith selection controls exist;
- Submit invokes the existing strategic `AcceptRequest` effect on that exact prisoner and only then clears `requestWindowOpen`;
- Cancel/refusal invokes the existing `RefuseRequest` consequence and only then clears `requestWindowOpen`.

## Failure/closure boundary

- any invalid/dead/despawned subject at final Submit becomes refusal rather than silently feeding a replacement prisoner;
- if the real involved-Wraith roster becomes invalid between stages, the request is refused/retried safely rather than substituting fabricated names;
- close/cancel/Escape behavior must map to the same refusal outcome so the player cannot dismiss the request without consequence;
- ordinary strategic hunger records/timers remain the authority; this is not converted into a Quest system;
- no ordinary `Drain Life`, Mature-Hive local ecology or retaliation code is changed in this pass.

## Exact next pass

**Implement only this strategic-hunger two-stage paused UI** on a fresh branch from public `e1a080c...`:
1. add the force-paused WNG subject-selection dialog;
2. keep one request lock active across both stages;
3. resolve exact real same-faction involved Wraith identities without synthetic names;
4. add stage-2 count/name confirmation using native force-paused dialog behavior;
5. preserve existing accept/refusal/raid consequences and faction-specific hunger state;
6. do not alter ordinary feeding, Mature-Hive feeding stock, Growth Chamber, or retaliation;
7. validate using the corrected small-helper/minimal-workflow method rather than another large inline workflow;
8. checkpoint validated branch before promotion.

---

# PRIOR PUBLIC MILESTONE — Wraith Growth Chamber

Public mod milestone: **`e1a080c93893ff5742f5aa91bc00fd7ecc1699f7`**.  
Validation run: **`34612430265` — SUCCESS**.

---

# PUBLIC MILESTONES

- `26680fe84...` — Temporary Asuran lattice intrusion.
- `9ce7137045...` — recurring exact-map Queen recovery.
- `0b8150f3ff...` — captured-Queen sovereign consequences.
- `8495b846c7...` — Neural Interface / exact reconstruction.
- `c7a9b46a3b...` — infiltration conceal/reveal.
- `87da0e5243...` — covert visitor impersonation.
- `b242dc72d1...` — Quiet Lattice society.
- `45e62cd7f5...` — native WNG backstories.
- `12590e8ea8...` — physical Replicator Grav adaptation.
- `b5cde48e3c...` — native energy-shield AntiShield integration.
- `e1a080c938...` — bounded Wraith Growth Chamber.

All completed public milestones were source/Def validated before promotion. Broad live RimWorld validation remains outstanding.
