# WNG — PUBLIC / PLAN / HISTORICAL RECONCILIATION

Date: **2026-09-11**  
Author/final design authority: **Vardath**

# PURPOSE

This document records the completed reconciliation requested after work was mistakenly reasoned about as though private/reference work had landed when it had not.

It answers one question only:

> **What is actually present on current public WNG `main`, what exists only as historical/private reference evidence, what is genuinely unfinished under the current plan, and what is deliberately planned-only?**

This file is current-state authority for that reconciliation. It does not turn historical code into a known-good state and it does not authorize wholesale copying from the private repository.

Mandatory authority order remains:

1. newest explicit Vardath instruction;
2. current public `Vardath/Wraith-Nanite-Gravtech-1.6` source/Defs/assets;
3. this reconciliation plus `CURRENT_PUBLIC_STATE.md`;
4. `CANONICAL_RECOVERY_LEDGER.md` for recovered design/history;
5. `MASTER_PLAN.md`, corrections and active subsystem contracts;
6. historical/private source only as requirement/reference evidence.

There are **no known-good historical WNG builds**.

---

# 1. HARD PUBLIC BASELINE

Active implementation repository:

`Vardath/Wraith-Nanite-Gravtech-1.6`

Verified public `main` at reconciliation:

**`0e5dfc893a8efec624053e677ae99d6983c25fc9` — `cleanup: remove temporary Neural Lattice validation workflow`**

The original canonical-ledger implementation snapshot:

**`4af4f60c184f1971ee7bc7516b63e3b33142fea0`**

is **45 public commits behind** `0e5dfc8...`.

Those 45 commits materially changed the implementation. They added, among other things:
- human-form Asuran/Nanite-Reserve physiology and faction foundation;
- exact Replicator Queen vault/release/recovery state;
- physical Asuran recovery Jumper and exact capture boundary;
- exact Queen sovereign block-Replicator control;
- physical Sovereign Neural Lattice item/research/surgery/control;
- Goa'uld/Ha'tak native gravship family;
- Death Glider mission/strike layer;
- landed Ha'tak carrier site;
- real player cross-map/orbital Ha'tak bombardment.

Therefore every old statement that those features are absent is superseded by actual public source.

---

# 2. STATUS DEFINITIONS

Every plan item is classified as one of:

- **IMPLEMENTED FOUNDATION** — real current public source/Defs exist for the intended mechanic; live testing or later refinement may remain.
- **PARTIAL** — a meaningful real implementation exists, but one or more required branches from the current plan are absent or intentionally unfinished.
- **MISSING REQUIRED** — current plan requires it and current public source/Defs do not implement it.
- **CHANGED / REJECTED** — Vardath/current design deliberately replaced or rejected the older planned form; absence is not a missing feature.
- **PLANNED ONLY / DEFERRED** — deliberately recorded future content whose plan says not to implement it yet.
- **LIVE-TEST NEEDED** — static source/compile/XML evidence exists, but actual RimWorld behavior has not been established in this environment.

A historical/private implementation does **not** upgrade a public status. It is reference evidence only.

---

# 3. PRIVATE / HISTORICAL WORK — WHAT IT PROVES AND WHAT IT DOES NOT

The private repository contains useful evidence from the pre-reset/rebuild process, including:

- native-passenger-shuttle boarding work for Wraith Dart, Puddle Jumper, Wraith Strike Craft and Wraith Cruiser;
- complete/private gravship-art and conduit-parity work, including old generated Wraith/Asuran gravship presentation and connection-state ambitions;
- human-form Replicator/Asuran factions and role pools;
- a hostile Lattice/Precursor collective plus the non-hostile **Quiet Lattice** enclave;
- a substantial native WNG `BackstoryDef` pool;
- Neural Interface operations for recruit, imprison, Ideology enslave, skill/passions extraction and construction of a human-form copy while preserving source identity data and rolling back failed resource spending.

Useful private/reference commits include:
- `e2ba63fb7a8646f8e9010cd1a34803aa4dcc96b1` — native passenger-shuttle boarding contract;
- `33087e588b8db2b111873ffacc38097d50e6edcb` — old complete gravship-art release boundary;
- `3039b0df7c8176032242455f0761ffb34db8fbcf` — old conduit hardening/parity tooling;
- `0ca2f499ab662d5af2bc3cf8d89c8610e256aa5f` — paused-modal Neural Interface work.

The branch `rebuild/wngr2-humanform-factions-20260909` also contains historical/reference faction/backstory material including `WNG_HumanFormEnclave` / **The Quiet Lattice** and `Defs/BackstoryDefs/Backstories_WNG.xml`.

**None of that proves the feature exists on current public `main`.** It proves only that the intended behavior/design had concrete prior work and gives reference material for a clean public rebuild.

The private recovery/gravship work must especially not be treated as a successful migration merely because it was prepared or discussed. Current public files decide what survived.

---

# 4. MASTER-PLAN REBUILD ORDER — ACTUAL PUBLIC STATUS

## Step 1 — Preserve approved Replicator graphics/resources

**IMPLEMENTED FOUNDATION.**

Approved block body/adaptation/resource graphics are present and the current Replicator feature map accounts for Drone, Hunter, Bulwark, Titan, Siege Mass, Controller, Repairer, Burrower, Artillery plus Armor/Ranged/Power/Grav/Shield overlays and Replicator Matter/Core Fragment resources.

No replacement art should be generated unless Vardath asks.

## Steps 2–3 — Block Replicator foundation / compile-play foundation

**IMPLEMENTED FOUNDATION; LIVE-TEST NEEDED.**

Public contains:
- Drone -> Hunter -> Bulwark -> Titan -> Siege Mass recombination;
- real downward destruction breakup;
- split-born recombination lockout;
- Controller/Repairer/Burrower/Artillery specialists;
- assimilation and stored-matter economy;
- bounded offspring/population;
- dangerous Replicator Matter reassembly;
- EMP suppression;
- powered containment;
- local retaliation/terminal consumption behavior;
- Child's Toy player branch;
- exact controller-domain-aware split/recombine/state inheritance.

Adaptation detail:
- Material — implemented state/economy;
- Armor — implemented effect + overlay;
- Ranged — implemented effect + overlay;
- Power — implemented effect + overlay;
- Shield — implemented effect + overlay;
- AntiShield — implemented state and current Replicator-vs-Replicator shield interaction, **broader cross-system shield interaction still partial**;
- Grav — learned/save-persistent state + overlay only; **richer physical grav/mobility effect remains unfinished**.

Do not call the whole adaptation branch final while Grav and broader AntiShield integration remain dependency-recorded.

## Step 4 — Wraith xenotype/identity/castes/factions

**IMPLEMENTED FOUNDATION.**

Public has one `WNG_Wraith` xenotype and Hunter/Warrior/Commander/Keeper/Queen caste PawnKinds plus four lineage factions:
- Sable Brood;
- Cinder Court;
- Veiled Hive;
- Pale Covenant.

Current maintenance enforces the pale Wraith hair presentation. Castes remain roles/PawnKinds, not separate races.

## Step 5 — Life Force / full+partial feeding / regeneration / hibernation / appearance

**IMPLEMENTED FOUNDATION; LIVE-TEST NEEDED.**

Public has Life Force, full Drain Life, Partial Feed, Life Drained/Fed Recently behavior, regeneration and hibernation/torpor foundations. Ordinary feeding remains separate from strategic faction hunger.

## Step 6 — Strategic Wraith faction hunger

**PARTIAL.**

The important mechanical correction is implemented correctly:
- strategic hunger is faction-level;
- ordinary Drain Life does not open the request;
- request-capable factions need genuine hunger threshold/chance;
- refusal/unresolved hunger increases/forces raid pressure;
- Sable Brood can be configured unable to request feeding.

However the current public request UI does **not** complete the master-plan multi-stage flow. It goes from the initial request to prisoner selection; it does not then show the planned participating-Wraith count/names stage. Therefore the strategic system is mechanically present but the requested UI flow is incomplete.

## Step 7 — Wraith captivity/rescue / Hive infrastructure / mature-Hive ecology

**PARTIAL.**

Implemented publicly:
- exact-pawn captivity/rescue registry and rescue-site flow;
- Wraith raid kidnap bridge;
- Feeding Niche;
- Hibernation Pod;
- Dormancy Vault;
- Hive Heart;
- mature-Hive active/dormant/feeding-stock ecology;
- bounded population/replacement behavior;
- mature-Hive neutralization/retaliation.

**Missing required item:** the master-plan rebuild order explicitly names **Growth Chamber**, and current public search/tree contains no Growth Chamber implementation.

Ordinary feeding, strategic hunger, mature-Hive feeding ecology and mature-Hive retaliation remain separate systems.

## Step 8 — Wraith living technology / Grav Engine

**IMPLEMENTED FOUNDATION; PRESENTATION PARTIAL.**

Public has biological bootstrap/growth paths, Living Forge/workshop foundations and the intended Wraith **Grav Engine** path using Odyssey's exact native engine rather than restoring obsolete Gravcore behavior.

Final professional living-tech presentation remains part of the art/audio debt.

## Step 9 — Human-form Replicators/Asurans / Neural Interface / infiltration / factions / backstories

**PARTIAL, WITH MAJOR MISSING REQUIRED BRANCHES.**

Implemented publicly:
- `WNG_NaniteHumanoid` physical xenotype;
- human-form nanite physiology;
- native food/eating behavior repurposed as visible **Nanite Reserve**;
- ordinary operation drains that reserve;
- self-repair and fabrication spend additional reserve;
- synthetic depletion/shutdown path rather than biological malnutrition;
- EMP disruption;
- Asuran workshop/fabrication;
- hidden hostile `WNG_AsuranLattice`;
- Operative/Technician/Commander PawnKinds.

Still **MISSING REQUIRED**:
- broader Neural Interface recruit/imprison/enslave/copy/create-human-form system;
- exact copy/reconstruction path preserving biography/name/skills/passions/XP/appearance/genome as required;
- real infiltration/impersonation/reveal mechanic;
- non-hostile **Quiet Lattice** human-form enclave;
- player human-form variants;
- broader engineer/infiltrator/soldier/coordinator role structure where distinct from the current minimal three roles;
- mixed human-form + block raid composition;
- native WNG `BackstoryDef` layer.

Current public contains **no `Defs/BackstoryDefs` directory**. Historical/private reference material does contain a substantial `Backstories_WNG.xml`; this is reference evidence, not current implementation.

## Step 10 — Queen vault / recruitment / recovery / sovereign consequences

**PARTIAL, SUBSTANTIALLY ADVANCED.**

Implemented publicly:
- one exact persistent female human-form Replicator Queen, current age 13;
- real precursor-style cryptosleep vault/site;
- immediate player recruitment on release;
- first all-or-nothing four-operative nonlethal Asuran recovery operation;
- physical Asuran recovery Jumper;
- capture only commits when the exact Queen physically leaves inside the exact hostile shuttle transit container;
- exact kidnapped-pawn persistence;
- exact Queen sovereign authority over real block Replicators;
- real faction transfer, exact controller/domain state and dedicated controlled-block commands;
- split/recombine controller-domain continuity;
- EMP/containment interference;
- physical **Sovereign Neural Lattice** item/research/fabrication/native brain install/remove and bounded non-Queen controller domain.

Still **MISSING REQUIRED**:
- **Temporary Asuran lattice intrusion** implementation;
- exact pre-intrusion authority/controller/domain/faction snapshot and restoration;
- recurring later Queen-recovery/capture operations targeting whichever player map physically contains the exact Queen;
- consequences when Asurans successfully retain/recruit the captured Queen;
- genuine mixed Asuran + sovereign block-Replicator hostile compositions tied to captured-Queen consequences;
- infiltration linkage.

Important current-code boundary: `TemporaryAsuran` exists only as a reserved authority identity. Current timeout handling calls ordinary `ReleaseAuthority()`; that is **not sufficient** for the required temporary override because a real implementation must restore an exact prior Queen/Neural-Lattice/autonomous domain rather than erase it.

## Step 11 — Discovery / story progression

**PARTIAL.**

Real public discovery/event content now exists for Queen vault, mature Hive, Dart/captivity/rescue, Ha'tak carrier and other implemented systems, and the old day-84 Queen schedule has not been restored.

The broader master-plan discovery branch is not complete. Historical concepts such as ruined Wraith/Replicator/Ancient laboratories, cloning installations, dormant Asuran facilities and deceptive Ancient-survey/hidden-Asuran reveals are not currently a complete public story-progression layer. These historical site names are concept/reference ideas rather than immutable required exact site names, but the intended overall `mystery -> encounter -> evidence -> understanding -> reconstruction -> mastery` progression remains incomplete.

## Step 12 — Optional CatCraft / ONAC / RimGate interactions

**PARTIAL.**

Implemented:
- exact verified package/Def identities;
- dependency-safe package detection;
- CatCraft ownership boundary preserved;
- Wraith Dart uses optional Stargate-aware escape decision path;
- ONAC/RimGate exact System-Lord/Jaffa integration for Goa'uld content;
- transport rings and current Goa'uld integration foundations.

Still unfinished:
- friendly **Quiet Lattice / Puddle Jumper courier** Stargate delegation path is absent and currently blocked by the missing Quiet Lattice branch;
- safe standalone Goa'uld shuttle/gravship resource/research route when ONAC is absent is unresolved;
- do not invent uranium/chemfuel or another unspecified Goa'uld fallback;
- broader optional integration still requires live testing with actual mod combinations.

## Step 13 — Craft / shuttles

**IMPLEMENTED MECHANICAL FOUNDATION; PRESENTATION/PUDDLE-JUMPER RESOURCE DESIGN PARTIAL.**

Public has native `Building_PassengerShuttle`/Odyssey shuttle stacks for the principal WNG craft, including:
- Wraith Dart;
- Wraith scout/Strike Craft;
- Wraith Cruiser;
- Puddle Jumper;
- Al'kesh;
- plus Death Glider and Asuran recovery Jumper where applicable.

The private native-boarding parity work therefore has a real current public mechanical equivalent and must **not** be re-imported simply because it existed privately.

Still unfinished:
- several current craft use vanilla shuttle graphics as mechanics placeholders rather than final distinct professional craft art;
- Puddle Jumper still explicitly uses **chemfuel as a temporary native-mechanics placeholder** pending deliberate Ancient power/fuel abstraction;
- friendly Quiet-Lattice courier behavior is absent;
- broad live boarding/loading/launch/world/save-load verification remains needed.

**Al'kesh stays.**

## Step 14 — Wraith + Asuran gravship families

**IMPLEMENTED MECHANICAL FOUNDATION; PRESENTATION PARTIAL.**

Current public uses Odyssey-native behavior and real family isolation rather than the failed old XML-parent mirror architecture.

Wraith current family includes native engine/hull/substructure, control, tanks, thrusters, field organ/extender, transport jammer, propulsion coordinator/fuel-savings analogue, living-hull regeneration, native power network and family-specific physical fuel pipes.

Asuran current family includes native engine/hull/substructure, control, tanks, thrusters, field extender, signal jammer, fuel optimizer, true native gravship shield emitter, Asuran power cell, support, native power network and family-specific physical fuel pipes.

Current Wraith defensive design deliberately uses biological **living-hull regeneration** rather than the rejected generic Wraith shield reskin. Do not mark absence of a Wraith energy-shield Def as a missing feature.

Themed fuel pipe connectivity is real and family-specific while Odyssey remains authoritative for fuel storage/accounting/consumption.

Still unfinished:
- final faction-specific professional hull/part/conduit art;
- Wraith/Asuran themed **native hull corner / inside-corner / diagonal / transition presentation** is not found in current public source; native Odyssey geometry works mechanically, but the old/private custom themed topology-rendering ambition did not land publicly;
- current public `Source/WNG/Gravship` contains fuel network, engine-theme and parts logic, but not the old/private themed hull section-layer renderer;
- broad live gravship construction/launch/fuel/save-load validation remains needed.

## Step 15 — Professional art/audio

**MISSING / PARTIAL.**

Preserved approved block Replicator art is present.

But the first complete professional presentation pass is **not complete**:
- current craft and several gravship parts explicitly use vanilla mechanics-validation graphics/placeholders;
- Neural Lattice item still has placeholder presentation;
- custom Wraith/Asuran hull corner/diagonal topology art is absent from current public runtime implementation;
- final dedicated craft/weapon/building/ability/resource presentation is not complete across the mod;
- no complete WNG professional audio library/SoundDef layer is present in current public tree.

Historical/private generated art and release tooling are reference only. Do not restore old generated assets wholesale and do not generate replacement images without Vardath's explicit request.

## Step 16 — Live test / tune / revise

**MISSING REQUIRED FINAL VALIDATION.**

Current source has passed numerous narrow C# / XML / invariant checks during implementation. Those are useful but do not prove live RimWorld behavior.

A broad current-build live pass remains required for:
- Def loading with actual DLC/mod stack;
- world/faction/site generation;
- Wraith hunger modal behavior;
- Queen/recovery/capture state;
- controller domains and save/load;
- native shuttle boarding/loading/launch;
- gravship construction/fuel/launch;
- exact-pawn transport/captivity;
- art rendering/rotations/connections;
- sound mix when real WNG audio exists;
- performance in a large real mod stack.

---

# 5. GOA'ULD / HA'TAK — LEDGER CORRECTION

The original canonical ledger said the Ha'tak family was not implemented. That is now stale.

**CURRENT PUBLIC IMPLEMENTED FOUNDATION:**
- Goa'uld Odyssey-native gravship family;
- pel'tac/control and native substructure/hull/engine path;
- power/fuel networks;
- heavy plasma battery;
- real two-seat Death Glider;
- exact verified System-Lord/Jaffa hostile strikes;
- landed Ha'tak carrier site with real native gravship structure, defenders and parked Gliders;
- real player cross-map/orbital bombardment from a powered Ha'tak battery into a distinct generated Surface map using native bombardment behavior.

Still unfinished/blocked:
- Ha'tak content remains ONAC-gated because Vardath has not defined a safe standalone Goa'uld ship material/fuel/research path;
- hostile native Ha'tak takeoff/retreat/pursuit is blocked by Odyssey's player-oriented `Current.Game.Gravship` singleton and must not be faked with deletion/proxy replacement;
- final presentation/live testing remains unfinished.

---

# 6. WRAITH GRAVSHIP SHIELD CLARIFICATION

The generic master-plan gravship list included shields for each family, but later current implementation deliberately diverged for Wraith identity.

**CURRENT DESIGN:**
- Asuran: true powered Odyssey gravship shield emitter;
- Wraith: biological living-hull regeneration as the defensive analogue;
- generic Wraith shield reskin was rejected in current public content.

Status: **CHANGED / REJECTED**, not missing.

---

# 7. NEWER 2026-09-11 APPENDS — PLANNED ONLY, NOT FAILED MIGRATIONS

The following approved branches remain tracked but their absence from current public implementation is **not** evidence of lost private work:

## Anomaly / Ideology append

Explicit status: **PLANNED CONTENT ONLY — DO NOT IMPLEMENT YET**.

Includes future:
- Iratus/Wraith xenobiology containment/study;
- Whispers-style feral hybrid/fog encounters;
- intelligent human-Wraith hybrids;
- Bug People/engineered organisms;
- unstable transformations/treatment;
- ideology/precept/ritual/role integration for feeding, xenobiology, synthetic life, Goa'uld symbiosis, etc.

## Iratus / diplomacy / pharmacology / Royalty append

Explicit status: **PLANNED CONTENT**, not part of the then-current Ha'tak slice unless Vardath moves it forward.

Includes future:
- real wild Iratus animals and queens;
- attachment/paralysis/feeding/removal behavior;
- Wraith worshippers/client states/tributaries;
- Wraith/Iratus pharmacology;
- Kassa crop/addiction branch;
- Royalty-based Wraith court/telepathy where native mechanics fit;
- related Reol/Hoffan/hybrid treatment branches.

Do not turn these into current missing-migration defects. They remain required future design work until Vardath changes/rejects them.

---

# 8. COMPLETE CURRENT UNFINISHED / DEBT INVENTORY

The following are the **genuine current public gaps** found in this reconciliation. This list supersedes shorter checkpoint lists that omitted some branches.

### Replicator controller / Queen consequences
- Temporary Asuran lattice intrusion;
- exact prior-domain snapshot/restoration through expiry/interruption and split/recombine;
- recurring Queen recovery raids on the exact map physically containing her;
- captured-Queen sovereign consequences;
- mixed Asuran + sovereign block threat composition.

### Human-form Replicators / Asurans
- Neural Interface recruit/imprison/enslave/copy/create-human-form branch;
- exact template biography/name/skill/passions/XP/appearance/genome reconstruction semantics;
- infiltration/impersonation/reveal;
- Quiet Lattice non-hostile enclave;
- player human-form variants;
- broader role/faction composition and mixed raids;
- native WNG backstories;
- complete synthetic disease/implant/temperature/vacuum physiology audit;
- final art/audio/live testing.

### Block adaptation refinement
- richer Grav adaptation effect;
- broader AntiShield integration against concrete non-Replicator shield systems.

### Wraith
- Growth Chamber named in rebuild step 7;
- strategic hunger UI stage showing intended involved-Wraith count/names;
- broader discovery/story progression beyond current implemented sites;
- final presentation/audio/live testing.

### CatCraft / optional integration
- friendly Quiet-Lattice/Puddle-Jumper courier delegation path;
- broader live compatibility testing.

### Craft
- final distinct craft art/audio;
- deliberate Ancient/Puddle-Jumper power/fuel abstraction instead of temporary chemfuel placeholder;
- broad native boarding/loading/launch/world/save-load live validation.

### Gravships
- final professional Wraith/Asuran/Goa'uld presentation;
- faction-specific themed native corner/inside-corner/diagonal/transition rendering/art;
- broad live construction/fuel/power/launch/save-load validation;
- hostile Ha'tak native takeoff/retreat/pursuit remains a technical blocker, not to be faked.

### Goa'uld standalone route
- safe standalone WNG-owned Goa'uld craft/gravship material/fuel/research path when ONAC is absent;
- no invented uranium/chemfuel fallback.

### Research / discovery
- complete encounter/evidence/reconstruction progression remains partial even though many research gates are real and usable.

### Art/audio
- professional mod-wide final art pass remains incomplete outside preserved/finished pockets;
- professional WNG audio layer remains incomplete/not present as a full current public system.

### Validation
- broad live RimWorld validation and tuning of the current fresh public build.

---

# 9. THINGS THAT ARE **NOT** MISSING AND MUST NOT BE REBUILT JUST BECAUSE PRIVATE WORK EXISTS

Do not re-import old private implementations for these simply because similar work existed there:

- block Replicator hierarchy/splitting/recombination;
- Controller/Repairer/Burrower/Artillery foundation;
- Armor/Ranged/Power/Shield adaptation foundation;
- EMP/containment/matter/Child's Toy foundation;
- Wraith Life Force/full+partial feeding/hibernation/regeneration foundation;
- strategic Wraith hunger trigger/raid-pressure foundation;
- exact captivity/rescue foundation;
- mature-Hive core ecology/Hive Heart/Niches/dormancy foundation;
- Wraith biological bootstrap and real Grav Engine path;
- native passenger-shuttle mechanical stacks;
- Wraith/Asuran gravship mechanical families and family fuel networks;
- transport rings;
- Wraith stun staff;
- Goa'uld/Ha'tak gravship, Death Glider, carrier and bombardment foundations;
- exact Queen vault/release/first recovery/capture boundary;
- exact Queen sovereignty;
- physical Sovereign Neural Lattice.

Refine or complete their recorded gaps; do not replace functioning current public architecture with historical code by default.

---

# 10. CORRECTED CONTINUATION RULE

The previous single-line `Temporary Asuran intrusion is next` checkpoint was too narrow to function as a complete project state, even though Temporary Asuran intrusion is indeed a genuine unfinished controller slice.

Future continuations must:

1. fetch current public `main` first;
2. compare it to the HEAD recorded here / in `CURRENT_PUBLIC_STATE.md`;
3. read this entire reconciliation before treating any plan item as present or absent;
4. use private/history only as reference for a specifically confirmed public gap;
5. keep every gap in section 8 explicitly tracked until implemented, changed/rejected by Vardath, or deliberately deferred;
6. never infer that uncommitted/private reasoning changed public WNG;
7. update this reconciliation or `CURRENT_PUBLIC_STATE.md` when public state changes materially.

For the controller branch specifically, Temporary Asuran intrusion remains a valid next implementation candidate because current public already supplies the shared sovereignty architecture. But completing it does **not** mean the broader human-form, Wraith, story, presentation and live-validation debts listed above disappear.

---

# 11. RECONCILIATION VERDICT

The fresh public rebuild is **substantially more advanced** than the old canonical ledger snapshot, but **less complete** than the later checkpoint/primer wording implied.

The largest stale-ledger false negatives were:
- human-form physiology foundation;
- exact Queen/vault/first recovery;
- Queen sovereignty;
- Sovereign Neural Lattice;
- Ha'tak/Death Glider/carrier/orbital branch.

The largest checkpoint false positives / omitted debts were:
- human-form Neural Interface/infiltration/Quiet Lattice/player variants/backstories/mixed raids;
- recurring Queen recovery and captured-Queen consequences;
- Wraith Growth Chamber;
- incomplete strategic-hunger UI flow;
- richer Grav/broader AntiShield integration;
- friendly Quiet-Lattice Stargate courier;
- themed gravship hull corner/diagonal presentation;
- final craft/gravship/implant art and professional audio;
- broader discovery/story progression;
- standalone Goa'uld resource/research route;
- broad live RimWorld/save-load/mod-stack validation.

This is now the public-vs-plan reconciliation baseline. **Public source remains the final implementation truth.**
