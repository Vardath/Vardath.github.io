# WNG — CURRENT PUBLIC STATE

Updated: **2026-09-11**  
Author/final design authority: **Vardath**

This is the mutable live-state supplement to `CANONICAL_RECOVERY_LEDGER.md`, `PUBLIC_RECONCILIATION_2026-09-11.md` and the running short-pass log `PASS_CHECKPOINTS.md`.

**Current public source is implementation truth. Private/old work is reference evidence only. There are no known-good historical builds.**

## Mandatory recovery order

1. `STANDING_RULES.md`;
2. all of `CANONICAL_RECOVERY_LEDGER.md` for recovered history/design;
3. all of `PUBLIC_RECONCILIATION_2026-09-11.md`;
4. all of this file;
5. latest entries in `PASS_CHECKPOINTS.md`;
6. `WNG_IMPLEMENTATION_CHECKLIST.md`;
7. fetch current public `Vardath/Wraith-Nanite-Gravtech-1.6` `main` and compare it with the HEAD below;
8. inspect every newer commit before coding;
9. read active subsystem contracts/plan append(s);
10. follow `PLAN_EXECUTION_PROTOCOL.md`;
11. update `PASS_CHECKPOINTS.md` after every bounded pass and this live state whenever public/debt state changes materially.

---

# CURRENT PUBLIC MOD HEAD

Repository: `Vardath/Wraith-Nanite-Gravtech-1.6`

**`0b8150f3ff6ca7138482ba9a604847f5967fc48b` — captured Queen sovereign consequences and mixed Asuran/block threats landed on public `main`.**

The original canonical implementation snapshot `4af4f60...` is historical only and substantially behind current public source.

## Most recent completed public slices

### Temporary Asuran lattice intrusion

Public milestone: **`26680fe84b95a0bfd5a23841b714fdba9cde1a98`**  
Status: **IMPLEMENTED FOUNDATION / LIVE-TEST NEEDED**.

Public contains:
- `WNG_AsuranLatticeLink` on `WNG_NaniteHumanoid`;
- hostile automatic use restricted to exact hostile `WNG_AsuranLattice`;
- Def-tunable first-build range/duration/cap/check/chance;
- real `TemporaryAsuran` authority transaction;
- exact suspended authority/controller/faction/domain snapshot and restoration;
- split/recombine/save-load continuity;
- timeout, intruder death/downing, separation, EMP and containment interruption;
- no permanent Queen sovereignty for ordinary Asurans.

### Recurring exact-map Queen recovery

Public milestone: **`9ce713704505a220d357f8a6f234fb6e040e0b2e`**  
Status: **IMPLEMENTED FOUNDATION / LIVE-TEST NEEDED**.

Public contains:
- later recovery attempts after the initial vault recovery;
- only the exact player-home map physically containing the exact Queen can be targeted;
- no attack against a different colony while she is off-map/travelling/caravanning;
- real recovery Jumper, nonlethal subdual, physical loading and exact shuttle-departure capture boundary;
- Def-tunable 2–4 day current cadence, transient retry handling, one operation at a time and save-persistent scheduling;
- active recovery identity tied to the exact Jumper `CompShuttle.requiredPawns` list.

### Captured Queen sovereign consequences / mixed threat

Public milestone: **`0b8150f3ff6ca7138482ba9a604847f5967fc48b`**  
Status: **IMPLEMENTED FOUNDATION / LIVE-TEST NEEDED**.

Public contains:
- assimilation-born blocks inherit exact `CompReplicatorSovereignty` as well as learned state;
- exact captured-Queen retention is verified against `GameComponent_ReplicatorQueenState`, the exact Queen pawn and the exact `WNG_AsuranLattice` native `KidnappedPawnsTracker`;
- captured remote Queen authority is valid only while that exact faction genuinely retains that exact Queen;
- real captured-Queen assignment uses genuine `ReplicatorControlAuthority.Queen`, exact Queen pawn reference and exact Queen domain key;
- only the narrow captured-retained-Queen case bypasses ordinary same-map Queen physical-presence validation;
- remote blocks must actually belong to the exact captor faction;
- when exact retention ends, per-block authority becomes invalid and the normal sovereignty release path restores recorded pre-control/autonomous faction/domain;
- `GameComponent_CapturedQueenThreats` save-persistently schedules consequence strikes only while exact retention remains true;
- `WNG_CapturedQueenSovereignStrike` is scheduler-only (`baseChance=0`) and uses storyteller threat points with Def-tunable cadence/chance/count/composition;
- mixed strikes contain real Asuran Operative/Technician/Commander pawns plus real WNG block Replicators;
- each hostile block is generated first as autonomous `WNG_ReplicatorSwarm`, then genuinely assigned to the exact captured Queen, preserving autonomous `originalFaction` for later reversion;
- real Drone/Hunter plus optional specialist/heavy/Titan composition is used; first-build mixed pool deliberately excludes Siege Mass;
- one real `LordJob_AssaultColony` controls the mixed exact-captor force;
- active Queen-domain force detection prevents immediate stacking of another consequence force;
- partial spawn failure rolls the force back rather than leaving a fake half-event.

Validation for the captured-Queen branch:
- remote-sovereignty foundation run **34596238345** — passed C# build, Def/Patch XML and authority invariants;
- mixed-threat run **34596657164** — passed C# build, Def/Patch XML and mixed-threat invariants;
- temporary validation helpers were removed before promotion;
- the branch tree was promoted as one clean public commit, not with temporary validator history;
- all validation above is source/Def validation, **not live RimWorld validation**.

---

# CURRENT ACTIVE BRANCH

No branch-only feature is currently authoritative after the captured-Queen promotion. Create the next bounded public-repo branch from current public `main` for the next subsystem.

---

# CURRENT IMPLEMENTED FOUNDATIONS

## Block Replicators

Implemented foundation:
- `Drone -> Hunter -> Bulwark -> Titan -> Siege Mass` upward hierarchy and real downward destruction breakup;
- split-born recombination lockout;
- Controller, Repairer, Burrower and Artillery specialists;
- stored-matter assimilation/reproduction economy and bounded growth;
- dangerous Replicator Matter;
- EMP and powered containment;
- regeneration/local retaliation/terminal-consumption behavior;
- Child's Toy player branch;
- controller-domain-aware split/recombine/assimilation offspring state inheritance;
- Material/Armor/Ranged/Power/Shield adaptation foundations;
- AntiShield persistent state/current Replicator-shield interaction;
- Grav learned/save-persistent state + visual overlay.

Still partial:
- richer Grav mobility/physical behavior;
- broader AntiShield interaction with concrete non-Replicator shield systems.

## Controller domains

Implemented publicly:
- `None` autonomous;
- exact `Queen` authority;
- physical `NeuralLattice` implant authority;
- temporary restorable `TemporaryAsuran` intrusion;
- exact captured-retained-Queen remote `Queen` authority for genuine Asuran sovereign consequence forces.

Queen and implant remain separate exact controller identities. Temporary Asuran intrusion suspends/restores rather than erases. Captured remote Queen authority exists only while the exact Asuran Lattice native kidnapped-pawn tracker still retains the exact Queen.

## Human-form Replicators / Asurans

Implemented foundation:
- `WNG_NaniteHumanoid`;
- native Food machinery presented/used as Nanite Reserve;
- synthetic depletion instead of ordinary malnutrition;
- reserve-powered reconstruction/fabrication;
- EMP disruption;
- Asuran workshop/fabrication;
- hidden hostile `WNG_AsuranLattice`;
- Operative/Technician/Commander roles;
- temporary lattice intrusion;
- captured-Queen mixed Asuran/block consequence strikes.

Still required:
- broader Neural Interface recruit/imprison/Ideology-enslave/copy/create-human-form system;
- exact copy/reconstruction preserving biography/name/skills/passions/XP/appearance/genome source data;
- real infiltration/impersonation/reveal;
- non-hostile Quiet Lattice;
- player human-form variants;
- broader role/faction composition beyond the current hostile/captured-Queen strike foundation;
- native WNG backstories;
- complete synthetic disease/implant/temperature/vacuum physiology audit;
- final dedicated art/audio and live testing.

## Exact Replicator Queen

Implemented publicly:
- one exact persistent female human-form Queen, current age 13;
- real precursor cryptosleep vault;
- immediate player recruitment on release;
- first all-or-nothing four-operative nonlethal Asuran recovery operation;
- recurring later exact-map recovery operations;
- exact physical Asuran recovery Jumper;
- capture commits only when the exact Queen physically exits in the exact hostile shuttle transit container;
- exact kidnapped-pawn persistence;
- genuine exact Queen block-Replicator sovereignty;
- physical Sovereign Neural Lattice exists separately from Queen authority;
- Temporary Asuran intrusion exists separately from both;
- captured-Queen remote sovereign consequence authority;
- save-persistent mixed Asuran + genuine Queen-domain block threat consequences;
- authority collapse/reversion if the exact Queen is no longer genuinely retained by the exact capturing Asuran faction.

Still required:
- infiltration/Neural-Interface linkage and broader human-form society/story consequences;
- live RimWorld validation.

## Wraith

Implemented foundation:
- one Wraith xenotype with Hunter/Warrior/Commander/Keeper/Queen castes;
- pale/white hair enforcement;
- Life Force, full Drain Life, Partial Feed, regeneration, hibernation/torpor;
- Sable Brood, Cinder Court, Veiled Hive, Pale Covenant;
- strategic faction hunger separated from ordinary feeding;
- exact captivity/rescue;
- Feeding Niche, Hibernation Pod, Dormancy Vault, Hive Heart;
- mature-Hive population/feeding-stock/retaliation foundation;
- living-tech bootstrap and real Wraith Grav Engine path;
- Wraith stun staff;
- Wraith Dart culling/captivity foundation;
- Wraith gravship mechanics and living-hull regeneration defense.

Still required:
- Wraith Growth Chamber;
- strategic hunger later UI stage showing involved-Wraith count/names;
- broader discovery/story progression;
- final presentation/audio/live testing.

Ordinary Wraith feeding, strategic faction hunger, mature-Hive local feeding ecology and mature-Hive retaliation remain four separate systems.

## Craft / Stargate integration

Mechanical foundations present:
- Wraith Dart;
- Wraith Strike/scout craft;
- Wraith Cruiser;
- Puddle Jumper;
- **Al'kesh**;
- Death Glider;
- Asuran recovery Jumper;
- Goa'uld transport rings;
- CatCraft/ONAC/RimGate ownership boundaries and verified package identities.

Still required/partial:
- friendly Quiet-Lattice/Puddle-Jumper Stargate courier path;
- deliberate Ancient/Puddle-Jumper power/fuel abstraction instead of temporary chemfuel;
- unloaded-world-site ring transport remains a later exact-world-object problem and must never use pawn recreation/proxies;
- broad live boarding/loading/fuel/launch/world/save-load validation;
- final distinct art/audio.

## Gravships / Goa'uld

Wraith and Asuran Odyssey-native mechanical gravship families are implemented with family-isolated fuel networks/pipes and appropriate parts. Wraith defense currently uses biological living-hull regeneration; the generic Wraith energy-shield reskin was rejected. Asuran uses a true powered native shield emitter.

Goa'uld/Ha'tak public foundation includes:
- Odyssey-native Ha'tak family;
- pel'tac/control, engine/hull/substructure, power/fuel network;
- heavy plasma battery;
- real two-seat Death Glider;
- verified System-Lord/Jaffa strikes;
- landed Ha'tak carrier site;
- real player cross-map/orbital bombardment.

Still required/blocked:
- safe standalone Goa'uld craft/gravship material/fuel/research route without ONAC — do not invent uranium/chemfuel fallback;
- hostile native Ha'tak takeoff/retreat/pursuit remains blocked by Odyssey's player-oriented gravship singleton and must not be faked;
- faction-specific professional hull corner/inside-corner/diagonal/transition presentation;
- final art/audio/live gravship testing.

---

# CURRENT REQUIRED UNFINISHED INVENTORY

Temporary Asuran intrusion, recurring exact-map Queen recovery and captured-Queen sovereign mixed-threat consequences are removed from this debt list because they are now implemented on public `main`.

1. **Human-form Neural Interface recruit/imprison/enslave/copy/create-human-form branch.**
2. Human-form infiltration/impersonation/reveal.
3. Quiet Lattice non-hostile enclave, player human-form variants and broader human-form role/faction composition.
4. Native WNG backstories.
5. Richer block Grav adaptation and broader AntiShield integration.
6. Wraith Growth Chamber.
7. Strategic Wraith hunger involved-Wraith count/names UI stage.
8. Broader discovery/story progression.
9. Friendly Quiet-Lattice/Puddle-Jumper Stargate courier path.
10. Safe standalone Goa'uld craft/gravship material/fuel/research route when ONAC is absent.
11. Deliberate Ancient/Puddle-Jumper power/fuel abstraction.
12. Unloaded-world-site transport-ring exact-pawn/world-object transport; never fake via pawn recreation.
13. Faction-specific professional gravship corner/inside-corner/diagonal/transition presentation.
14. Final professional craft/gravship/implant/building/weapon/resource art review.
15. Professional WNG audio layer.
16. Hostile Ha'tak native takeoff/retreat/pursuit only if Odyssey ownership can be solved safely; never fake it.
17. Broad current-build live RimWorld/save-load/mod-stack/performance validation and tuning.
18. Approved planned-only Anomaly/Ideology/Iratus/diplomacy/pharmacology/Kassa/Royalty branches when Vardath advances them.

No item may silently disappear merely because another branch is worked first.

---

# GENUINE NEXT IMPLEMENTATION SLICE

**Human-form Neural Interface / exact copy-reconstruction foundation.**

Required boundary before implementation:
- use current public human-form Asuran/Nanite Reserve architecture rather than restoring an old private implementation wholesale;
- use private/reference Neural Interface code only as requirement/behavior evidence after current public mechanics are checked;
- preserve exact source pawn identity data required by the plan: name/biography/backstories, skills/passions/XP, appearance and genome/xenotype data where native APIs permit exact copying;
- recruit/imprison/Ideology-enslave operations must use native RimWorld faction/guest/slavery mechanics rather than fake flags;
- copy/create-human-form operations must create a genuine new pawn while leaving the exact source pawn intact;
- resource spending/rollback must be transactional so a failed operation does not consume the required nanite/resource cost;
- Queen, Neural Lattice, Temporary Asuran and captured-Queen block-control systems remain distinct from ordinary Neural Interface pawn manipulation;
- implementation must be broken into bounded coherent passes and checkpointed in `PASS_CHECKPOINTS.md` before each next pass;
- source/Def validation before promotion; live RimWorld validation remains separately required.
