# WNG — Replicator Queen / Asuran recovery / controller design

This is a working first-build design, not immutable canon. Vardath may alter details after testing.

## Current implementation checkpoint — 2026-09-11

Public mod implementation through:

**`0e5dfc893a8efec624053e677ae99d6983c25fc9` — validated Sovereign Neural Lattice build with temporary workflow removed**

Implemented now:
- one exact persistent Queen pawn;
- real cryptosleep-vault release and immediate player recruitment;
- first physical all-or-nothing four-operative Asuran recovery/capture attempt;
- capture only when the exact Queen physically leaves inside the exact recovery Jumper transit container;
- genuine exact-Queen controller-domain authority over real block Replicators;
- physical Sovereign Neural Lattice implant for bounded non-Queen controller authority;
- authority persistence through save/load and block split/recombine;
- dedicated controller-linked block commands;
- EMP/containment interference and physical-presence validity;
- controller-domain isolation across hierarchy, Controller coordination, Repairer support and retaliation.

Not yet implemented:
- temporary Asuran lattice intrusion;
- later recurring Queen recovery attempts;
- captured-Queen hostile sovereign consequences / mixed Asuran + block threats;
- infiltration / broader Neural Interface copy-reconstruction;
- live RimWorld validation/balance tuning.

## Queen identity

Current exact Queen:
- unique human-form Replicator individual;
- female;
- age 13 in current first-build design;
- `WNG_NaniteHumanoid` physical identity;
- unique innate sovereignty belongs only to that exact pawn;
- one exact pawn/state persists through storyline and capture;
- ordinary Asuran Operative/Technician/Commander roles remain separate and do not gain Queen authority by sharing physiology.

## Vault/release — IMPLEMENTED

- neutral Queen-vault world site;
- exact Queen physically held in vanilla `CryptosleepCasket`;
- only the Dormant exact Queen becoming physically spawned on the real vault map triggers release;
- she joins the player immediately;
- later map transitions cannot replay release/reset first recovery timer;
- synthetic Queen does not keep ordinary cryptosleep-sickness residue.

## First Asuran recovery — IMPLEMENTED FOUNDATION

Current flow:
1. exact Queen released;
2. global bounded recovery delay begins;
3. recovery requires all four configured `WNG_AsuranOperative` pawns to spawn or the partial attempt is rolled back;
4. operatives are generated without ordinary weapons;
5. dedicated subdue/load/hold jobs are nonlethal and damage-override-proof;
6. one exact operative uses native `StunHandler` against the exact Queen;
7. the real Queen is physically carried to the real Asuran recovery Jumper;
8. she is transferred into that exact native transporter;
9. surviving operatives physically board;
10. stun/down/carry/load are **not capture**;
11. only the exact shuttle actually leaving the map with the exact Queen still inside commits capture;
12. successful departure registers the same pawn in exact Asuran faction native kidnapped-pawn state and marks WNG global Queen state captured;
13. failed/unprovable departure does not silently consume/proxy her.

Current timings/counts remain Def-tunable.

## Later recovery raids — UNFINISHED

Required:
- may target any player map physically containing the exact Queen;
- never target another map while she is elsewhere/caravaning/off-map/dead/already captured;
- real raid/entry rather than teleport beside her;
- physical subdual/carry/carrier departure remains the capture boundary;
- cadence must remain tunable and non-spammy.

---

# CONTROLLER AUTHORITY

## Shared real controller-domain architecture — IMPLEMENTED

`CompReplicatorSovereignty` lives on every WNG block body and distinguishes:
- `None`;
- `Queen`;
- `NeuralLattice`;
- future `TemporaryAsuran`.

A controlled block stores exact authority/controller/domain/faction metadata and changes real faction ownership. It remains the same physical hierarchy/adaptation/matter pawn—not a proxy or outbreak modifier.

Different controller domains cannot recombine, coordinate, repair or share retaliation simply because faction matches.

## Exact Queen authority — IMPLEMENTED

Current behavior:
- exact living WNG block targets;
- exact Queen reference + persistent Queen domain key;
- block pre-control faction recorded;
- real faction transfer to Queen's faction;
- valid while physically together on same map or same caravan;
- invalid authority releases/restores prior faction where possible;
- Queen EMP, block EMP and active containment interfere;
- dedicated move/attack/Repairer/Burrower/recombine/release commands;
- explicit upward recombination retains real hierarchy requirements;
- split/recombine conserves exact Queen domain, adaptations and stored matter;
- Queen human-form Nanite Reserve remains separate from block stored matter.

Current Def tuning:
- 40-cell exact-target acquisition;
- 24-cell nearby-swarm acquisition radius;
- normal cap 12 controlled spawned bodies.

Validation run **34576583840**: C# build, XML parse and sovereignty-domain invariants SUCCESS. Live RimWorld testing pending.

## Sovereign Neural Lattice authority — IMPLEMENTED

The **Sovereign Neural Lattice is a WNG-specific Stargate-derived extrapolation**, not a claim of a canon-named device. Its design derives from demonstrated Replicator controller/network behavior including Reese's direct command relationship and later human-form command of block Replicators.

Physical implementation:
- tangible `WNG_SovereignNeuralLattice` item;
- research requires Replicator study + Asuran fabrication;
- fabrication belongs only to `WNG_AsuranWorkshop`;
- uses real Replicator Core Fragment, `WNG_NaniteSludge`, plasteel and advanced components;
- native brain `Recipe_InstallImplant` surgery;
- native `Recipe_RemoveImplant` removal returns the physical item;
- removal releases the exact bearer's implant domain.

Authority boundary:
- bearer is **not Queen**;
- exact Queen cannot create an overlapping implant controller domain over innate Queen authority;
- authority type is exactly `NeuralLattice`, with exact bearer reference + unique domain key;
- real block faction transfer/prior faction restoration uses the same proven controller infrastructure;
- exact-target acquisition only; no Queen nearby-swarm seizure;
- current Def tuning: **24-cell acquisition range, normal cap 3 controlled bodies, 1,800-tick EMP signal disruption**;
- after acquisition the shared physical-presence validity is same map/same caravan; 24 cells is current acquisition range, not an ownership-breaking leash;
- EMP/containment interfere with both acquisition and commands;
- split/recombine preserves exact implant domain;
- genuine split may temporarily produce more same-domain bodies than the normal acquisition cap because controller identity is conserved;
- different Queen/implant domains remain isolated.

Candidate run **34580535936** found one real compile issue (protected Gizmo field access). It was corrected to public `Command.Disable(...)`.

Corrected validation run **34580647197**: C# build, all Def/Patch XML parsing and physical implant/research/fabrication/surgery/domain invariants SUCCESS. Temporary workflow removed before promotion. Live RimWorld testing pending.

Current implant graphic is a vanilla mechanics placeholder only; no generated replacement art was created and final dedicated art remains unfinished.

## Temporary Asuran lattice intrusion — NEXT / UNFINISHED

This must remain a third distinct authority model.

Required semantics:
- use `ReplicatorControlAuthority.TemporaryAsuran`;
- temporary hijack only, not Queen or implant acquisition;
- ordinary Asuran rank/physiology does not confer permanent sovereignty;
- preserve enough exact prior controller-domain state to restore Queen, Neural-Lattice or autonomous ownership correctly when the override ends;
- expiry/interruption must not erase pre-existing controller ownership;
- duration/range/cap/trigger behavior remains author-tunable;
- EMP/containment are real counterplay;
- hierarchy transactions during active override must preserve coherent temporary/restoration state without duplication/cross-domain leakage.

## If Asurans capture the Queen — CONSEQUENCE UNFINISHED

Do not model this as an arbitrary `+1 outbreak` or generic faction buff.

Intended consequence:
- suitable future Lattice/Asuran threats can gain **genuine sovereign block access** if the faction retains the exact captured Queen;
- use real controller/domain state and mixed physical Asuran + block threat composition;
- do not create duplicate/proxy Queen state.

## Infiltration / broader Neural Interface — UNFINISHED

Still required later:
- human-looking infiltrator behavior/reveal mechanics;
- recruit/imprison/enslave/copy/create-human-form Neural Interface operations where game rules permit;
- exact copied-person biography/name/skill/passions/appearance/genome continuity;
- real resource costs and no free duplication loop.

## Validation boundary

Static compile/XML/API checks are source sanity only. Live gameplay still needs testing for:
- Queen release/recovery/capture/save-load;
- Queen control/acquisition/commands/release;
- Neural Lattice fabrication/install/remove/save-load/control;
- EMP/containment interruption;
- split/recombine inheritance/domain isolation;
- later temporary override restoration.

## Pacing

Never restore old hard-coded day-84 Queen discovery. Vardath's games may be performance-bound by around day 20; major content needs tunable short-campaign accessibility.
