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

**`8495b846c7dd31c079db6d4f007be490df3247f3` — Neural Interface and exact human-form reconstruction landed on public `main`.**

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
- exact captured-Queen retention is verified against `GameComponent_ReplicatorQueenState`, exact Queen pawn and exact `WNG_AsuranLattice` native kidnapped-pawn tracker;
- captured remote Queen authority is valid only while that exact faction genuinely retains that exact Queen;
- real captured-Queen assignment uses genuine `ReplicatorControlAuthority.Queen`, exact Queen pawn reference and exact Queen domain key;
- only the narrow captured-retained-Queen case bypasses ordinary same-map Queen physical-presence validation;
- when exact retention ends, per-block authority becomes invalid and normal sovereignty release restores recorded pre-control/autonomous faction/domain;
- `GameComponent_CapturedQueenThreats` save-persistently schedules consequence strikes only while exact retention remains true;
- `WNG_CapturedQueenSovereignStrike` is scheduler-only and uses storyteller threat points with Def-tunable cadence/chance/count/composition;
- mixed strikes contain real Asuran pawns plus real WNG block Replicators generated as autonomous swarm first and then genuinely assigned to the exact captured Queen;
- real hostile `LordJob_AssaultColony` integration and partial-force rollback are present.

Validation:
- remote sovereignty run **34596238345** — SUCCESS;
- mixed threat run **34596657164** — SUCCESS.

### Neural Interface / exact human-form reconstruction

Public milestone: **`8495b846c7dd31c079db6d4f007be490df3247f3`**  
Status: **IMPLEMENTED FOUNDATION / LIVE-TEST NEEDED**.

Public contains:
- touch-range `WNG_NeuralInterface` ability on the existing nanite-humanoid physiology gene;
- use limited to player-controlled nanite humanoids after current Asuran fabrication research;
- biological-humanlike target filtering that excludes existing synthetic nanite humanoids/block Replicators;
- native `Pawn.SetFaction` recruitment rather than fake allegiance state;
- native prisoner guest status;
- Ideology-gated native slave guest status;
- direct skill/passion/XP-pattern copying;
- real separate `WNG_HumanFormReplicatorCopy` PawnKind for reconstructed persons;
- source pawn remains intact; reconstruction creates a distinct pawn;
- Def-tunable first-build 60% Nanite Reserve reconstruction cost;
- transactional reserve spending: no cost before viable placement and rollback/destroy if the final reserve commit fails;
- source name, gender, biological/chronological age, childhood/adulthood, title/birth surname, body/head/hair/skin appearance, traits, skills/passions/XP and source genome copied into the synthetic body;
- source xenogene/endogene distinction preserved using current RimWorld `Pawn_GeneTracker.Xenogenes` API;
- current WNG nanite identity layered after the source-person snapshot;
- no source deletion/recreation proxy semantics.

Validation:
- initial run **34597748048** failed only on obsolete historical `Gene.Xenogene` API use;
- corrected against current API;
- final run **34599563874** — SUCCESS;
- Release build passed with **0 warnings / 0 errors**;
- all **102** current Def/Patch XML files parsed;
- Neural Interface identity/cost/native-state invariants passed;
- temporary validator removed before the clean public promotion.

All validation in these public slices is source/Def validation, **not live RimWorld validation**.

---

# CURRENT ACTIVE BRANCH

No branch-only feature is currently authoritative after the Neural Interface promotion. Create the next bounded public-repo branch from current public `main` for the next subsystem.

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
- captured-Queen mixed Asuran/block consequence strikes;
- Neural Interface native recruit/imprison/Ideology-slave operations;
- skill/passion/XP extraction;
- real copy/create-human-form reconstruction with exact core identity/genome snapshot and transactional reserve cost.

Still required:
- real infiltration/impersonation/reveal;
- non-hostile Quiet Lattice;
- player human-form variants;
- broader role/faction composition beyond current hostile/copy foundations;
- native WNG backstories;
- complete synthetic disease/implant/temperature/vacuum physiology audit;
- optional broader DLC identity-copy fidelity audit;
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
- authority collapse/reversion if the exact Queen is no longer genuinely retained by the exact capturing Asuran faction;
- ordinary Neural Interface pawn-manipulation system remains separate from all Queen/block authority systems.

Still required:
- infiltration linkage and broader human-form society/story consequences;
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

Temporary Asuran intrusion, recurring exact-map Queen recovery, captured-Queen sovereign consequences and Neural Interface/exact core copy-reconstruction are removed from this debt list because they are now implemented on public `main`.

1. **Human-form infiltration/impersonation/reveal.**
2. Quiet Lattice non-hostile enclave, player human-form variants and broader human-form role/faction composition.
3. Native WNG backstories.
4. Richer block Grav adaptation and broader AntiShield integration.
5. Wraith Growth Chamber.
6. Strategic Wraith hunger involved-Wraith count/names UI stage.
7. Broader discovery/story progression.
8. Friendly Quiet-Lattice/Puddle-Jumper Stargate courier path.
9. Safe standalone Goa'uld craft/gravship material/fuel/research route when ONAC is absent.
10. Deliberate Ancient/Puddle-Jumper power/fuel abstraction.
11. Unloaded-world-site transport-ring exact-pawn/world-object transport; never fake via pawn recreation.
12. Faction-specific professional gravship corner/inside-corner/diagonal/transition presentation.
13. Final professional craft/gravship/implant/building/weapon/resource art review.
14. Professional WNG audio layer.
15. Hostile Ha'tak native takeoff/retreat/pursuit only if Odyssey ownership can be solved safely; never fake it.
16. Broad current-build live RimWorld/save-load/mod-stack/performance validation and tuning.
17. Optional broader DLC identity-copy fidelity audit for Neural Interface copies.
18. Approved planned-only Anomaly/Ideology/Iratus/diplomacy/pharmacology/Kassa/Royalty branches when Vardath advances them.

No item may silently disappear merely because another branch is worked first.

---

# GENUINE NEXT IMPLEMENTATION SLICE

**Human-form infiltration / impersonation / reveal foundation.**

Required boundary before implementation:
- use current public `WNG_NaniteHumanoid` and actual Asuran role/faction architecture;
- inspect historical/private infiltrator work only as behavior evidence, never as known-good code;
- hidden synthetic state must be attached to the exact pawn and survive save/load;
- concealment must affect what the player is told/shown about that pawn rather than merely setting flavor text;
- reveal must be a concrete persistent state change, not a temporary message;
- current intended reveal families are scanning, meaningful injury/damage exposure and suspicious synthetic behavior; implement only paths that can be tied to real current APIs/mechanics;
- revealed state must not change the pawn into a proxy/recreated pawn;
- exact faction/pawn identity must remain intact across conceal/reveal;
- Queen uniqueness and block sovereignty must not be inferred from ordinary infiltrator state;
- source/Def validation before promotion; live RimWorld validation remains separately required;
- checkpoint every bounded pass before moving on.
