# WNG — Replicator Queen / Asuran recovery design

This is a working first-build design, not immutable canon. Vardath may alter any detail after testing.

## Current implementation checkpoint — 2026-09-11

Public mod implementation through:

**`f2b9c0b3c7ac6ac440dd80d715d44f47a0981973` — validated exact-Queen sovereignty build**

Implemented now:
- one exact persistent Queen pawn;
- real cryptosleep-vault release and immediate recruitment;
- first physical four-operative Asuran recovery/capture attempt;
- capture only when the exact Queen physically leaves in the exact recovery Jumper transit container;
- genuine exact-Queen controller-domain authority over real block Replicators;
- authority persistence through save/load and block split/recombine transactions;
- dedicated Queen-linked block commands;
- EMP/containment interference and physical-presence validity;
- controller-domain isolation across hierarchy, Controller coordination, Repairer support and retaliation.

Not yet implemented:
- Sovereign Neural Lattice implant bearer control;
- temporary Asuran lattice intrusion;
- later recurring Queen recovery attempts;
- captured-Queen hostile sovereign consequences/mixed Asuran + block threats;
- infiltration;
- live RimWorld validation/balance tuning of these systems.

## Queen identity

Current Queen:
- unique human-form Replicator individual;
- female;
- age 13 in the current first-build design;
- uses the human-form Replicator/nanite humanoid identity rather than a block-machine race;
- unique sovereign authority belongs to the exact Queen, not every human-form Replicator;
- one exact pawn/state persists through the storyline;
- while validly aligned/present, she has genuine sovereign control over appropriate block Replicators rather than a cosmetic or statistical bonus.

Ordinary Asuran Operative/Technician/Commander roles remain separate. Sharing `WNG_NaniteHumanoid` physiology does **not** confer Queen authority.

## Cryosleep release — IMPLEMENTED

The Queen is held in a real RimWorld `CryptosleepCasket` at the precursor-style vault/site.

**When the exact dormant Queen is physically released/spawned on the real vault map, she joins the player immediately.** There is no later neutral guest recruitment stage.

Release is guarded by exact global Queen state and vault-map identity so moving the pawn to another map later cannot replay recruitment or reset the recovery timer.

Her release triggers the hostile Asuran/Lattice recovery attempt.

## First recovery attempt — IMPLEMENTED FOUNDATION

Current flow:
1. player reaches vault;
2. Queen remains in the real casket until released;
3. release recruits the exact Queen immediately;
4. hostile recovery operation activates after a bounded tunable delay;
5. current design requires all four human-form Asuran recovery operatives to spawn successfully or the partial operation rolls back;
6. they prioritize the Queen rather than generic destruction;
7. dedicated subdue/load/hold jobs are nonlethal and do not damage-override into ordinary combat;
8. one operative stuns the exact Queen through RimWorld's real `StunHandler`;
9. that operative physically carries the real Queen to the physical Asuran recovery Jumper;
10. the exact pawn is transferred into that Jumper's native transporter;
11. surviving operatives physically board;
12. stun/down/carry/loading are **not** capture;
13. capture commits only at the real leaving-map boundary while that same exact Queen is still inside that same exact transit container;
14. successful departure stores the exact Queen in the Asuran faction's native kidnapped-pawn tracker and marks global Queen state `CapturedByAsurans`;
15. if departure cannot be proven, WNG refuses to silently consume/proxy the Queen.

Numbers/timing/arrival variation remain tunable. CatCraft Stargates may later provide an optional arrival variation but are not required for this storyline.

## Later recovery raids — UNFINISHED

If she remains with the player, hostile Asurans/Lattice may occasionally attempt to recover her again.

Rules remain:
- may target **any player map where the exact Queen is physically present**; not restricted to home maps;
- do not target another player map while she is physically elsewhere;
- do not fire while she is caravaning/off-map/dead/already captured;
- real raid/entry, not teleporting directly beside her;
- objective is Queen subdual/kidnap;
- physical carrier/map departure is required to commit capture;
- do not stack constant recovery raids; cadence must be tunable and tested.

## Exact Queen sovereignty — IMPLEMENTED FOUNDATION

The real Queen now has innate sovereign authority using the same actual block pawns already present in WNG.

Controller state is attached to each block through `CompReplicatorSovereignty`, not represented as an outbreak probability, aura, invisible ownership assumption or duplicate swarm.

Current Queen authority:
- targets exact living WNG block Replicators;
- stores the exact Queen as controller plus a save-persistent Queen domain key;
- records the block's pre-control faction;
- changes the exact block pawn to the Queen's real current faction;
- remains valid only while controller and block remain physically together on one map or in one caravan;
- releases/restores ownership if the authority becomes invalid;
- is blocked/interrupted by Queen EMP disruption, block EMP suppression and active WNG Replicator containment;
- gives controlled blocks dedicated sovereign move/attack commands plus Repairer/Burrower specialist commands where appropriate;
- permits explicit player-commanded upward recombination rather than silently restoring hostile automatic recombination;
- preserves the exact authority domain through real split/recombine transactions;
- does not merge the Queen's human-form Nanite Reserve with block Replicators' separate stored-matter economy.

Current first-build tuning is Def-driven:
- 40-cell direct acquisition range;
- 24-cell nearby-swarm acquisition radius;
- 12 controlled spawned block bodies on the Queen's map.

These are balance values for testing, not immutable doctrine.

Different controller domains are explicitly isolated: they cannot recombine, coordinate Controller focus, receive Repairer support or share retaliation merely because their current faction happens to match.

## Queen authority vs implant authority

Real Queen — IMPLEMENTED FOUNDATION:
- innate broader sovereign control of appropriate block Replicators when physically present/aligned;
- genuine exact controller/faction state;
- dedicated player commands;
- save/load and hierarchy continuity;
- EMP/containment remain real constraints.

Sovereign Neural Lattice implant bearer — **NEXT UNFINISHED CONTROL LAYER**:
- is not made into a Queen;
- gets bounded target-specific control;
- must reuse the live `NeuralLattice` controller-domain path in `CompReplicatorSovereignty` rather than create a second incompatible system;
- controller identity must persist through save/load and relevant split/recombine transactions while valid;
- different Queen/implant domains must never merge accidentally;
- should remain mechanically more bounded than the Queen, with tunable range/capacity/cost/cooldown as appropriate.

Temporary Asuran lattice intrusion — UNFINISHED AND SEPARATE:
- separate temporary override authority;
- uses its own explicit expiry/restoration semantics;
- not equivalent to Queen sovereignty;
- not equivalent to Sovereign Neural Lattice ownership.

## If Asurans capture the Queen — CONSEQUENCE UNFINISHED

Do not represent this as an arbitrary extra autonomous outbreak pawn.

The intended consequence remains real sovereign access: suitable future hostile Lattice/Asuran threat composition may include block Replicators acting under that faction's control because the captured Queen gives them genuine sovereign authority.

The new controller-domain implementation provides the technical ownership model for this future consequence; the actual captured-Queen threat composition is not yet implemented.

This should modify suitable existing/future threat compositions rather than necessarily creating a new arbitrary recurring raid timer.

## Validation boundary

Queen sovereignty was compiled and Def/XML/invariant checked in temporary GitHub Actions run **34576583840**, which succeeded. The temporary workflow was removed afterward.

This is not a claim of live RimWorld gameplay validation. Live tests still need to cover release, recovery, exact capture/save-load, Queen acquisition/release, commands, EMP/containment interruption, split/recombine inheritance and domain isolation.

## Pacing

Do not hard-code the old day-84 discovery. Vardath's games can become performance-bound around day 20. The Queen and other major content must be reachable in short campaigns through tunable discovery/story pacing.
