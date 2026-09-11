# WNG — CURRENT PUBLIC STATE

Updated: **2026-09-11**  
Author/final design authority: **Vardath**

# PURPOSE

This is the mutable live-state supplement to `CANONICAL_RECOVERY_LEDGER.md`.

The completed public-vs-plan/private reconciliation is:

**`PUBLIC_RECONCILIATION_2026-09-11.md`**

Read that file in full before using an older checkpoint, feature map, primer or private branch to decide what exists.

The canonical ledger preserves the one-time historical reconstruction, but its original implementation snapshot is now historical. Current public source and this live state supersede stale “missing/current/next” claims inside older snapshots.

Mandatory recovery order:
1. `STANDING_RULES.md`;
2. all of `CANONICAL_RECOVERY_LEDGER.md` for recovered design/history;
3. all of `PUBLIC_RECONCILIATION_2026-09-11.md`;
4. all of this file;
5. `WNG_IMPLEMENTATION_CHECKLIST.md`;
6. fetch current public mod `main` and compare it with the HEAD below;
7. inspect newer commits before coding;
8. active subsystem contracts/plan appends;
9. `PLAN_EXECUTION_PROTOCOL.md`;
10. update current state/reconciliation before handoff.

**Current public `main` always beats stale checkpoint/"next" prose. Private work is reference evidence only.**

---

# CURRENT MOD HEAD

Repository: `Vardath/Wraith-Nanite-Gravtech-1.6`

**`0e5dfc893a8efec624053e677ae99d6983c25fc9` — `cleanup: remove temporary Neural Lattice validation workflow`**

The canonical ledger's original `4af4f60...` implementation snapshot is **45 public commits behind** this HEAD. Those commits added major human-form/Queen/sovereignty/Neural-Lattice and Goa'uld/Ha'tak implementation layers.

The continuity-repo reconciliation commit is:

**`c2d55c55aa34b3233f56abf8e7c7bed9a35f5bbc` — `wng: add authoritative public reconciliation ledger`**

---

# GLOBAL CONTENT / OWNERSHIP RULES

WNG requires the complete current RimWorld DLC set:
- Royalty;
- Ideology;
- Biotech;
- Anomaly;
- Odyssey.

Use a DLC system only where it actually models the Stargate/WNG function; the dependency does not require checkbox content.

Third-party Stargate ecosystem mods remain optional unless Vardath changes this:
- CatCraft Stargates! — owns gate network/address/dial/iris/receive-buffer mechanics;
- ONAC — owns its Goa'uld resources/systems including `ONAC_LiquidNaquadria` and tretonin/tritonin content;
- RimGate Jaffa Biotech — owns its Jaffa/System-Lord identities.

Do not duplicate externally owned factions/resources. Do not invent uranium/chemfuel or another unspecified Goa'uld fallback. **Al'kesh exists and stays.**

---

# CURRENT IMPLEMENTATION — CORRECTED STATUS

## Block Replicators — IMPLEMENTED FOUNDATION / REFINEMENTS REMAIN

Implemented:
- physical `Drone -> Hunter -> Bulwark -> Titan -> Siege Mass` hierarchy and real downward destruction breakup;
- split-born recombination lockout;
- Controller, Repairer, Burrower and Artillery specialists;
- assimilation/stored-matter reproduction economy and population bounds;
- dangerous Replicator Matter;
- EMP suppression and powered containment;
- regeneration and local retaliation/terminal-consumption behavior;
- Child's Toy player branch;
- controller-domain-aware hierarchy/state inheritance.

Adaptations:
- Material, Armor, Ranged, Power and Shield foundations are implemented;
- AntiShield has persistent evidence/state and current Replicator adaptive-shield interaction, but broader non-Replicator shield integration remains later;
- **Grav is currently learned/save-persistent state + visual overlay only; richer grav/mobility behavior remains unfinished.**

Block Replicators do **not** use human-form Nanite Reserve. Their stored matter is separate.

## Controller-domain architecture — IMPLEMENTED FOUNDATION

Every real block body carries `CompReplicatorSovereignty` and distinguishes:
- `None` — autonomous;
- `Queen` — exact Queen innate authority;
- `NeuralLattice` — physical implant bearer;
- `TemporaryAsuran` — **reserved only; implementation unfinished**.

Queen and Neural-Lattice control use real exact controller references, faction transfer, domain identity, save persistence, dedicated commands, split/recombine inheritance and EMP/containment interference.

### Exact Queen sovereignty — IMPLEMENTED

Implemented:
- exact persistent Queen authority only;
- same-map/same-caravan physical validity;
- exact-target plus bounded local-swarm acquisition;
- current first-build tuning 40-cell direct / 24-cell local swarm / normal cap 12;
- real controlled-block faction/domain behavior;
- existing-save Queen authority maintenance;
- EMP/containment interference.

Static validation succeeded during implementation. Live RimWorld validation remains pending.

### Sovereign Neural Lattice — IMPLEMENTED

Implemented:
- physical `WNG_SovereignNeuralLattice` item;
- research and Asuran-workshop fabrication;
- native brain install/remove surgery;
- exact non-Queen `NeuralLattice` controller identity;
- current tuning 24-cell target acquisition / normal cap 3 / 1,800-tick EMP disruption;
- no Queen-style local-swarm seizure;
- domain persistence through split/recombine;
- removal releases that bearer's controller domain.

The exact Queen does not become a second implant-controller domain.

Current item presentation is still a mechanics placeholder. Live validation remains pending.

### Temporary Asuran lattice intrusion — MISSING REQUIRED

Public has the enum/reserved authority identity, not the real mechanic.

Required implementation must:
- be temporary only;
- snapshot the exact previous authority/controller/domain/faction;
- restore Queen, Neural-Lattice or autonomous state correctly on expiry/interruption;
- survive real hierarchy transactions coherently;
- keep EMP/containment effective;
- never grant ordinary Asurans permanent Queen sovereignty.

Current generic `temporaryUntil -> ReleaseAuthority()` behavior is not sufficient for that required restoration model.

---

# HUMAN-FORM REPLICATORS / ASURANS — PARTIAL

Implemented:
- `WNG_NaniteHumanoid` xenotype;
- human-form nanite physiology;
- native food/eating behavior repurposed as visible **Nanite Reserve**;
- ordinary operation drains reserve, while repair/fabrication spend additional reserve;
- synthetic depletion behavior instead of biological malnutrition;
- EMP disruption;
- Asuran workshop/fabrication;
- hidden hostile `WNG_AsuranLattice`;
- Operative/Technician/Commander current roles.

**Missing required current-plan branches:**
- broader Neural Interface recruit/imprison/Ideology-enslave/copy/create-human-form system;
- exact copy/reconstruction preserving required biography/name/skills/passions/XP/appearance/genome source data;
- real infiltration/impersonation/reveal mechanics;
- non-hostile **Quiet Lattice** enclave;
- player human-form variants;
- broader role/faction composition and mixed human-form/block raids;
- native WNG backstories — current public has **no `Defs/BackstoryDefs` directory**;
- full synthetic disease/implant/temperature/vacuum physiology audit;
- final dedicated art/audio and live testing.

Historical/private implementations of Neural Interface, Quiet Lattice and backstories are reference evidence only and were **not** successfully migrated to current public.

---

# EXACT QUEEN / RECOVERY — PARTIAL

Implemented:
- one exact persistent female human-form Queen, current age 13;
- real precursor-style cryptosleep vault;
- immediate player recruitment on release;
- first all-or-nothing four-operative nonlethal Asuran recovery operation;
- exact physical recovery Jumper;
- capture commits only when the exact Queen physically exits inside that exact shuttle transit container;
- exact kidnapped-pawn persistence;
- exact Queen sovereign controller domain.

Still missing:
- **recurring later recovery/capture operations** on whichever player map physically contains the exact Queen;
- consequences if Asurans retain/recruit the captured Queen;
- genuine captured-Queen-backed Asuran sovereign block access in suitable future threats;
- mixed Asuran + block threat composition;
- infiltration linkage.

The current state latches the first recovery with `initialRecoverySpawned`; it is not a recurring recovery scheduler.

---

# WRAITH — STRONG FOUNDATION, NOT COMPLETE

Implemented:
- one Wraith xenotype with Hunter/Warrior/Commander/Keeper/Queen castes;
- enforced pale/white Wraith hair handling;
- Life Force, full Drain Life, Partial Feed, regeneration and hibernation/torpor;
- Sable Brood, Cinder Court, Veiled Hive and Pale Covenant;
- strategic faction hunger/request/raid-pressure mechanics separated from ordinary feeding;
- exact-pawn captivity/rescue;
- Feeding Niche;
- Hibernation Pod;
- Dormancy Vault;
- Hive Heart;
- mature-Hive population/feeding-stock/retaliation foundation;
- living-tech bootstrap and real Wraith Grav Engine path;
- ranged nonlethal Wraith stun staff;
- Wraith Dart culling/captivity foundation;
- Wraith gravship mechanical family and living-hull regeneration defense.

Still incomplete:
- **Growth Chamber**, explicitly named in rebuild step 7, is not found on current public;
- strategic hunger UI does not implement the planned later stage showing involved-Wraith count/names after the subject-selection flow;
- broader discovery/story progression is partial;
- professional presentation/audio and broad live testing remain unfinished.

Critical separation remains mandatory: ordinary Drain Life, strategic faction hunger, mature-Hive local feeding ecology and mature-Hive retaliation are four distinct systems.

---

# CRAFT / STARGATE INTEGRATION — MECHANICAL FOUNDATION IMPLEMENTED, PRESENTATION PARTIAL

Public native/Odyssey craft stack includes:
- Wraith Dart;
- Wraith scout/Strike Craft;
- Wraith Cruiser;
- Puddle Jumper;
- Al'kesh;
- Death Glider;
- Asuran recovery Jumper where applicable.

The principal craft use real native passenger-shuttle mechanics rather than the failed old static/raid-only model. Therefore old private boarding work is reference only; do not overwrite current architecture just because similar private work existed.

Unfinished:
- several craft still use vanilla shuttle graphics as mechanics placeholders;
- Puddle Jumper still explicitly uses **chemfuel as a temporary placeholder** pending deliberate Ancient power/fuel abstraction;
- friendly **Quiet Lattice / Puddle Jumper courier** Stargate delegation path is absent;
- broad live board/load/fuel/launch/world/save-load testing remains needed.

CatCraft package/ownership detection exists, and the Wraith Dart has an optional Stargate-aware escape decision path. CatCraft still owns the gate network/dial/iris/receive buffer.

---

# WRAITH / ASURAN GRAVSHIPS — MECHANICAL FOUNDATION IMPLEMENTED, PRESENTATION PARTIAL

Both families use Odyssey's real native GravEngine/hull/substructure behavior with family isolation and real WNG physical fuel-pipe connectivity.

## Wraith

Implemented mechanical roles include:
- real native engine/hull/substructure;
- pilot/control interface;
- small/large bio-sludge tanks;
- small/large thrusters;
- field organ/extender;
- transport/signal jammer;
- propulsion coordinator/fuel-savings analogue;
- living-hull regeneration;
- native power conduits;
- family-specific visible/hidden fuel pipes.

**Design correction:** generic Wraith gravship energy-shield reskin was rejected. Biological living-hull regeneration is the current defensive analogue. Do not call the missing Wraith shield Def a bug.

## Asuran

Implemented mechanical roles include:
- native engine/hull/substructure;
- control interface;
- nanite-sludge tanks;
- thrusters;
- field extender;
- signal jammer;
- fuel optimizer;
- true powered native Odyssey gravship shield emitter;
- Asuran power cell;
- orbital/vacuum support;
- native power conduits;
- family-specific fuel pipes.

## Unfinished gravship presentation

Current public does **not** contain the old/private themed hull section-layer renderer for Wraith/Asuran native corner/inside-corner/diagonal/transition art. Native Odyssey hull geometry works mechanically, but faction-specific professional topology presentation did not migrate.

Final part/conduit/hull art and broad live construction/fuel/power/launch/save-load testing remain unfinished.

---

# GOA'ULD / HA'TAK — IMPLEMENTED FOUNDATION, SPECIFIC BLOCKERS REMAIN

The old canonical-ledger statement that Ha'tak was absent is superseded.

Implemented publicly:
- Goa'uld Odyssey-native gravship family;
- pel'tac/control, engine/hull/substructure, power/fuel network;
- heavy plasma battery;
- real two-seat Death Glider;
- verified System-Lord/Jaffa hostile Death Glider strikes;
- landed Ha'tak carrier site with real gravship structure, defenders and parked Gliders;
- true player cross-map/orbital bombardment into a distinct Surface map using native bombardment behavior.

Still unfinished/blocked:
- current Ha'tak/ship content remains ONAC-gated because Vardath has not defined a safe standalone Goa'uld ship resource/fuel/research route;
- **do not invent uranium/chemfuel or another substitute**;
- hostile native Ha'tak takeoff/retreat/pursuit remains blocked by Odyssey's player-oriented `Current.Game.Gravship` singleton and must not be faked by deleting/recreating/proxying the ship;
- final professional art/audio and broad live validation remain unfinished.

Goa'uld transport rings are implemented as WNG-owned transport technology with current standalone architect routing; final authentic visuals/audio remain presentation debt.

---

# DISCOVERY / RESEARCH — PARTIAL

Current public has real research/progression for Replicators, Asuran fabrication, Sovereign Neural Lattice, Wraith bootstrap/shuttles and Goa'uld transport/gravships, plus real sites/incidents for several implemented systems.

The complete intended `mystery -> encounter -> evidence -> understanding -> reconstruction -> mastery` story layer remains partial. Historical ruined-lab/vault/facility concepts are reference ideas rather than immutable exact site names, but broader encounter-driven discovery is not yet a completed mod-wide progression system.

---

# PROFESSIONAL ART / AUDIO — INCOMPLETE

Approved block Replicator graphics are preserved.

The whole-mod professional presentation contract is not complete:
- several craft/gravship/item graphics remain vanilla mechanics placeholders;
- dedicated Neural Lattice art remains unfinished;
- faction-specific native hull corner/diagonal topology presentation is absent;
- full purpose-specific art review across buildings/weapons/abilities/resources/craft remains unfinished;
- no complete professional WNG audio/SoundDef library is present as a finished current-public system.

Do not generate replacement art unless Vardath explicitly asks.

---

# APPROVED PLANNED CONTENT — DELIBERATELY NOT CURRENT IMPLEMENTATION

Do **not** misclassify the 2026-09-11 planning append branches as failed migration work.

The Anomaly/Ideology append explicitly says planned-only/do not implement yet. The Iratus/diplomacy/pharmacology/Royalty append likewise records planned future content rather than a current required Ha'tak implementation slice.

Tracked future design includes, among other things:
- Wraith/Iratus xenobiology and containment/study;
- Whispers-style hybrid/fog encounters;
- advanced hybrids/Bug People/unstable transformations;
- real Iratus ecology/attachment/queens;
- Wraith client states/worshippers/tributaries;
- Ideology precepts/rituals/roles;
- Wraith/Iratus pharmacology;
- Kassa;
- Reol/Hoffan/related biological branches;
- suitable Royalty integration.

These remain planned until Vardath moves or changes them.

---

# COMPLETE CURRENT REQUIRED UNFINISHED INVENTORY

This is the authoritative compact debt list derived from `PUBLIC_RECONCILIATION_2026-09-11.md`:

1. Temporary Asuran lattice intrusion with exact prior-domain restoration.
2. Recurring exact-map Queen recovery/capture raids.
3. Captured-Queen sovereign consequences + mixed Asuran/block threats.
4. Human-form Neural Interface recruit/imprison/enslave/copy/create-human-form branch.
5. Human-form infiltration/impersonation/reveal.
6. Quiet Lattice non-hostile enclave, player human-form variants and broader human-form role/faction composition.
7. Native WNG backstories.
8. Richer block Grav adaptation and broader AntiShield integration.
9. Wraith Growth Chamber.
10. Strategic Wraith hunger involved-Wraith count/names UI stage.
11. Broader discovery/story progression.
12. Friendly Quiet-Lattice/Puddle-Jumper Stargate courier path.
13. Safe standalone Goa'uld craft/gravship material/fuel/research route when ONAC is absent.
14. Deliberate Ancient/Puddle-Jumper power/fuel abstraction.
15. Faction-specific professional gravship corner/inside-corner/diagonal/transition presentation.
16. Final professional craft/gravship/implant/building/weapon/resource art review.
17. Professional WNG audio layer.
18. Hostile Ha'tak native takeoff/retreat/pursuit only if Odyssey singleton ownership can be solved safely; never fake it.
19. Broad current-build live RimWorld/save-load/mod-stack/performance validation and tuning.
20. Approved planned-only Anomaly/Ideology/Iratus/diplomacy/pharmacology/Kassa/Royalty branches when Vardath advances them.

No item may silently disappear merely because another branch is being worked first.

---

# CURRENT NEXT IMPLEMENTATION INTERPRETATION

Temporary Asuran intrusion remains a valid immediate controller slice because the shared sovereignty architecture already exists.

But it is **not the entire unfinished project**. After any implementation batch, select the next work from the authoritative debt inventory above plus actual current public `main` and Vardath's newest instruction.

Do not treat a single checkpoint's “next” line as proof everything else is complete.

---

# VALIDATION BOUNDARY

Static/API/CI checks establish source/Def sanity only. **Broad live RimWorld validation of the current public build has not been completed in this environment unless explicitly supported by actual game/log evidence.**

Never report static validation as live-game validation.
