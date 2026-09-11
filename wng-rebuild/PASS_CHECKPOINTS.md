# WNG — PASS CHECKPOINTS

Author/design authority: **Vardath**  
Active implementation repository: **public `Vardath/Wraith-Nanite-Gravtech-1.6`**  
Continuity repository: **public `Vardath/Vardath.github.io/wng-rebuild/`**

A pass is a bounded coherent implementation batch. Before beginning the next pass, record exact public/branch SHAs, actual implementation, validation boundary, discovered defects/dependencies, remaining work and exact next steps. Branch-only work is never written as public. Historical/private WNG is reference evidence only.

---

# CHECKPOINT — 2026-09-12 — Strategic Wraith hunger two-stage UI validated on branch

## Public state

Public mod `main` remains:

**`e1a080c93893ff5742f5aa91bc00fd7ecc1699f7` — bounded Wraith Growth Chamber.**

Strategic-hunger UI work is branch-only at this checkpoint.

## Active branch

**`rebuild/wraith-hunger-request-ui-20260912`**

Validated clean branch HEAD:

**`639c4a284dcd8254aea4e9e7dfb6d7f507939498` — `rebuild: complete paused strategic Wraith feeding request UI`**

Clean tree:

**`f2c5a161a65fa0879a4980d29eadf21d7c9ed492`**

Clean compare against public contains exactly two intended files:
- `Source/WNG/Wraith/WraithFactionHunger.cs` — strategic request flow modified;
- `Source/WNG/Wraith/WraithFeedingRequestDialog.cs` — new paused stage-one subject dialog.

Temporary workflow/helper files are absent from clean branch HEAD.

## Implemented behavior

- genuine strategic faction hunger remains the only source of the feeding-request UI;
- the previous initial-message-plus-`FloatMenu` flow is removed;
- stage 1 is a dedicated WNG `Window` with `forcePause=true`, `absorbInputAroundWindow=true`, no close-X and no click-outside dismissal;
- stage 1 shows only eligible prisoner/feeding-stock subjects, preserving the rule that the player does not choose Wraiths there;
- one subject is auto-selected only when exactly one eligible subject exists; otherwise the player selects a prisoner by exact pawn name;
- stage 1 displays current strategic hunger percentage, the existing biological-age/Life-Drained consequence, and the refusal-pressure warning;
- Submit advances to stage 2 without releasing `requestWindowOpen`;
- Cancel/Escape routes through the existing `RefuseRequest` path, including configured forced-raid consequence;
- stage 2 is native force-paused `Dialog_MessageBox` and shows selected subject, exact involved-Wraith count and each exact Wraith name;
- involved Wraiths are **not fabricated**: living operational same-faction Wraiths physically present on the home map are used when present; otherwise the exact living same-faction faction leader is used;
- if no real Wraith identity can be resolved, the request is not opened and uses the normal retry timer;
- if the exact roster becomes invalid between stages, the request is safely released for retry rather than substituting fake names;
- final Submit clears the request lock and invokes the existing `AcceptRequest` effect on the exact selected prisoner;
- final Cancel/Escape clears the lock and invokes the existing refusal/raid consequence;
- invalid selected prisoner at final completion remains a refusal; no replacement prisoner is silently substituted;
- no Quest conversion and no changes to ordinary Drain Life, Mature-Hive feeding ecology, Growth Chamber, Dormancy Vault or retaliation.

## Reconciliation boundary retained

Recovered history requires count/names but contains no rule for inventing a hunger-percentage participant count. This implementation therefore reports actual resolved Wraith pawn identities rather than creating arbitrary presentation-only pawns or names. Any later Vardath-defined multi-Wraith roster rule can replace the resolver without changing the two-stage UI transaction.

## Validation

Validation run:

**`34613728004` — SUCCESS**

Passed:
- targeted strategic-hunger source patch;
- Release C# build;
- all Def/Patch XML parsing;
- force-paused stage-one dialog invariants;
- exact involved-Wraith stage-two count/name invariants;
- single request lock across both stages;
- Submit/Cancel paths tied to existing accept/refusal methods;
- removal of old `FloatMenu` prisoner stage;
- explicit invariant forbidding `PawnGenerator.GeneratePawn` in this UI pass, preventing fake presentation identities;
- explicit subsystem-boundary checks against Drain Life, Feeding Niche, Dormancy Vault and Growth Chamber coupling;
- temporary validation workflow/helpers removed before clean branch HEAD.

The validation used the corrected **small helper scripts + minimal workflow** method established after the repeated workflow-wrapper failures. No large inline validation workflow was reintroduced.

This remains **source/Def validation, not live RimWorld validation**.

## Exact next pass

**Promotion-only pass:**
1. recheck public `main` is still `e1a080c...`;
2. promote clean tree `f2c5a161...` as one public commit with parent `e1a080c...`;
3. verify public diff is exactly the two intended strategic-hunger UI files;
4. update `CURRENT_PUBLIC_STATE.md` and this checkpoint to exact promoted SHA;
5. remove the strategic-hunger count/names UI stage from missing-required debt;
6. only then begin reconciliation of broader discovery/story progression.

---

# PREVIOUS RECONCILIATION DECISION

The recovered corrected sequence is: stage 1 identifies/selects feeding-stock prisoner subject(s) only; Submit advances to stage 2; stage 2 shows count/names of involved Wraiths; final Submit accepts, Cancel/refusal retains raid pressure; the game remains paused throughout. Ordinary Wraith feeding never creates these boxes.

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
