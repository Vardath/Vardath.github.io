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

**`9ce713704505a220d357f8a6f234fb6e040e0b2e` — recurring exact-map Queen recovery landed on public `main`.**

The original canonical implementation snapshot `4af4f60...` is historical only and substantially behind current public source.

## Most recent completed public slices

### Temporary Asuran lattice intrusion

Public milestone:

**`26680fe84b95a0bfd5a23841b714fdba9cde1a98`**

Status: **IMPLEMENTED FOUNDATION / LIVE-TEST NEEDED**.

Public contains:
- `WNG_AsuranLatticeLink` on `WNG_NaniteHumanoid`;
- hostile automatic use restricted to the exact hostile `WNG_AsuranLattice` faction;
- Def-tunable current first-build range 18, duration 2,500 ticks, cap 3, 600-tick AI check and 0.65 attempt chance;
- `TemporaryAsuran` authority as a real temporary controller transaction;
- exact pre-intrusion authority/controller/original faction/control faction/domain snapshot;
- active temporary domain keyed by exact intruder and exact restoration identity;
- no merge of blocks from different suspended domains merely because one Asuran hacked them;
- split/recombine/save-load continuity for active and suspended authority;
- timeout, intruder death/downing, physical separation, EMP and containment interruption;
- restoration of exact suspended Queen/Neural-Lattice/autonomous state when still valid;
- ordinary/recruited/player nanite humanoids do not silently auto-hijack blocks;
- ordinary Asurans do not receive permanent Queen sovereignty.

Validation:
- C# build passed;
- current Def/Patch XML parsed successfully;
- temporary validation workflow removed before public promotion;
- source/Def validation only, not live RimWorld validation.

### Recurring exact-map Queen recovery

Public milestone:

**`9ce713704505a220d357f8a6f234fb6e040e0b2e`**

Status: **IMPLEMENTED FOUNDATION / LIVE-TEST NEEDED**.

Public contains:
- later recovery attempts after the initial vault-triggered recovery;
- exact target is only the player-home map on which the exact Queen is physically spawned;
- no recovery attack against another player map while she is traveling, caravanning or off-map;
- existing physical Asuran recovery Jumper, exact nonlethal subdual, physical loading and native departure/capture transaction are reused;
- current first-build cadence is Def-tunable at 2–4 in-game days;
- transient edge/spawn failure retries rather than consuming the attempt forever;
- one real Queen recovery operation at a time;
- exact recovery operatives are read from the recovery Jumper's native `CompShuttle.requiredPawns`, preventing unrelated Asurans from keeping an old recovery attempt flagged active;
- recurring scheduler state is save-persistent.

Validation:
- C# build passed;
- Def/Patch XML parse passed after exact-operative refinement;
- temporary validation workflow removed before promotion;
- source/Def validation only, not live RimWorld validation.

---

# CURRENT ACTIVE BRANCH — NOT PUBLIC YET

Branch:

**`rebuild/captured-queen-sovereign-threats-20260911`**

Current branch HEAD at this state write:

**`af77e358a411f25e7c2ab88dfeb8a76e4b2bff03`**

Branch-only work currently includes:
- assimilation-born block Replicators now inherit the parent's exact `CompReplicatorSovereignty` state in addition to learned Replicator/adaptation state.

This branch is **not** public `main` yet and must not be reported as completed public functionality until validated and promoted.

The current captured-Queen design boundary is recorded in `PASS_CHECKPOINTS.md`.

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
- controller-domain-aware split/recombine/state inheritance;
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
- temporary restorable `TemporaryAsuran` intrusion.

Queen and implant remain separate exact controller identities. Temporary Asuran intrusion suspends/restores them rather than erasing them.

Captured-Queen remote sovereign use is the active branch and is not yet public.

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
- temporary lattice intrusion.

Still required:
- broader Neural Interface recruit/imprison/Ideology-enslave/copy/create-human-form system;
- exact copy/reconstruction preserving biography/name/skills/passions/XP/appearance/genome source data;
- real infiltration/impersonation/reveal;
- non-hostile Quiet Lattice;
- player human-form variants;
- broader role/faction composition and mixed human-form/block threats;
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
- Temporary Asuran intrusion exists separately from both.

Still required:
- captured-Queen consequences;
- genuine Asuran sovereign block access/mixed Asuran + block threats after successful capture;
- authority collapse/reversion if the exact Queen is no longer genuinely retained by the capturing Asuran faction;
- infiltration linkage.

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

Temporary Asuran intrusion and recurring exact-map Queen recovery are removed from this debt list because they are now implemented on public `main`.

1. **Captured-Queen sovereign consequences + mixed Asuran/block threats.**
2. Human-form Neural Interface recruit/imprison/enslave/copy/create-human-form branch.
3. Human-form infiltration/impersonation/reveal.
4. Quiet Lattice non-hostile enclave, player human-form variants and broader human-form role/faction composition.
5. Native WNG backstories.
6. Richer block Grav adaptation and broader AntiShield integration.
7. Wraith Growth Chamber.
8. Strategic Wraith hunger involved-Wraith count/names UI stage.
9. Broader discovery/story progression.
10. Friendly Quiet-Lattice/Puddle-Jumper Stargate courier path.
11. Safe standalone Goa'uld craft/gravship material/fuel/research route when ONAC is absent.
12. Deliberate Ancient/Puddle-Jumper power/fuel abstraction.
13. Unloaded-world-site transport-ring exact-pawn/world-object transport; never fake via pawn recreation.
14. Faction-specific professional gravship corner/inside-corner/diagonal/transition presentation.
15. Final professional craft/gravship/implant/building/weapon/resource art review.
16. Professional WNG audio layer.
17. Hostile Ha'tak native takeoff/retreat/pursuit only if Odyssey ownership can be solved safely; never fake it.
18. Broad current-build live RimWorld/save-load/mod-stack/performance validation and tuning.
19. Approved planned-only Anomaly/Ideology/Iratus/diplomacy/pharmacology/Kassa/Royalty branches when Vardath advances them.

No item may silently disappear merely because another branch is worked first.

---

# GENUINE NEXT IMPLEMENTATION SLICE

**Captured-Queen sovereign consequences + mixed Asuran/block threats.**

Required boundary:
- exact kidnapped Queen remains the genuine controller identity; do not create a proxy Queen or abstract faction bonus;
- the exact capturing Asuran faction must genuinely retain that exact Queen in its native kidnapped-pawn tracker for captured-Lattice Queen authority to remain valid;
- if that exact faction no longer retains that exact Queen, captured-Queen remote authority must become invalid and blocks must fall back through recorded release/faction state;
- real Asuran-backed blocks must carry exact `Queen` authority/domain metadata tied to the exact Queen;
- mixed threats must contain real spawned Asuran pawns and real block Replicators using normal Replicator specialist/combat/domain behavior;
- assimilation offspring, split/recombine and save/load must retain the exact controller domain correctly;
- no outbreak-count modifier or decorative faction bonus as a substitute;
- source/Def validation before promotion, with live RimWorld validation still separately required.

Work this as bounded meaningful passes, and checkpoint each pass in `PASS_CHECKPOINTS.md` before beginning the next one.
